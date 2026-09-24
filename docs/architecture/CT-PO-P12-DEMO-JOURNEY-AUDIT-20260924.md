# CT-PO-P12-DEMO-JOURNEY-AUDIT-20260924

**Reference:** `CT-PO-P12-DEMO-JOURNEY-AUDIT-20260924`
**Date:** 2026-09-24
**Task:** P12 Step-2 final — end-to-end investor demo data journey & reporting acceptance
**Repository:** `/home/shomonrobie/ct_93d5cdd` @ `p8-release-reconciled`
**Production:** **NEVER AUTHORIZED** — not accessed
**Status:** INVESTIGATION DELIVERABLE — Step 2 gate unchanged

> **No fabrication.** Everything below is measured against the running Demo Lab and
> the release source. Nothing was inserted directly, no evidence line was
> manufactured, no supplier relationship was hand-built, and no product code was
> changed.

---

# A. DEMO DATA JOURNEY AUDIT

## A.1 Environment verified BEFORE any action (§14)

| Item | Value |
| --- | --- |
| Repo under test | `/home/shomonrobie/ct_93d5cdd` (branch `p8-release-reconciled`, HEAD `790923f`) |
| Postgres endpoint | `127.0.0.1:54426` → container **`supabase_db_carbon_ledger`** |
| Target database | `carbontally_demo_local` (`current_database()` confirmed) |
| Backend DSN | `127.0.0.1:54426 / carbontally_demo_local` |
| Demo Lab marker | T1 manifest namespace `demo-lab-t1`; 14 `@demo-lab.carbontally.local` users |
| Protected `postgres` | 116 tables / **975 orgs** / 1,344 users / **14** lab-domain users / +1 user today (the documented `pe.beta.manager` lab identity) |
| `carbontally_test` | 117 / 15 / 717 / **0** lab-domain users |
| `carbontally_qa_phase8` | 133 / 25 / 498 / **0** lab-domain users |
| Production | **never contacted** |

The topology matched the expected chain (`ct_93d5cdd` tooling → `54426` →
`supabase_db_carbon_ledger` → `carbontally_demo_local`), so **no destructive
operation was attempted in this task** — none was required for the audit.

## A.2 Status by stage

| Stage | Status | Measured evidence |
| --- | --- | --- |
| **PDF ingestion** | **WORKS** | 10 PDFs uploaded through the real API (`POST /api/v3/uploads`), stored, queued (`document_processing_queue`, `file_type=PDF`) |
| **CSV ingestion** | **WORKS** | 1 CSV uploaded as `text/csv`, stored `file_type=SPREADSHEET` |
| **PDF extraction** | **WORKS (flat)** | `extracted_data` = `{date, unit, activity, quantity, gross_amount, net_amount, invoice_number}` — **no `line_items[]`** on any of the 10 |
| **CSV extraction** | **WORKS (tabular)** | `extracted_data` = `{date, supplier, line_items[], invoice_number, source_headers}`; `jsonb_typeof(line_items) = array` |
| **Structured line items** | **CSV only** | 0/10 PDF vs 1/1 CSV |
| **Mapping** | **PARTIAL** | CSV: matched (`Natural gas` → DEFRA-2025 `0.2027`). PDFs: 5 × `ambiguous`, 2 × `clarification required`, 1 × `no_match`, 1 × completeness `0.33 < 0.50`, 1 × **validation blocked (`EXTRACTION_MISSING_FIELD (supplier)`)** — the one PDF that mapped was then blocked because no supplier was extracted |
| **Supplier extraction from PDF** | **NOT IMPLEMENTED** | `SELECT count(*) … WHERE file_type='PDF' AND extracted_data ? 'supplier'` → **0** |
| **Supplier extraction from CSV** | **WORKS** | the CSV carries a `supplier` key per line |
| **Supplier reuse across years** | **NOT IMPLEMENTED** | `document_processing_queue.ai_mapped_supplier_id` **0/11**; `manual_extraction_items.mapped_supplier_id` **0/11**; `emissions_logs.supplier_id` **0/2**; **no supplier-match/resolve/ensure helper exists in the backend** (`grep` returns none) |
| **Multi-year** | **PARTIAL** | `calculation_snapshots.reporting_year` + `date` support periods; reports exist for 2024 and 2025 — but no supplier/entity continuity carries data between years |
| **Calculation** | **CSV: PASS · PDF: FAIL (this corpus)** | 2 snapshots + 2 emissions logs, both CSV-derived (`2469.169780`; `1706.734000`) |
| **Evidence / provenance** | **CSV: PASS · PDF: ABSENT** | 2 `evidence_line_items` (`FORWARD`, `extraction_method=csv`), 2/2 `source_line_item_id` links, Viewer 200 FULL; **0 evidence lines for any PDF** |
| **Reporting** | **WORKS** | 3 reports generated (`annual` 2024/2025), `status=completed`; `content`, `versions`, `download` all HTTP 200 from the real API |
| **Supplier master data (CRUD)** | **WORKS (manual)** | 1 supplier created through the real CRUD API (`British Gas`, `utility`, `GB`); org-scoped `suppliers.organization_id` |

