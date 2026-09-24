# CT-PO-P12-GAP-02 — Canonical PDF Extraction, Supplier Attribution and Multi-Year Reuse Acceptance

# A. Task Identity

```text
P12-GAP-02-20260924-CANONICAL-PDF-SUPPLIER-REUSE
```

**Date:** 2026-09-24
**Repository:** `/home/shomonrobie/ct_93d5cdd`, branch `p8-release-reconciled`
**Corpus under test:** `p12-canonical-demo-v1` (P12-DOC-03), 6 PDFs, oracle
`tools/demo_lab/p12_canonical_manifest.json` (read-only, unmodified)
**Purpose:** the first real CarbonTally extraction acceptance test against the
canonical investor-demo PDF documents.

> **Nothing was manufactured.** No extracted payload was inserted directly into any
> table, no oracle value was edited, no extracted value was repaired, no supplier was
> created to make the test pass, no P1 mode change was made, and no product code was
> changed. Where the real path stops, this report records the dependency instead of
> working around it.

---

# B. Environment Safety

| Item | Value |
| --- | --- |
| Repo / branch | `/home/shomonrobie/ct_93d5cdd` @ `p8-release-reconciled`, HEAD `0fee936` at start |
| Database used | `carbontally_demo_local` (`current_database()` verified) |
| Host / port | `127.0.0.1:54426` → container `supabase_db_carbon_ledger` |
| Backend under test | `127.0.0.1:8070` (release backend, OpenAPI reachable) |
| Production | **NEVER contacted / never authorised** |
| `carbontally_test` | demo-lab users **0** — untouched |
| `carbontally_qa_phase8` | demo-lab users **0** — untouched |
| Protected flagship `postgres` | demo-lab users 14 (the documented lab identity, unchanged) |
| Demo Lab marker | 14 users `@demo-lab.carbontally.local` in `carbontally_demo_local`; 4 orgs (`Demo Lab Organisation A/B`, `Demo Lab Client A/B`) |
| Destructive resets | **NONE** — none was required |
| Writes performed | 6 PDF uploads through the product API into `Demo Lab Organisation A`; harness evidence files. **No direct table writes.** |

Baseline before the test (recorded so the effect of the uploads is measurable):
`snapshots=2, emissions=2, evidence=2, suppliers=1, reports=4, items=11`.
After the test: `snapshots=2, emissions=2, evidence=2, suppliers=1, reports=4,
items=17` — the only change is **+6 extraction items** (one per canonical PDF).

---

# C. Corpus

Corpus `p12-canonical-demo-v1` at
`$HOME/ct_local_env/demo_lab/corpus/p12-canonical-demo-v1/`, oracle
`tools/demo_lab/p12_canonical_manifest.json`. Each PDF's SHA-256 was recomputed and
**matched the oracle for 6/6** before upload.

| document_id | FY | oracle PDF SHA-256 (first 16) | SHA matched | oracle line items |
| --- | --- | --- | --- | --- |
| `p12canon_waste_001` | 2025 | `6142fd3d43156c46` | yes | 3 |
| `p12canon_waste_002` | 2025 | `b384148016dd4ac3` | yes | 4 |
| `p12canon_waste_004` | 2025 | `c659fb2eaad6322a` | yes | 2 |
| `p12canon_waste_003` | 2026 | `f915c9a71a35d275` | yes | 5 |
| `p12canon_waste_005` | 2026 | `9b2753cf2147beb3` | yes | 3 |
| `p12canon_waste_006` | 2026 | `efcc1b223e3cb847` | yes | 4 |

Oracle (unchanged, used as-is): supplier **`Robinsons Recycling Services Ltd`**,
customer **`Sustainable Direct Group`**, `tonnes`, 20% VAT, all six text-native waste
invoices.

**Tenancy note.** The corpus is a *document* corpus; `Sustainable Direct Group` is the
name printed on the documents as the buyer, not a CarbonTally tenant. The acceptance
uploads target the existing **`Demo Lab Organisation A`**
(`3fd0f325-16a1-5b53-8fb8-27929cf218fa`) — the same organisation that already holds the
EV-01 CSV evidence chain and the FY2025 report — so the multi-year question is asked
inside one tenant. No tenant was created and no tenant architecture was modified.

---

# D. Extraction Results

Upload: **6/6 → HTTP 201** through `POST /api/v3/uploads` (real product ingestion,
multipart, `application/pdf`, per-file content type derived from the filename extension).

| document_id | FY | document (queue) id | extraction item id | queue status | stage |
| --- | --- | --- | --- | --- | --- |
| `…001` | 2025 | `a63b2e54-844d-458e-b2ae-a9c80b7defd9` | `9ef70492-1036-46b1-989e-b51b0a34c1ab` | `manual_review` | `blocked` |
| `…002` | 2025 | `b1a9c75d-f07d-42f4-b7cb-5b678b51d9c4` | `1a27d672-13ec-4bfc-a2d9-dec825705841` | `manual_review` | `blocked` |
| `…004` | 2025 | `13168792-b3c8-409c-81b3-44403d73dc71` | `e368d87e-b95a-4e51-b17b-ff09bce1f20c` | `manual_review` | `blocked` |
| `…003` | 2026 | `1e485193-a2ec-4f0b-a5d4-6fafb8cd7249` | `4e025eaf-e11f-4358-b8ca-3675e3828c5b` | `manual_review` | `blocked` |
| `…005` | 2026 | `e976e32d-1263-45a3-9c81-534086201ff8` | `c553b7fe-1f09-4641-8426-f6c51639c447` | `manual_review` | `blocked` |
| `…006` | 2026 | `66ea7610-b1b7-43ca-8286-c98436488f97` | `fa8efa89-36d8-48c8-8718-66ff633d20fb` | `manual_review` | `blocked` |

All six rows carry `pipeline_version = v3-auto-1.1`. Extraction **ran** for every
document (`status = ok`, method `pdf_text`; no `no_text` failures, no errors, no
retries — `attempt_count` 0 except `…002` = 1).

**Persisted extracted payload per document** (from `manual_extraction_items.extracted_data`,
the durable item the operator workbench reads):

| document_id | persisted extraction |
| --- | --- |
| `…001` | `{"date": "2025-04-02", "activity": "Waste", "invoice_number": "SVC2025008717"}` |
| `…002` | `{"unit": "t", "activity": "Waste", "quantity": 112.0}` |
| `…004` | `{"activity": "Waste"}` |
| `…003` | `{"date": "2026-07-02", "activity": "Waste", "net_amount": "£11,628.76", "invoice_number": "UTL2025-1409"}` |
| `…005` | `{"date": "2026-07-07", "activity": "Waste", "net_amount": "£8,949.690", "invoice_number": "ECO2024006142"}` |
| `…006` | `{"date": "Feb 02, 2026", "activity": "Waste", "invoice_number": "GRN/2027/1879"}` |

Blocking reason recorded by the pipeline per document:

| document_id | `manual_review_reason` |
| --- | --- |
| `…001`, `…003`, `…004`, `…005`, `…006` | `extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit` |
| `…002` | `mapping could not auto-resolve: line 1: clarification required for 'Waste' (the activity can mean either a treatment/material handling of the substance or a combustion of it as fuel, and those families share no accounting meaning)` |

Also observed: `document_processing_queue.extracted_data` is empty for 5/6 (only `…002`
holds the same partial payload) — the durable, human-readable extraction result for this
corpus is on the extraction item, and that is what is recorded above.

---

# E. Supplier Extraction

**0/6** — `Robinsons Recycling Services Ltd` was **never** extracted into any field the
downstream product uses.

Evidence: no extracted payload for any document contains a `supplier` key (see §D);
`manual_extraction_items.mapped_supplier_id` is `NULL` 6/6; the extractor's own
`unresolved` list names `supplier`; the offline re-extraction of `…001` returns
`supplier: None`, and the same is true with the P1 shape `enabled` (§H).

| document | oracle supplier | extracted supplier | result |
| --- | --- | --- | --- |
| `…001` | Robinsons Recycling Services Ltd | *(absent)* | FAIL |
| `…002` | Robinsons Recycling Services Ltd | *(absent)* | FAIL |
| `…003` | Robinsons Recycling Services Ltd | *(absent)* | FAIL |
| `…004` | Robinsons Recycling Services Ltd | *(absent)* | FAIL |
| `…005` | Robinsons Recycling Services Ltd | *(absent)* | FAIL |
| `…006` | Robinsons Recycling Services Ltd | *(absent)* | FAIL |

**SUPPLIER EXTRACTION: 0/6.** Note that the supplier name *is* printed prominently as
the first line of every PDF — that is exactly why §20 forbids treating visible text as a
PASS. It is present in the document and absent from the extraction result.

---

# F. Customer Extraction

**0/6** — `Sustainable Direct Group` was never extracted either, under the same evidence
(no `customer` key in any payload; `customer` is not reported as resolved by the
extractor). The documents print it under the generator's `Buyer:` label.

**CUSTOMER EXTRACTION: 0/6.**

---

# G. Line-Item Extraction

**0/6 in the primary product path.** No document produced a `line_items[]` key in any
persisted payload; the P1 shape mode that would emit it is **not active** (§H).

| document | oracle line-item count | extracted `line_items[]` | quantities extracted | unit extracted |
| --- | --- | --- | --- | --- |
| `…001` | 3 | **none** | none | none |
| `…002` | 4 | **none** | `112.0` (first line only, document-level) | `t` |
| `…003` | 5 | **none** | none | none |
| `…004` | 2 | **none** | none | none |
| `…005` | 3 | **none** | none | none |
| `…006` | 4 | **none** | none | none |

Per-field outcome for the flat (primary) payload across the corpus:

* activity → `"Waste"` **6/6** ✓ (correct family, but see the ambiguity block in §I);
* `invoice_number` → present and **exactly correct 4/6** (`SVC2025008717`, `UTL2025-1409`,
  `ECO2024006142`, `GRN/2027/1879`); absent for `…002`, `…004`;
* `date` → present 4/6 (`2025-04-02`, `2026-07-02`, `2026-07-07` exact ISO;
  `"Feb 02, 2026"` semantically correct but a different format);
* `quantity`/`unit` → **1/6 partial** (`…002` only) and even there it is the *first line's*
  quantity presented as a document-level value, not a line item;
* `net_amount` → 2/6 (`£11,628.76`, `£8,949.690`) — these equal the oracle **document net
  totals**, not line values;
* `supplier`, `customer`, `line_items` → never.

**LINE-ITEM EXTRACTION: 0/6.**

---

# H. P1 Shadow Analysis

P1 was **not promoted, not modified**, and the running backend's configuration was not
touched. The mode was measured two ways: from the running configuration, and by running
the extraction service offline in isolated processes.

**Running configuration (decisive):** the Demo Lab backend environment contains **no**
`CARBONTALLY_P1_EXTRACTION_SHAPE` and **no** `CARBONTALLY_P1_ORGANIZATION_ALLOWLIST`
entry, and the resolver reports:

```text
shape_mode()      -> "shadow"
rollout_status()  -> {"requested_mode": "shadow", "effective_mode": "shadow",
                      "organization_id": null, "in_rollout": false,
                      "allowlist_size": 0, "allow_all": false}
```

| Question (§8) | Finding |
| --- | --- |
| Primary extraction payload | Flat: `activity`, `date`, `invoice_number`, occasionally `net_amount`/`quantity`/`unit`; **never** `line_items[]`, **never** `supplier`, **never** `customer` |
| Shadow payload | The `shadow` hook emits **no structure at all** — it attaches a *coverage* block only (`multi_line_suspect`, `candidate_lines`, `text_chars`, `clipped`, `mode`, `ai_fanout`) to the in-process result and logs it |
| Shadow payload contains structured line items? | **No.** In `shadow` the `extracted` dict is passed through unchanged |
| Primary payload contains structured line items? | **No** — 0/6 |
| Is the shadow result persisted? | The **coverage block is absent** from every persisted payload: `document_processing_queue.extracted_data`, `automation_extracted_data` and `manual_extraction_items.extracted_data` contain no coverage fields and no `line_items` |
| Does any production workflow consume the shadow result? | No. Nothing downstream can consume a structure that is absent; mapping iterates `line_items` and found none for 5/6 (for `…002` the mapping stage ran on the flat single value and blocked — §I) |

**Shadow coverage is nonetheless accurate** — measured offline on the real corpus:

| document | `multi_line_suspect` | `candidate_lines` | oracle line items |
| --- | --- | --- | --- |
| `…001` | true | **3** | 3 ✓ |
| `…002` | true | **4** | 4 ✓ |
| `…003` | true | **6** | 5 (+1 = the `Net Amount` footer line) |
| `…004` | true | **3** | 2 (+1 = a `MH82 …KM` row) |
| `…005` | true | **4** | 3 (+1 = the `GST` total line) |
| `…006` | true | **4** | 4 ✓ |

For `…001` the coverage block read: `{"multi_line_suspect": true, "candidate_lines": 3,
"page_count": 2, "page_basis": "document", "text_chars": 574, "clipped": false,
"reasons": ["3 candidate source lines"], "mode": "shadow",
"ai_fanout": {"per_page_ai": false, "pages": 0, "reason": "text layer is within the AI
clip; a single pass suffices"}}`. So P1's *measurement* is sound; only the *emission* is
gated.

**Deliberate un-promoted probe (evidence only — NOT a promotion).** Running the same
service in isolated processes with `CARBONTALLY_P1_EXTRACTION_SHAPE=enabled` and a global
allowlist — **no environment or product change** — produces `line_items[]` for **6/6**,
but with material defects that must not be glossed over:

* `…001`, `…006`: quantities **exactly match** the oracle (90/64/58 and
  41.98/91.6/41.42/94.7), units `tonne`;
* `…002`: quantities exact (112/25.8/63.5/47.6) but **units wrong for 2 lines — `GBP`**
  instead of `tonnes`;
* `…004`: quantities **wrong** (`5.0`, `43.0` vs oracle `4.6`, `42.8`) **plus a false
  positive** row (`MH82 KM`, qty 2.0);
* `…003`: 5 real lines correct **plus a false positive** `"Net Amount: £"` qty 11,628.76;
* `…005`: 3 real lines correct but **all units `GBP`** **plus a false positive**
  `"GST: £"` qty 1,789.93;
* **supplier and customer remain `None` in `enabled` mode for all six.**

Conclusion, stated exactly as §8 requires:

```text
EXTRACTION STRUCTURE AVAILABLE ONLY WHEN P1 IS 'enabled'
          (UN-PROMOTED; THE PRIMARY PRODUCT PATH EMITS NO line_items[])
PRIMARY PRODUCT PATH DOES NOT CONSUME IT
AND EVEN IN 'enabled' MODE SUPPLIER/CUSTOMER ARE NOT EXTRACTED
```

**This is NOT a PASS for the production/demo workflow.**

---

# I. Mapping

**0/6 mapped. No factor was selected for any canonical line.**

1. **5/6 never reached the mapping stage.** The pipeline blocked them earlier, at
   extraction completeness (`0.33 < 0.50`, unresolved `quantity, unit`) — there was
   nothing to map.
2. **1/6 (`…002`) reached mapping and was blocked by activity ambiguity.** The product's
   own reason string:
   > `mapping could not auto-resolve: line 1: clarification required for 'Waste' (the
   > activity can mean either a treatment/material handling of the substance or a
   > combustion of it as fuel, and those families share no accounting meaning)`

   This is the same `Waste`-ambiguity behaviour recorded for the Step-2 waste document —
   i.e. **even with a clean `Waste` activity, the current factor set does not
   auto-resolve a waste line**. A product/PO matter, not an extraction defect.
3. **Operator mapping route not reachable for this corpus** (measured, not assumed):

   * `…/ops/entities/{entity_id}/extraction/items/{item_id}[/mapping-options|/map|/calculate]`
     as `pe_manager` → **403 `Item is not effectively assigned to this processing entity`**
     — correct authorization (PE isolation): all six items were created with
     `processing_entity_id = NULL` and `processing_origin = CARBONTALLY_INTERNAL` in one
     batch (`d8b87866-8d72-41da-b4ed-f23500b52d5b`). Reaching the PE workbench would
     require the PE-assignment workflow, out of scope here.
   * The same PE path as `org_a_owner` → **403** (a customer owner correctly cannot use PE
     ops endpoints).
   * `PUT /api/v3/manual-extraction/items/{item_id}` accepts free-form `extracted_data` /
     `mapped_data` / `calculated_emissions_kg_co2e`. **It was deliberately NOT called with
     values**: writing `activity`/`quantity`/`unit`/supplier into it would be *me*
     supplying the data extraction failed to produce — forbidden by §7 and §20.