## A.3 The decisive structural finding

```text
PDF  : upload ✓ → store ✓ → extract ✓ (FLAT) → line_items[] ✗ → supplier ✗
       → mapping partly OK → validation BLOCKS on a missing supplier
       → calculation ✗ → evidence ✗ → reporting (no rows to report)

CSV  : upload ✓ → store ✓ → extract ✓ (TABULAR) → line_items[] ✓ → supplier ✓
       → mapping ✓ → validation ✓ → calculation ✓ → evidence ✓ → reporting ✓
```

**PDF provenance is structurally weaker than CSV provenance.** The PDF path emits a
single flat activity record and the P1 multi-line shaper that would produce
`line_items[]` runs in `shadow` mode (unchanged, deliberately), so a PDF cannot
produce an addressable evidence line. This is a **product-capability limitation of
the current configuration**, not a harness defect and not something this task may
work around (no backfill, no synthetic lines, no `derive_line_candidates` change).

---

# B. CANONICAL INVESTOR DEMO SCENARIO (as actually supported today)

Only the **CSV lane is fully live**. The PDF lane is demonstrable as *ingestion +
extraction + validation surfacing honest blockers*, but **not** as a completed
calculation. The scenario below states what the environment can really show.

```text
Organisation : Demo Lab Organisation A  (3fd0f325-16a1-5b53-8fb8-27929cf218fa)
Supplier     : British Gas (2fd4072c…, type=utility, country=GB) [created via real CRUD API]
Facility/Asset: 1 facility + 1 asset on the same organisation
Reporting yrs : FY2024, FY2025

LANE 1 — CSV (fully working, EV-01 preserved)
  p12imp_org-a-multi-site-gas-2025.csv                             doc 7ab110df
     | POST /api/v3/uploads -> object storage -> document_processing_queue
     v
  extraction -> extracted_data {date, supplier, invoice_number,
                                source_headers, line_items[]}  jsonb_typeof = array
     v
  2 line items -> source_item 0193ba83 / source_file c806c0cc
     v
  mapping  kWh (Net CV) -> DEFRA-DESNZ factor aef1f0bb (0.2027), factor_kind=emission_factor
     v
  validation -> pass
     v
  calculation (server-side, deterministic)
     12181.4 kWh x 0.2027 = 2469.169780 kg CO2e   snapshot f452ee2c
      8420.0 kWh x 0.2027 = 1706.734000 kg CO2e   snapshot 47b346f5
     v
  evidence_line_items, materialisation_kind=FORWARD, extraction_method=csv
     line 1 -> 9252ca02 (payload hash 8b0a3800400c…) linked 1:1 to snapshot f452ee2c
     line 2 -> 0b7ba27b (payload hash f05b11fe2dd7…) linked 1:1 to snapshot 47b346f5
     source_line_item_id populated 2/2  OK   Source Evidence Viewer HTTP 200 FULL
     v
  emissions_logs b96b19f6 (2469.169780) . 647218e4 (1706.734000), Scope 1, 2025-05-05
     supplier_id = NULL   <- the gap (see section D, G-02)
     v
  REPORT  eabfc75c . annual . 2025 . completed
     content : period 2025-01-01 -> 2025-12-31
               scopes  Scope 1 = 4175.903780 kg CO2e   (source DEFRA-DESNZ)
               totals  2 rows . 4175.903780 kg CO2e
               lineage emissions_logs + emission_factors . factor_ids [aef1f0bb…]
     versions 29353d06 v1 APPROVED   (DRAFT also produced)
     export  /download -> 200 JSON 5,108 bytes
             /pdf      -> 200 application/pdf 11,665 bytes  %PDF-1.4
                         filename report-eabfc75c-…-carbon_tally.pdf

LANE 2 — PDF (real ingestion/extraction; stops before calculation)
  10 supplier PDFs (British Gas, Thames Water, EDF, Veolia, E.ON, Octopus x2,
                    Certas, Biffa, National Rail)          docs c181203e … 46011f73
     | POST /api/v3/uploads -> storage -> queue  (file_type = PDF)
     v
  extraction -> FLAT payload {date, unit, activity, quantity, invoice_number,
                              gross_amount, net_amount}   line_items = ABSENT on 10/10
     v
  mapping    matched 1 . ambiguous 5 . clarification-required 2 .
             no_match 1 . completeness 0.33 < 0.50 1
     v
  validation EXTRACTION_MISSING_FIELD (supplier) -> BLOCKED / manual_review
             <- the one PDF that mapped was then blocked because no supplier
                was extracted from the PDF at all
     v
  calculation FAIL   evidence 0 lines   reporting rows NONE
```