`manual_extraction_items.mapped_supplier_id` and `emission_factor_used` are `NULL` for
**6/6**; `calculated_emissions_kg_co2e` is `NULL` for **6/6**.

Dependency chain (§13):

```text
PDF extraction produced no line_items[]
        -> mapping had no lines to map (5/6 blocked earlier by completeness)
        -> the only document that reached mapping was blocked by 'Waste' ambiguity
        -> 0/6 mapped, 0 factors selected
```

---

# J. Calculation

**0/6. No canonical PDF produced a calculation snapshot or an emissions row.**

* `calculation_snapshots` before = 2, after = **2** (both pre-existing EV-01 CSV rows);
* `emissions_logs` before = 2, after = **2**;
* canonical-document emissions = **0**; snapshots with `source_file LIKE '%p12canon%'` = **0**;
* `GET /api/v3/emissions/calculations?organization_id=…` → **200**, `total: 2`, both
  `Natural gas` / `kWh (Net CV)` / `0.2027` — the pre-existing CSV calculations only.

Calculation is **blocked by the mapping dependency** (§I). The calculation contract could
not be exercised for canonical data, so no arithmetic is asserted here and none was
invented.

---

# K. Evidence

**0/6. No canonical PDF produced an evidence line, and therefore no snapshot link.**

* `evidence_line_items` before = 2, after = **2** — both still the EV-01 CSV lines
  (`9252ca02-1a5a-452d-8943-047f8ff35045` line 1, `0b7ba27b-8448-42c6-9e03-d61f40172dbc`
  line 2, both `materialisation_kind = FORWARD`, `extraction_method = csv`,
  `source_file_id = c806c0cc-…`);
* evidence rows whose `source_file_id` is a canonical document = **0**;
* `source_line_item_id` links for canonical data = **0**.

Exact dependency (§15):

```text
PDF extraction produced no line_items[]
        -> no per-line source item to materialise
        -> no evidence_line_items row
        -> no source_line_item_id -> calculation snapshot link possible
        -> no emissions evidence
```

The **EV-01 CSV evidence chain was not altered** (counts and ids unchanged), so the
existing known-good provenance remains intact and the contrast between CSV provenance
(works) and PDF provenance (absent) stands exactly as recorded in the Step-2 audit.

---

# L. Supplier Persistence

**0/6. No supplier identity was persisted for any canonical document.**

| Surface | Value |
| --- | --- |
| `suppliers` table | **1 row**, unchanged: `2fd4072c… British Gas` (created in Step 2 through the real CRUD API). **No new supplier was created, and none was matched.** |
| `manual_extraction_items.mapped_supplier_id` | `NULL` 6/6 |
| `manual_extraction_items.emission_factor_used` | `NULL` 6/6 |
| `emissions_logs.supplier_id` | unaffected — no canonical emissions exist; and per `backend/domain/insight_query.py` the emission write path does not populate this column at all (PO C-06 / D-09 unresolved) |
| `document_processing_queue.ai_mapped_supplier_id` | `NULL` 6/6 |

The chain `extraction → processing item → mapped item → calculation → emissions` breaks at
the **first** link: no supplier is extracted, so nothing downstream can persist. Nothing
was created manually to repair this.

---

# M. Supplier Reuse

**Mandatory supplier-reuse matrix (§19).** Verdict column added; the requested columns are
all present.

| Document | Year | Expected Supplier | Extracted Supplier | Supplier ID | Reused Existing ID? | Automatic / Operator | Result |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| 001 | 2025 | Robinsons Recycling Services Ltd | *(none extracted)* | none | **NO** | neither — automatic extraction never produced a supplier; no operator association was made | **FAIL** |
| 002 | 2025 | Robinsons Recycling Services Ltd | *(none extracted)* | none | **NO** | neither | **FAIL** |
| 004 | 2025 | Robinsons Recycling Services Ltd | *(none extracted)* | none | **NO** | neither | **FAIL** |
| 003 | 2026 | Robinsons Recycling Services Ltd | *(none extracted)* | none | **NO** | neither | **FAIL** |
| 005 | 2026 | Robinsons Recycling Services Ltd | *(none extracted)* | none | **NO** | neither | **FAIL** |
| 006 | 2026 | Robinsons Recycling Services Ltd | *(none extracted)* | none | **NO** | neither | **FAIL** |

`Supplier IDs`: **none exist for any canonical document** (no creation, no matching, no
association).

**The three capabilities are different, and each is answered separately (§11):**

| Capability | Verdict | Evidence |
| --- | --- | --- |
| **AUTOMATIC SUPPLIER RECOGNITION** | **NOT IMPLEMENTED / FAIL** | supplier not extracted 0/6; `suppliers` table unchanged (1 row); no match/resolve/ensure/get-or-create routine exists anywhere in `backend/` or `frontend/` (repo-wide grep) |
| **OPERATOR-SUPPLIED SUPPLIER ASSOCIATION** | **EXISTS AS A FIELD, NOT EXERCISED** | `MapPayload.mapped_supplier_id` and `manual_extraction_items.mapped_supplier_id` exist and the ops/manual routes accept them — but the PE workbench route returned 403 (items unassigned) and the manual route requires an operator to type the data, which §7/§20 forbid me from doing |
| **SUPPLIER REUSE ACROSS YEARS** | **NOT DEMONSTRATED / FAIL** | depends on recognition (A), which is absent; no supplier identity exists to reuse |

Answering the acceptance question directly: *"Does CarbonTally recognize these as the same
supplier relationship across reporting years?"* — **No. Nothing in the product associates
either year with a supplier at all.** This is case **D (no supplier association)** from the
§11 option list; cases A, B and C (auto-create/match, duplicate creation, operator
requirement) cannot even be reached because no supplier is extracted in the first place.

No duplicate supplier records were created (there is nothing to duplicate) — so the
"duplicate supplier identities" risk in §12 is **not** the failure mode here; the failure
mode is **no identity at all**.

---

# N. Multi-Year

**FAIL — the FY2025 and FY2026 relationship cannot be preserved because neither year
carries a supplier identity.**

| Year | Documents | Document ids | Reporting period | Processing item ids | Mapped item ids | Calculation ids | Emissions ids |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FY2025 | `…001`, `…002`, `…004` | `a63b2e54…`, `b1a9c75d…`, `13168792…` | 2025-03, 2025-02, 2025-06 | `9ef70492…`, `1a27d672…`, `e368d87e…` | none | none | none |
| FY2026 | `…003`, `…005`, `…006` | `1e485193…`, `e976e32d…`, `66ea7610…` | 2026-06, 2026-06, 2026-01 | `4e025eaf…`, `c553b7fe…`, `fa8efa89…` | none | none | none |

* One supplier identity: **none** (so no id can be shared across years).
* One customer identity: **none** (customer also not extracted).
* Both years processed into the **same organisation** (`Demo Lab Organisation A`) and the
  same batch (`d8b87866-…`), so the *tenant* context is common — but document-level
  supplier/customer attribution does not exist to be shared.
* Reporting periods are present on the documents and were partly extracted as `date`
  (4/6), but no period is persisted on any calculation because no calculation occurred.

The multi-year acceptance question — "can the product preserve
`Supplier ├── FY2025 invoices └── FY2026 invoices` without unintentionally creating
duplicate suppliers?" — is **unanswerable in the affirmative**: there is no supplier to
preserve and no duplicate to worry about.

---

# O. Reporting

**No canonical PDF data reached reporting.** The dependency is recorded rather than
bypassed (§17).

* Dependency: extraction produced no line items → no mapping → no calculation → no
  emissions → **no rows for any canonical document can be aggregated into a report**.
* `report_generation_queue` before = 4, after = **4**; canonical documents appear in no
  report.
* **Regression check (the previously proven report path must not regress) — it did not:**

| Check | Result |
| --- | --- |
| `GET /api/v3/reports?organization_id=…` | **200** — 4 reports, incl. `2f92c5e3…` "Annual emissions report 2025" `completed` |
| `GET /api/v3/reports/{id}/content` (FY2025) | **200** |
| `GET /api/v3/reports/{id}/versions` (FY2025) | **200** (includes the APPROVED version) |
| `GET /api/v3/reports/{id}/pdf` (FY2025, branded PDF) | **200** `application/pdf` (verified in P12 demo-journey audit; path unchanged) |
| `GET /api/v3/emissions/calculations?organization_id=…` | **200**, `total: 2` (CSV only; no canonical rows) |
| `GET /api/v3/evidence/line-items/{EV-01 line 1}` (Source Evidence Viewer) | **200**, `materialisation_kind: FORWARD`, source item `0193ba83…`, org `3fd0f325…` — **CSV provenance unaffected** |

So: **the reporting product works and was not regressed; the canonical PDF data simply
never arrives.** No report was manufactured from hand-entered data.

**Source Evidence Viewer (§16):** there is no canonical PDF evidence line to view, so
Viewer acceptance for this corpus is **not reachable** (0 evidence lines). The Viewer
itself was exercised against the existing CSV evidence and returned 200 — i.e. the
Viewer is not broken; the canonical PDFs have nothing to show in it.

---

# P. Oracle Comparison

Oracle values are **unedited**. `—` means the product produced no value at all (recorded,
not silently normalised). "Extracted" is the persisted product payload (§D).

`…001` (FY2025)

| Field | Oracle | CarbonTally | Result |
| --- | --- | --- | --- |
| Supplier | Robinsons Recycling Services Ltd | *(absent)* | **MISSING** |
| Customer | Sustainable Direct Group | *(absent)* | **MISSING** |
| Invoice reference | SVC2025008717 | SVC2025008717 | **MATCH** |
| Invoice date | 2025-04-02 | 2025-04-02 | **MATCH** |
| Billing period | 2025-03-01 → 2025-03-31 | *(absent)* | **MISSING** |
| Line count | 3 | 0 | **MISSING** |
| Quantity | 90.0 / 64.0 / 58.0 t | — | **MISSING** |
| Unit | tonnes | — | **MISSING** |
| Rate | 107.639 / 190.222 / 100.22 | — | **MISSING** |
| Net | 27674.48 | — | **MISSING** |
| VAT | 5534.89 | — | **MISSING** |
| Gross | 33209.37 | — | **MISSING** |

`…002` (FY2025)

| Field | Oracle | CarbonTally | Result |
| --- | --- | --- | --- |
| Supplier | Robinsons Recycling Services Ltd | *(absent)* | **MISSING** |
| Customer | Sustainable Direct Group | *(absent)* | **MISSING** |
| Invoice reference | SVC2024-8258 | *(absent)* | **MISSING** |
| Invoice date | 2025-03-05 | *(absent)* | **MISSING** |
| Billing period | 2025-02-01 → 2025-02-28 | *(absent)* | **MISSING** |
| Line count | 4 | 0 | **MISSING** |
| Quantity | 112.0 / 25.8 / 63.5 / 47.6 t | `112.0` (first line, document-level) | **PARTIAL / MISREPRESENTED** |
| Unit | tonnes | `t` | **PARTIAL (wrong token)** |
| Rate | 178.665 / 189.996 / 98.522 / 80.726 | — | **MISSING** |
| Net | 35011.09 | — | **MISSING** |
| VAT | 7002.22 | — | **MISSING** |
| Gross | 42013.31 | — | **MISSING** |