**Year-over-year framing that is honest today:** the organisation, facility, asset,
supplier master record and reporting-period model all persist, and two consecutive
reporting years (2024, 2025) exist as independent reports. What does **not** yet
happen is the *supplier-linkage* step that would let the demo claim "Year 2 from the
same supplier is linked to the same supplier entity" - nothing populates
`emissions_logs.supplier_id` or `manual_extraction_items.mapped_supplier_id`
(0/2 and 0/11 measured), and no supplier-matching routine exists in the codebase.

---

# C. CAPABILITY MATRIX

| Capability | PDF | CSV | Status | Evidence | Classification |
| --- | --- | --- | --- | --- | --- |
| Upload | PASS | PASS | IMPLEMENTED | 10 PDF + 1 CSV via real upload API into `document_processing_queue` | — |
| Extraction | PASS (flat) | PASS (tabular) | IMPLEMENTED, asymmetric | `extracted_data` keys per document | PRODUCT_CAPABILITY |
| Structured line items (`line_items[]`) | **FAIL** | PASS | **GAP** | `jsonb_typeof` ABSENT 10/10 PDF vs `array` 1/1 CSV | PRODUCT_CAPABILITY (P1 shaper in `shadow`) |
| Mapping | PARTIAL | PASS | PARTIAL | queue mapping outcomes; snapshot `factor_id` `aef1f0bb` | PRODUCT_CAPABILITY |
| Supplier extraction | **FAIL (0/10)** | PASS (`supplier` key) | **GAP** | `extracted_data ? 'supplier'` | PRODUCT_CAPABILITY |
| Supplier to master-data association | FAIL (0/11) | FAIL (0/11) | **GAP** | `mapped_supplier_id` 0/11 | PRODUCT_CAPABILITY (PO C-06 / D-09) |
| Supplier reuse across years | FAIL | FAIL | **NOT IMPLEMENTED** | no match/resolve helper in repo; code comment admits it | PRODUCT_CAPABILITY |
| Multi-year | PARTIAL | PARTIAL | PARTIAL | reports FY2024 + FY2025; `reporting_year` on snapshots | PRODUCT_CAPABILITY |
| Calculation | **FAIL** (blocked) | PASS | PARTIAL | 2 snapshots, both CSV-derived | PRODUCT_CAPABILITY |
| Evidence / provenance | **FAIL (0 lines)** | PASS | PARTIAL | 2 `evidence_line_items`; `source_line_item_id` 2/2 | PRODUCT_CAPABILITY |
| Reporting | PASS | PASS | IMPLEMENTED | 4 reports `completed`; real aggregate 4175.903780 | — |
| Export | PASS | PASS | IMPLEMENTED | JSON 200/5,108 B; **PDF 200/11,665 B `%PDF-1.4`** | — |
| Report lifecycle (DRAFT to APPROVED) | PASS | PASS | IMPLEMENTED | `report_versions` 1 APPROVED + 3 DRAFT | — |

---

# D. GAP REGISTER

| ID | Capability | Current implementation status | Evidence | Smallest legitimate remediation | Step-2 blocker? |
| --- | --- | --- | --- | --- | --- |
| **G-01** | PDF to `line_items[]` | The P1 multi-line shaper exists but runs in **`shadow`** mode, so each PDF emits one flat record | `jsonb_typeof(line_items)` = ABSENT on 10/10 PDFs | Product/PO decision to promote the shaper out of `shadow` for the demo profile. **Not** a harness change and **not** permitted in this task | **No** (product enhancement) |
| **G-02** | Supplier identity on emissions | `emissions_logs.supplier_id` exists but the emission write path never populates it - the product's own source documents this | `emissions_logs.supplier_id` 0/2; verbatim in `backend/domain/insight_query.py`: "the emission write path never populates `emissions_logs.supplier_id` (PO C-06 / D-09 unresolved)" | Resolve **D-09 / C-06** (who owns supplier attribution) - **PO DECISION REQUIRED** - then wire the write path | **No** (PO decision) |
| **G-03** | Supplier extraction from PDF | Not implemented for any of the 10 PDFs | 0/10 `extracted_data ? 'supplier'` | Depends on G-01 plus an extraction rule for the supplier block | **No** (product enhancement) |
| **G-04** | Supplier matching / reuse across years | **NOT IMPLEMENTED** - no name-match, resolve, ensure or get-or-create routine anywhere in `backend/` or `frontend/`; supplier association exists only as an operator-supplied field (`POST /api/v3/items/{id}/map` with `mapped_supplier_id`) | repo-wide grep for supplier match/resolve/ensure/find/get_or_create returns only a docstring; `mapped_supplier_id` 0/11 | Design an org-scoped supplier resolution step (normalise name plus tax/registration/address; suggest, never silently choose) - **PO DECISION REQUIRED** on auto-match vs operator confirm | **No** (Step-3 / product) |
| **G-05** | Report artifact metadata | Structured 12-section JSON plus branded PDF both exist, but `final_report_file_name` is left empty on completed rows (the JSON download falls back to `report-<id>.json`) | `report_generation_queue.final_report_file_name` empty, `final_report_url` NOT NULL, sizes 1938 / 4522 | Populate `final_report_file_name` on completion | **No** (minor product) |
| **G-06** | Duplicated statement in product source | `backend/api/v3_reports.py` assigns `filename = report.get("final_report_file_name") or f"report-{report_id}.json"` **twice in a row** | lines ~468-469 of `v3_reports.py` | Delete the duplicate line | **No** (cosmetic dead code) |
| **G-07** | Harness cannot read binary responses | `t3_scenarios.api()` calls `raw.decode()` unconditionally, so a `%PDF-1.4` body raises `UnicodeDecodeError` in the *test client* | reproduced here; a raw `requests.get` returned 200 / 11,665 bytes | Return bytes when the response is not JSON | **No** - **DEMO_LAB_HARNESS**; must never be reported as a product failure |
| **G-08** | `uk-water` contract mismatch | `t3_scenarios.py` expects `EXPECTED_MATCHED`; the observed outcome is `no_match` | carried forward from Step 2 (T3 status record) | Reconcile the T3 expectation against the real factor set for Thames Water | **No** (carried forward, `DOCUMENTATION_CONTRACT`) |

Classification of every failure encountered in this task:

* `PRODUCT_CAPABILITY` - G-01, G-02, G-03, G-04, G-05, G-06
* `DEMO_LAB_HARNESS` - G-07
* `DOCUMENTATION_CONTRACT` - G-08
* `FIXTURE_DATA` / `TEST_DRIFT` / `ENVIRONMENT_TOPOLOGY` - none newly found
* `UNKNOWN` - the **210 vs 218** policy-count variance (section 13)