`…004` (FY2025)

| Field | Oracle | CarbonTally | Result |
| --- | --- | --- | --- |
| Supplier | Robinsons Recycling Services Ltd | *(absent)* | **MISSING** |
| Customer | Sustainable Direct Group | *(absent)* | **MISSING** |
| Invoice reference | INV2026004869 | *(absent)* | **MISSING** |
| Invoice date | 2025-07-03 | *(absent)* | **MISSING** |
| Billing period | 2025-06-01 → 2025-06-30 | *(absent)* | **MISSING** |
| Line count | 2 | 0 | **MISSING** |
| Quantity | 4.6 / 42.8 t | — | **MISSING** |
| Unit | tonnes | — | **MISSING** |
| Rate | 64.643 / 117.315 | — | **MISSING** |
| Net | 5318.44 | — | **MISSING** |
| VAT | 1063.69 | — | **MISSING** |
| Gross | 6382.13 | — | **MISSING** |

`…003` (FY2026)

| Field | Oracle | CarbonTally | Result |
| --- | --- | --- | --- |
| Supplier | Robinsons Recycling Services Ltd | *(absent)* | **MISSING** |
| Customer | Sustainable Direct Group | *(absent)* | **MISSING** |
| Invoice reference | UTL2025-1409 | UTL2025-1409 | **MATCH** |
| Invoice date | 2026-07-02 | 2026-07-02 | **MATCH** |
| Billing period | 2026-06-01 → 2026-06-30 | *(absent)* | **MISSING** |
| Line count | 5 | 0 | **MISSING** |
| Quantity | 16.0 / 29.0 / 18.0 / 26.0 / 19.0 t | — | **MISSING** |
| Unit | tonnes | — | **MISSING** |
| Rate | 186.208 / 83.741 / 94.935 / 51.864 / 166.508 | — | **MISSING** |
| Net | 11628.76 | `£11,628.76` (document total, not a line) | **MISATTRIBUTED** |
| VAT | 2325.76 | — | **MISSING** |
| Gross | 13954.52 | — | **MISSING** |

`…005` (FY2026)

| Field | Oracle | CarbonTally | Result |
| --- | --- | --- | --- |
| Supplier | Robinsons Recycling Services Ltd | *(absent)* | **MISSING** |
| Customer | Sustainable Direct Group | *(absent)* | **MISSING** |
| Invoice reference | ECO2024006142 | ECO2024006142 | **MATCH** |
| Invoice date | 2026-07-07 | 2026-07-07 | **MATCH** |
| Billing period | 2026-06-01 → 2026-06-30 | *(absent)* | **MISSING** |
| Line count | 3 | 0 | **MISSING** |
| Quantity | 36.7 / 17.2 / 8.0 t | — | **MISSING** |
| Unit | tonnes | — | **MISSING** |
| Rate | 127.074 / 165.465 / 180.009 | — | **MISSING** |
| Net | 8949.69 | `£8,949.690` (document total, not a line) | **MISATTRIBUTED** |
| VAT | 1789.93 | — | **MISSING** |
| Gross | 10739.62 | — | **MISSING** |

`…006` (FY2026)

| Field | Oracle | CarbonTally | Result |
| --- | --- | --- | --- |
| Supplier | Robinsons Recycling Services Ltd | *(absent)* | **MISSING** |
| Customer | Sustainable Direct Group | *(absent)* | **MISSING** |
| Invoice reference | GRN/2027/1879 | GRN/2027/1879 | **MATCH** |
| Invoice date | 2026-02-02 | `"Feb 02, 2026"` | **SEMANTIC MATCH, FORMAT DIFFERS** |
| Billing period | 2026-01-01 → 2026-01-31 | *(absent)* | **MISSING** |
| Line count | 4 | 0 | **MISSING** |
| Quantity | 41.98 / 91.6 / 41.42 / 94.7 t | — | **MISSING** |
| Unit | tonnes | — | **MISSING** |
| Rate | 93.821 / 141.134 / 84.737 / 170.098 | — | **MISSING** |
| Net | 36484.57 | — | **MISSING** |
| VAT | 7296.91 | — | **MISSING** |
| Gross | 43781.48 | — | **MISSING** |

**Corpus roll-up:** invoice reference **4/6 MATCH**; invoice date **3/6 exact + 1/6
format-only**; supplier **0/6**; customer **0/6**; line count **0/6**; quantity **0/6
correct** (1/6 partial and misrepresented); unit **0/6 correct** (1/6 wrong token); rate
**0/6**; net **0/6 as a line** (2/6 present as a document total); VAT **0/6**; gross
**0/6**.

---

# Q. Gap Classification

Every failure classified per §21. **No product code was changed.**