**No product code was changed in this task.** Nothing here required one, and G-01 to
G-04 are product/PO matters that this task is explicitly forbidden from "fixing" for
demo convenience.

---

# E. EVIDENCE MANIFEST

**Database:** `carbontally_demo_local` @ `127.0.0.1:54426` (container `supabase_db_carbon_ledger`), repo `ct_93d5cdd` @ `790923f`
**Organisation:** Demo Lab Organisation A - `3fd0f325-16a1-5b53-8fb8-27929cf218fa`

| Artefact | IDs / counts |
| --- | --- |
| Source document (CSV lane) | `7ab110df` `p12imp_org-a-multi-site-gas-2025.csv` (SPREADSHEET, `customer_review`) |
| Source documents (PDF lane) | `c181203e` uk-gas British Gas · `46011f73` uk-water Thames Water · `214ca5e4` uk-electricity Octopus · `d3ca8cce` uk-ambiguity Octopus · `d8442d19` uk-diesel Certas · `589d751d` uk-waste Biffa · `dfc9dec9` uk-missing-evidence National Rail · `37e60e8c` EDF · `3265a235` Veolia · `37d039fa` E.ON - all `manual_review` |
| Extraction items | `source_item` `0193ba83` (CSV), `source_file` `c806c0cc`; 11 `manual_extraction_items`; 4 `manual_extraction_batches` |
| Evidence line items | `9252ca02` line 1 hash `8b0a3800400c…` · `0b7ba27b` line 2 hash `f05b11fe2dd7…` - both `csv` / `FORWARD` |
| Calculation snapshots | `f452ee2c` (2025, 12181.4 kWh Net CV x 0.2027 = **2469.169780**, src line `9252ca02`) · `47b346f5` (2025, 8420.0 kWh x 0.2027 = **1706.734000**, src line `0b7ba27b`) |
| Emission factor | `aef1f0bb…`, `factor_source=DEFRA-DESNZ`, `factor_kind=emission_factor`, `customer_factor_id` NULL |
| Emissions logs | `b96b19f6` 2469.169780 · `647218e4` 1706.734000 (Scope 1, 2025-05-05); **`supplier_id` NULL 2/2** |
| Supplier master | `2fd4072c` **British Gas**, type `utility`, country `GB` (created through the real CRUD API) |
| Facility / Asset | 1 facility, 1 asset on Organisation A |
| Reports | `eabfc75c` annual 2025 **completed** · `1e01d6e4` annual 2024 completed · `60a76917` annual 2024 completed · `2f92c5e3` annual 2025 completed (generated during this audit) |
| Report versions | `29353d06` v1 **APPROVED** (eabfc75c) · `634be50c` v1 DRAFT · `c503ecbd` v1 DRAFT · `e09bf72a` v1 DRAFT - all `is_current` |
| Report totals | FY2025 Scope 1 = **4175.903780 kg CO2e**, 2 rows = 2469.169780 + 1706.734000 (equals the snapshot sum) |
| Report export | JSON `200` 5,108 bytes · **PDF `200` `application/pdf` 11,665 bytes `%PDF-1.4`**, `report-eabfc75c-…-carbon_tally.pdf` |
| Report types offered | `annual` only - "Annual emissions report (structured 12-section V3 report)" |
| Fresh evidence files | `$HOME/ct_local_env/demo_lab/evidence/p12_step2_demo_journey_audit.json` · `p12_step2_report_export.json` · `p12_step2_report_pdf_export.json` |

---

# F. FINAL ACCEPTANCE RECORD

```text
INVESTOR DEMO DATA JOURNEY: PARTIAL

PDF WORKFLOW: PARTIAL
  upload / storage / extraction / validation-surfacing PASS
  line_items[], supplier extraction, calculation, evidence FAIL

CSV WORKFLOW: PASS

SUPPLIER REUSE: FAIL   (NOT IMPLEMENTED - no extraction, no matching, no linkage)

MULTI-YEAR: PARTIAL
  period model + per-year reports PASS; supplier/entity continuity across years FAIL

EVIDENCE/PROVENANCE: PARTIAL
  CSV PASS (source_line_item_id 2/2, Source Evidence Viewer 200 FULL)
  PDF ABSENT (0 evidence lines)

REPORT GENERATION: PASS
  real aggregates from persisted emissions, DRAFT->APPROVED lifecycle,
  JSON + branded PDF export

STEP 2 GATE: INCOMPLETE

STEP 3: NOT STARTED
```

**Why the gate stays INCOMPLETE:** the two previously recorded Step-2 blockers are
untouched by this task and no new evidence clears them.

1. **Repeatability is not established** - migration re-application still adds
   policies, and the `210 vs 218` discrepancy remains `UNKNOWN` (section 13).
2. **Disposable integration acceptance is not green** - `12 failures / 92 tests`,
   including `get_profile_by_user()`, residual billing-table authenticated INSERT
   grants, six calculation FK fixture failures and stale consultant call sites.

A working CSV demonstration is not a Step-2 clearance, and this task does not treat
it as one.

---

# 13. REPEATABILITY - MECHANISM FINDING (carried forward, not resolved)

Preserved observations (unchanged by this task; no re-run performed, because the task
forbids re-running until counts match):

| Path | Tables | RLS | Policies |
| --- | --- | --- | --- |
| clean single pass A | 141 | 141/141 | 218 |
| clean single pass B | 141 | 141/141 | 218 |
| full `run_demo_lab.sh` pass | 141 | 141/141 | **210** |
| second migration application onto the same database | 141 | 141/141 | **298** (+ error on `20260801000000_rc2_constraints.sql`) |

**Mechanism established:** `298` is caused by **migration re-application** - the second
pass re-creates policy sets the first pass already created, so application is **not
idempotent** for policies. That is a harness/migration-application defect, not a
schema-design question.

**Mechanism NOT established:** `210` (full path) vs `218` (stack-only). Both are
*single* passes, so re-application cannot explain the difference; it must originate in
the additional steps of the full path or in ordering. This remains **`UNKNOWN`**.

Discriminating experiment for whoever picks this up (deliberately **not** run here):

```text
A) reset -> stack.py                 capture policy COUNT and full policy NAME SET
B) reset -> stack.py                 same
C) reset -> run_demo_lab.sh          same
D) reset -> stack.py ; provision.py  same
diff the NAME SETS (not just the counts) of A/B/C/D - the symmetric difference
names identify exactly which component adds or omits the 8 policies.
```

A count-only comparison cannot answer this; a **frozen policy name-set manifest** is
the required assertion artefact.

---

# 16. CHANGE RECORD

**Product code changed: NONE.**
Verification command at commit time: `git diff 790923f..HEAD -- ':!docs'` must be empty.

**Files changed by this task:** `docs/architecture/CT-PO-P12-DEMO-JOURNEY-AUDIT-20260924.md` (this document).

**Tests run:** none added - this was an investigation task and no product or harness
behaviour was modified, so no regression surface was introduced. All runtime evidence
was collected through the real authenticated API plus read-only SQL.

**Demo Lab database used:** `carbontally_demo_local` @ `127.0.0.1:54426`.
**Production touched:** **NO.**

**Remaining blockers:** the two Step-2 blockers above, plus G-01 to G-04 as
product/PO items (not Step-2 harness blockers).

**Recommendation: Step 2 cannot proceed to Step 3 yet.** The investor demo is
demonstrable end-to-end on the **CSV lane** (upload, extraction, line items, mapping,
calculation, evidence, reporting, branded PDF export) and honestly presentable on the
**PDF lane as an ingestion/extraction/validation story**, but the
supplier-extraction-and-reuse pillar of the intended narrative is
`NOT IMPLEMENTED` and depends on PO decisions (G-02 D-09/C-06, G-04 matching policy).
Clearing the gate still requires (1) idempotent migration application or a frozen
policy name-set assertion, including resolution of the `210 vs 218` mechanism, and
(2) a green or explicitly waived disposable integration run.