| ID | Gap (proven) | Classification | Severity | Smallest legitimate remediation / decision needed |
| --- | --- | --- | --- | --- |
| **GAP-02-01** | PDF primary payload emits **no `line_items[]`** (0/6); P1 resolves to `shadow` with an empty allowlist | `PRODUCT_CAPABILITY` (ratified governance state, **not a defect**) | **Critical for the demo** | P1 promotion is a **PO decision** (`P1-D1`: the default must stay `shadow` until shadow evidence is recorded). Shadow evidence now exists (this report + Step-2 record); promotion also needs GAP-02-05 fixed first |
| **GAP-02-02** | **Supplier never extracted from PDF (0/6)** although printed as the document's first line; the extractor itself lists `supplier` as `unresolved` | `PRODUCT_CAPABILITY` | **Critical** | Extraction must parse the supplier/vendor header block. Follow-up implementation item |
| **GAP-02-03** | **Customer never extracted from PDF (0/6)** | `PRODUCT_CAPABILITY` | High | Extract the buyer/customer block (the generator's label pool includes `Buyer:`/`Customer:`/`Client:`) |
| **GAP-02-04** | Table `Qty`/`Unit` columns not parsed → `quantity`/`unit` unresolved → 5/6 blocked at completeness 0.33 < 0.50 | `PRODUCT_CAPABILITY` | **Critical** | Either a PDF table row parser, or P1 promotion (which does parse them — with the GAP-02-05 caveats) |
| **GAP-02-05** | Even in P1 `enabled`, line quality is defective: units misread as `GBP` (2 docs), one quantity misread (1 doc), false-positive rows from `Net Amount`/`GST`/VRM lines (3 docs) | `PRODUCT_CAPABILITY` | High | Tighten the line classifier / total-line exclusion before any promotion; each case becomes a concrete regression test |
| **GAP-02-06** | **`Waste` activity does not auto-resolve to a factor** — "clarification required … treatment/material handling … or combustion … share no accounting meaning" | `PRODUCT_CAPABILITY` + **PO DECISION REQUIRED** | **Critical for the waste demo lane** | A PO decision on waste activity semantics; without it *no* waste invoice can complete the automatic lane regardless of extraction quality |
| **GAP-02-07** | **No supplier matching / creation / reuse of any kind** | `PRODUCT_CAPABILITY` (PO C-06 / D-09 unresolved) | **Critical** | Design an org-scoped supplier resolution step (normalise name + address; suggest, never silently choose). **PO DECISION REQUIRED** on auto-match vs operator confirm |
| **GAP-02-08** | `emissions_logs.supplier_id` is never populated by the write path (documented in `backend/domain/insight_query.py`) | `PRODUCT_CAPABILITY` (PO C-06 / D-09) | High | Same decision as GAP-02-07; blocks supplier-level reporting/Insight grouping |
| **GAP-02-09** | `page_count` reported as **2** for five 1-page documents | `PRODUCT_CAPABILITY` (low) | Low | Verify page counting before trusting it in evidence (renderer trailing page vs reader quirk) |
| **GAP-02-10** | PE workbench mapping route returns 403 for these items (created `CARBONTALLY_INTERNAL`, unassigned to any entity) | `ENVIRONMENT_TOPOLOGY` / `FIXTURE_DATA` | Low | **Not a defect** — correct PE isolation. Exercising that route needs the PE-assignment workflow (separate scenario, out of scope) |
| **GAP-02-11** | Invoice-number year prefix disagrees with the billing period (`INV2026004869` with a 2025-06 period) | `FIXTURE_DATA` (generator behaviour, documented in P12-DOC-03) | Informational | Not a CarbonTally issue; preserved so the demo shows realistic messiness |

No `DEMO_LAB_HARNESS`, `TEST_DRIFT`, `DOCUMENTATION_CONTRACT` or `UNKNOWN` findings arose.
In particular **no harness defect blocked this test**: the real product API was used
throughout, and the one known harness limitation (binary-response decoding in
`t3_scenarios.api()`, G-07 of the demo-journey audit) was avoided rather than patched
because it was not needed.

## Q.1 Product changes required (recommendation only — NOT implemented here)

Per §24 this is **not** a trivial defect correction, so it is documented rather than
implemented. Dependency order:

1. **Supplier/customer header extraction** for PDFs — populate `extracted_data.supplier`
   (and `customer`) so `unresolved: ["supplier"]` stops blocking and supplier attribution
   becomes possible at all. *(Extraction layer; no schema change.)*
2. **Tabular row parsing** (or P1 promotion with the GAP-02-05 defects fixed) so a
   multi-line PDF invoice yields trustworthy `line_items[]` with `quantity`/`unit`.
   *(Extraction layer; no schema change.)*
3. **Waste activity disambiguation** so a `Waste` line resolves to a factor family instead
   of a hard clarification block. *(Factor/mapping layer; **PO decision required**.)*
4. **Org-scoped supplier resolution** (match-or-create, suggest-don't-silently-choose) plus
   **supplier propagation onto the calculation/emissions write path**, so multi-year reuse
   and supplier-level reporting become demonstrable. *(Mapping + calculation layers;
   **PO decision required**, PO C-06 / D-09.)*

Until at least 1–3 exist, the investor PDF lane cannot reach calculation, evidence or
reporting through the automatic path.

---

# R. Product Changes

```text
PRODUCT CODE CHANGES: NONE
```

* No product source file was modified:
  `git diff 0fee936..HEAD -- ':!docs' ':!tools/demo_lab'` is **empty**.
* No P1 mode was promoted or changed; the running backend's environment was not modified.
* No migration, RLS policy, database object or configuration was changed.
* No table was written to directly; the only database writes were the 6 uploads performed
  by the product's own ingestion API.

**Harness / tooling changes (additive — not defect fixes):**

| File | Change | Why |
| --- | --- | --- |
| `tools/demo_lab/p12_gap02_acceptance.py` | **new** (~175 lines): real uploads, queue/item observation, isolated P1 shadow-vs-enabled probes, evidence dump | Makes this acceptance reproducible from one documented command |
| `docs/architecture/CT-PO-P12-GAP-02-CANONICAL-PDF-SUPPLIER-REUSE-20260924.md` | **new** | This mandatory report |

**External evidence written** (Demo Lab state dir, outside the repo):
`$HOME/ct_local_env/demo_lab/evidence/p12_gap02_acceptance.json`,
`p12_gap02_product_path.json`, `p12_gap02_operator_path.json`.

**Corpus:** unchanged — the six PDFs and the oracle manifest were read only.
**Demo database used:** `carbontally_demo_local`. **Production touched:** NO.

---

# S. Test Results

Commands run (all from `/home/shomonrobie/ct_93d5cdd`, with the Demo Lab backend
environment sourced for the offline probes):

```text
1. safety / identity
   psql -h 127.0.0.1 -p 54426 -U postgres -d carbontally_demo_local -Atc 'SELECT current_database()'
   -> carbontally_demo_local ; protected envs carbontally_test / carbontally_qa_phase8 = 0 lab users

2. corpus integrity
   recomputed SHA-256 of all 6 canonical PDFs vs tools/demo_lab/p12_canonical_manifest.json
   -> 6/6 matched

3. acceptance runner (real uploads + observation + P1 probes)
   ./backend/.venv/bin/python tools/demo_lab/p12_gap02_acceptance.py
   -> 6/6 uploads HTTP 201 ; 6/6 manual_review ; shadow_items=0 x6 ; enabled_items=3,4,6,3,4,4

4. offline P1 mode resolution
   python -c "from services import extraction_fidelity as p1; print(p1.shape_mode(), p1.rollout_status())"
   -> shadow ; in_rollout False, allowlist_size 0

5. offline extraction (shadow default) on p12canon_waste_001.pdf
   -> status ok, method pdf_text, confidence 0.3333
      keys ['activity','date','invoice_number'] ; supplier None ; customer None
      quantity None ; unit None ; line_items absent
      unresolved ['quantity/unit','supplier']

6. offline extraction probe with CARBONTALLY_P1_EXTRACTION_SHAPE=enabled (+ allowlist '*')
   (isolated subprocess; NOT a promotion)
   -> line_items for 6/6 with the quality defects recorded in §H ; supplier/customer still None x6

7. operator product-path probes
   GET/POST /api/v3/ops/entities/{entity}/extraction/items/{item}/{mapping-options,map,calculate}
     as pe_manager  -> 403 "Item is not effectively assigned to this processing entity"
     as org_a_owner -> 403
   PUT /api/v3/manual-extraction/items/{item} -> NOT called with values (deliberate; §7/§20)

8. regression surfaces
   GET /api/v3/reports?organization_id=…                -> 200 (4 reports)
   GET /api/v3/reports/{id}/content                     -> 200
   GET /api/v3/reports/{id}/versions                    -> 200
   GET /api/v3/emissions/calculations?organization_id=… -> 200, total 2 (CSV only)
   GET /api/v3/evidence/line-items/9252ca02-…           -> 200 (CSV evidence, FORWARD)

9. database impact
   before: snapshots=2 emissions=2 evidence=2 suppliers=1 reports=4 items=11
   after : snapshots=2 emissions=2 evidence=2 suppliers=1 reports=4 items=17   (+6 items = the 6 uploads)
```

| Result | Value |
| --- | --- |
| Canonical PDFs tested | **6/6** |
| Uploads accepted (HTTP 201) | **6/6** |
| Extraction executed | **6/6** |
| Supplier extracted | **0/6** |
| Customer extracted | **0/6** |
| `line_items[]` produced (primary path) | **0/6** |
| Mapped | **0/6** |
| Calculated | **0/6** |
| Evidence lines created | **0/6** |
| Supplier identities persisted | **0** |
| Reports affected | **0** (report path itself unregressed, 200s) |
| Product code changes | **NONE** |
| Harness defect fixes | **NONE required** |

No test was written to pass; the acceptance runner asserts nothing and only records
observations, deliberately, so that no observation can be tuned.

---

# T. Acceptance

```text
CANONICAL PDF UPLOAD: PASS

PDF EXTRACTION: PARTIAL

SUPPLIER EXTRACTION: FAIL

CUSTOMER EXTRACTION: FAIL

LINE-ITEM EXTRACTION: FAIL

MAPPING: FAIL

CALCULATION: FAIL

EVIDENCE/PROVENANCE: FAIL

SUPPLIER PERSISTENCE: FAIL

SUPPLIER REUSE: FAIL

MULTI-YEAR: FAIL

REPORTING: FAIL

INVESTOR PDF DATA JOURNEY: FAIL

STEP 2: INCOMPLETE

STEP 3: NOT STARTED
```

**Rationale for the two non-obvious verdicts**

* `PDF EXTRACTION: PARTIAL` — extraction genuinely runs and gets real things right
  (`activity` 6/6, invoice reference 4/6, date 4/6 with one format variance), but the
  fields that matter for the journey (supplier, customer, line items, quantity, unit) are
  absent, so a flat PASS would be dishonest.
* `REPORTING: FAIL` — *for the canonical PDF journey*, no canonical data reached reporting
  (the dependency chain is recorded in §O). The separately-run regression checks show the
  reporting product itself is **not** regressed (200s, 4 reports, calculations surface
  intact) — the failure is that the PDF data never arrives, not that reporting broke.

**Existing Step-2 blockers remain untouched by this task:** migration repeatability,
the `210 vs 218` policy variance, and the disposable integration acceptance are all
unchanged and **not** cleared here. Step 2 is not complete on the basis of this test — in
fact this test *adds* product-capability evidence that the investor PDF lane is not yet
demonstrable end-to-end.




