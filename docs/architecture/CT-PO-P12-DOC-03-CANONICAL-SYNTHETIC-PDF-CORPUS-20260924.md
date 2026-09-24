# CT-PO-P12-DOC-03 — Canonical Synthetic PDF Provenance and Investor Demo Corpus

# A. Task Identity

```text
P12-DOC-03-20260924-CANONICAL-SYNTHETIC-PDF-CORPUS
```

**Date:** 2026-09-24
**Repository:** `/home/shomonrobie/ct_93d5cdd` (branch `p8-release-reconciled`)
**Scope:** establish the authoritative source and provenance of the PDFs used in the
CarbonTally investor Demo Lab, and establish the canonical investor-demo source
corpus that subsequent extraction acceptance testing MUST use.

> **This task is not the extraction task.** P1 `shadow` mode was not changed, no
> extraction code was touched, no supplier extraction/matching was implemented, and
> **no CarbonTally table was written**. Nothing here claims that CarbonTally can
> extract the canonical corpus — that is the following, separate task.

---

# B. Environment Safety

| Item | Value |
| --- | --- |
| Repo | `/home/shomonrobie/ct_93d5cdd`, branch `p8-release-reconciled`, HEAD `25873f6` at start |
| Demo Lab target (documented, not written to) | `127.0.0.1:54426` — `carbontally_demo_local`, container `supabase_db_carbon_ledger` |
| Production | **NEVER authorized, never contacted** |
| `carbontally_test` | not modified |
| `carbontally_qa_phase8` | not modified |
| Protected flagship data | not modified |
| Database writes performed by this task | **NONE** (read-only recon only) |
| Destructive resets | **NONE** |
| External generator repo | `/home/shomonrobie/carbon_tally_synthetic_documents` — **verified UNCHANGED** (`git status --porcelain` byte-identical before/after generation) |

No database statement of any kind was issued against a CarbonTally database in this
task. The only writes were files in the Demo Lab state directory
(`$HOME/ct_local_env/demo_lab/corpus/p12-canonical-demo-v1/`) and the new tooling +
report in the repo.

---

# C. Existing PDF Provenance

## C.1 Where the 10 Step-2 PDFs actually came from

They are **not** Demo Lab fixtures and **not** hand-authored. The chain is:

```text
https://github.com/shomonrobie/carbon_tally_synthetic_documents_generator
        |  checkout pinned at commit 8ade2bf778d518d59924905849ab114ab2d0820a
        v
/tmp/extgen/  (offline producer checkout -- NO LONGER EXISTS, deleted)
        |  t3_scenarios.py sync-corpus --source /tmp/extgen
        |  selection: method "real-extractor-activity-quantity-unit-v2",
        |             selection_seed 42, chunk 30, cap 240
        v
$HOME/ct_local_env/demo_lab/corpus/t3-uk-curated-v1/   (outside the repo, 49 files)
        |  POST /api/v3/uploads  (Step-2 audit, 10 of the corpus documents)
        v
document_processing_queue   (all 10 -> manual_review)
```

Recovery of the provenance record: `corpus_provenance.json` records
`source: "/tmp/extgen"` and, per document, a `source_pdf` path of the form
`/tmp/extgen/samples/hierarchical_structure/…` plus `pdf_sha256`, `truth_sha256` and
`document_generation_seed`. The generator **checkout itself survives** at
`/home/shomonrobie/carbon_tally_synthetic_documents` at the same pinned commit with
`samples/hierarchical_structure/` intact (1,909 PDFs), so the recorded `source_pdf`
paths still resolve to real files under that checkout.

**Known provenance degradation (disclosed, not hidden):**
`docs/verification/OHD_TASK_079_DEMO_T3_INDEPENDENT_VERIFICATION_20260920.md` recording
O-D states that OHD re-syncs **rewrote** `corpus_provenance.json` — *"the shipped file
is not in git"* — so the original `source` / `candidates_considered` attribution was
lost. `documents[]` now holds **11** entries while the corpus directory holds **24**
documents; the remaining corpus files are attributable by name convention only.

## C.2 Provenance table — the 10 documents used in the Step-2 audit

Path column is `<state>/corpus/t3-uk-curated-v1/<file>`; SHA-256 was recomputed from
disk and compared against the `pdf_sha256` recorded in `corpus_provenance.json`.

| PDF | Path | SHA-256 (matches record) | Source Generator | Original Generation Run | Used in Step-2 Audit |
| --- | ---- | ------------------------ | ---------------- | ----------------------- | -------------------- |
| `t3imp_uk-gas__ORG_022_british_gas_202511.pdf` | `…/t3-uk-curated-v1/` (mtime 2026-09-20 21:18:56) | **YES** | generator @ `8ade2bf…` | `selection_seed 42` via `/tmp/extgen` (deleted) | yes — doc `c181203e` |
| `t3imp_uk-water__ORG_030_thames_water_202605.pdf` | same dir | **YES** | same | same | yes — `46011f73` |
| `t3imp_uk-electricity__ORG_027_octopus_energy_202510.pdf` | same dir | **YES** | same | same | yes — `214ca5e4` |
| `t3imp_uk-ambiguity__ORG_027_octopus_energy_202608.pdf` | same dir | **YES** | same | same | yes — `d3ca8cce` |
| `t3imp_uk-diesel__ORG_029_certas_energy_202509.pdf` | same dir | **YES** | same | same | yes — `d8442d19` |
| `t3imp_uk-waste__ORG_018_biffa_waste_202601.pdf` | same dir | **YES** | same | same | yes — `589d751d` |
| `t3imp_uk-missing-evidence__ORG_018_national_rail_202511.pdf` | same dir | **PARTIAL — no shipped record** | generator @ `8ade2bf…` (attributable from T3 scenario naming + `t3_manifest.json`) | **UNKNOWN** (entry lost in the OHD re-sync overwrite, O-D) | yes — `dfc9dec9` |
| `t3imp_consultant-client-a__ORG_029_edf_energy_202510.pdf` | same dir | **YES** | same | same | yes — `37e60e8c` |
| `t3imp_consultant-client-b__ORG_019_veolia_uk_202602.pdf` | same dir | **YES** | same | same | yes — `3265a235` |
| `t3imp_direct-org-b-isolation__ORG_019_e.on_energy_202602.pdf` | same dir | **YES** | same | same | yes — `37d039fa` |

**Result: 9 / 10 fully hash-verified against the shipped provenance record; 1 / 10
attributable to the pinned generator but with no shipped per-document record.**

## C.3 What those 10 documents actually contain (the problem for the investor story)

Read from their own ground-truth sidecars:

| Step-2 PDF | Supplier (printed) | Customer (printed) | Period | Line items |
| --- | --- | --- | --- | --- |
| `…edf_energy_202510` | Smart Utilities PLC | Future Power Ltd | 2025-02 | 5 |
| `…veolia_uk_202602` | Sustainable Eco & Co | Future Power Group | 2025-10 | 3 |
| `…e.on_energy_202602` | Eco Power Ltd | Bright Utilities Group | 2026-04 | 3 |
| `…octopus_energy_202608` | Future Resources PLC | Eco Utilities Group | 2025-06 | 5 |
| `…certas_energy_202509` | Clear Eco PLC | Energy Eco Ltd | 2026-08 | 2 |
| `…octopus_energy_202510` | Power Power Ltd | Pure Eco Ltd | 2025-01 | 3 |
| `…british_gas_202511` | Clear Power PLC | Bright Direct PLC | 2025-04 | 3 |
| `…national_rail_202511` | Pure Utilities Group | Future Direct & Co | 2026-01 | 4 |
| `…biffa_waste_202601` | Green Energy Ltd | Clear Eco & Co | 2026-07 | 4 |
| `…thames_water_202605` | Eco Energy Ltd | Pure Direct & Co | 2025-02 | 5 |

Across the whole 24-document T3 corpus there are **23 distinct suppliers and 21
distinct customers** — i.e. **every document names a different company**. There is no
recurring supplier, no recurring customer, and no canonical investor identity. That is
precisely why a new canonical corpus is required.

---

# D. Generator Verification

`https://github.com/shomonrobie/carbon_tally_synthetic_documents_generator`
(local checkout `/home/shomonrobie/carbon_tally_synthetic_documents`, HEAD
`8ade2bf778d518d59924905849ab114ab2d0820a` — identical to the pin recorded by the T3
corpus and the Step-2 environment record). **Read-only inspection; repository not
modified** (verified before/after).

| Capability question | Finding |
| --- | --- |
| Supplier/customer invoice relationships? | **YES.** `generator/main.py::DocumentGenerator` orchestrates `DataFactory` (content) → `ReportLabRenderer` (PDF) → `GroundTruthBuilder` (sidecar JSON) → `ManifestBuilder`. |
| Direct customers? | **YES.** `BulkCarbonTallyGenerator.generate_organizations(sector_counts, customer_type='direct')`; `generation_report.md` records 13 direct + 14 consultant-client organisations. |
| Consultant clients? | **YES.** `generate_consultants(count, min_clients, max_clients)` assigns only `customer_type='client'` orgs; hierarchical output `consultants/<Consultant>/<Organization>/`. |
| Multiple reporting periods? | **YES.** `DataFactory.create_dates()` selects a full calendar month in **2025 or 2026**; `create_invoice_number()` uses an independent 2024–2027 prefix year; `generate_document_specs_for_stream` iterates monthly/quarterly. |
| Realistic invoice line items? | **YES — including the exact waste/recycling domain.** `generator/data_factory.py::_generate_description` emits `"Recycling services - {type}"`, `"Waste disposal - {type}"`, `"Waste collection - {type}"` with types `General / Recycling / Hazardous / Organic / Mixed`. |
| Quantity/unit/rate/net/subtotal/tax/total in ground truth? | **YES — all present.** Line items carry `quantity`, `unit`, `unit_price`, `net_amount`, `vat_rate`, `vat_amount`, `gross_amount`; document carries `net_total`, `vat_total`, `gross_total`. |
| Supplier and customer in structured ground truth? | **YES.** `supplier`, `supplier_address`, `customer`, `customer_address` at document level. |
| Enough information for CarbonTally extraction? | **Structurally yes** — text-native PDFs with a labelled item table (`Description / Qty / Unit / Rate / Subtotal`), invoice ref, date, buyer and period. **Whether the current release extractor parses them is NOT tested here** (see J). |

**Naming limitation (decisive for §6):** all company names come from small pools —
`DataFactory.COMPANY_PREFIXES = ["Green","Eco","Power","Energy","Sustainable", …]`,
`COMPANY_SUFFIXES = ["Energy","Power","Solutions","Resources","Services","Utilities","Supply","Direct","Eco"]`,
`create_company_name()` = `f"{prefix} {suffix} {Ltd|PLC|& Co|Group}"`; and
`business_ecosystem.py` has a second pool
(`British/London/National/United/Western/Northern/Central/Royal/Imperial/Premier`).
**`Robinsons Recycling Services Ltd` cannot be produced by any pool** — there is no
`Robinsons` prefix and no `Recycling` suffix anywhere in the generator
(`grep -rn 'Robinsons'` → **zero hits**). Conversely `Sustainable Direct Group` **is**
producible (`Sustainable` + `Direct` + `Group`).

---

# E. Local Corpus Verification

`/home/shomonrobie/carbon_tally_synthetic_documents/output_all_variations`

| Property | Finding |
| --- | --- |
| Corpus size | **1,155 files** = **579 documents** (576 PDF + 3 CSV) + **576 ground-truth JSON**; `manifests/` exists but is empty |
| Structure | `documents/`, `ground_truth/`, `manifests/` |
| Document types | 8 × 72: `general_invoice`, `electricity_bill`, `travel_document`, `fuel_invoice`, **`waste_invoice` (72)**, `gas_bill`, `logistics_invoice`, `water_bill` |
| Suppliers | **299 distinct** generated names (`Pure Resources Ltd`, `Smart Supply Group`, `Sustainable Resources Ltd`, …) |
| Customers | **289 distinct** (`Pure Services & Co`, `Sustainable Direct Group` ×5, …) |
| Reporting periods | 2025 and 2026 calendar months |
| Ground-truth metadata | **YES** — one `.json` sidecar per document, `schema_version 1.0` |
| Deterministic/reproducible | **YES** — per-document `generation_seed` + repo `base_seed`; pools stable at the pinned commit |
| Corresponds to the GitHub generator? | **YES** — same repo/commit, produced by `run_generation.py`; `generation_report.md` records the bulk run (`Job 3539fbf5-…`, seed 42, 27 orgs, 1,688 PDFs, 12 months) |
| The uploaded reference sample | `diff_realistic_waste.pdf` **is a member of this directory** — confirmed generator output (`document_type waste_invoice`, `generation_seed 1402237045`, supplier `Sustainable Solutions Group`, customer `Sustainable Direct Group`, invoice `PWR/2024/1437`, period 2025-03) |

**Why selection alone is not enough.** A census of every generated corpus
(`samples/hierarchical_structure` 1,895 docs; `output_all_variations` 576;
`output_bulk` 2,000) shows customer `Sustainable Direct Group` appearing only
**4 / 5 / 4** times respectively, with **exactly one** `waste_invoice` for that
customer in all of the generated data. There is **no existing coherent multi-year
waste/recycling set** for the canonical customer, so the canonical corpus is
**generated** (explicitly permitted by the task objective) rather than selected.

Best fallback candidates had generation been impossible: the 72 `/waste_invoice/`
documents in `output_all_variations` (recycling-domain, full ground truth) — but none
carry the canonical supplier, and none hold a stable customer across years.

---

# F. Canonical Corpus

```text
corpus_id : p12-canonical-demo-v1
supplier  : Robinsons Recycling Services Ltd      (canonical)
customer  : Sustainable Direct Group              (canonical)
years     : FY2025, FY2026
documents : 6 text-native PDF waste invoices + 6 ground-truth sidecars
```

## F.1 Location and file handling (§14)

| Item | Value |
| --- | --- |
| Corpus (external, outside both repos) | `$HOME/ct_local_env/demo_lab/corpus/p12-canonical-demo-v1/` |
| Layout | `documents/` (6 PDF, 3.7–5.6 KB each, **28 KB total**), `ground_truth/` (6 JSON), `manifests/`, `canonical_manifest.json`, `corpus_provenance.json` |
| Copied into the CarbonTally repo? | **No PDFs.** Only the small oracle manifest is committed (`tools/demo_lab/p12_canonical_manifest.json`, 14 KB) plus the regeneration driver. No large corpus is committed. |
| Regeneration | `myenv/bin/python tools/demo_lab/p12_canonical_corpus.py --generator-root <checkout> --output-dir <path>` |

## F.2 How it was generated (and what was NOT done)

The generator is used **strictly as a library**; **its repository was not modified**
(`git status --porcelain` identical before and after; `diff` of the snapshots: no
difference).

| Aspect | Value |
| --- | --- |
| Method | New Demo Lab driver `tools/demo_lab/p12_canonical_corpus.py` imports the pinned generator's own `DocumentGenerator`, `schemas`, `DataFactory`, `DocumentBuilder` |
| Category | `DocumentCategory.WASTE` for all six |
| Line items | 2–5 per document, differing per document |
| Difficulty mix | `clean` ×2, `realistic` ×3, `difficult` ×1 |
| Scan | `has_scan=False` for all six → **text-native** (extractable without OCR) |
| Currency | `GBP`, 2 decimals |
| Table variants | varied per document (1–6) |
| **Only binding applied** | `supplier = "Robinsons Recycling Services Ltd"`, `customer = "Sustainable Direct Group"` via a documented `CanonicalNameDataFactory(DataFactory)` subclass |
| Everything else | **generator-produced**: line-item descriptions, quantities, units, unit prices, VAT, gross amounts, totals, addresses, invoice numbers, billing periods, layouts, seeds |
| Periods | **selected, not edited** — candidate document ids searched deterministically against the generator's own `create_dates()` derivation until their period fell in 2025 / 2026 |
| CarbonTally tables written | **NONE** |

**Why the name binding was technically necessary (documented deviation).** All six
PDFs are rendered by the pinned generator; had the names come from its pools, the
supplier would have been one of 299 pool names — none of which is
`Robinsons Recycling Services Ltd`, because no `Robinsons` token exists in the
generator (§D). Two options existed: (a) ship a corpus whose supplier is *not* the
canonical supplier, contradicting §6/§13, or (b) bind the two canonical business names
at generation time. Option (b) was taken, is confined to two fields, and is recorded
in `corpus_provenance.json`. **No PDF was hand-authored, no field was invented, and no
CarbonTally data was touched.**

## F.3 Verification performed on the corpus

Every document was text-extracted (`pdftotext -layout`) and checked for the canonical
supplier name, the canonical customer name, the invoice reference, arithmetic
coherence of `line items → subtotal → VAT → total`, and manifest/ground-truth
agreement. **All six passed every check (`ALL CANONICAL CHECKS: PASS`).**

Sample of the printed rendering (`p12canon_waste_001`):

```text
                Robinsons Recycling Services Ltd
                        850 Green Lane
                           Sheffield
                           QI14 5ZD
                              UK
             WASTE INVOICE
Invoice #: SVC2025008717
Date: 2025-04-02
Buyer: Sustainable Direct Group
Period: 2025-03-01 – 2025-03-31
Description                    Qty    Unit     Rate       Subtotal
Recycling services - Mixed     90     tonnes   £107.64    £9,687.51
Waste disposal - General       64     tonnes   £190.22    £12,174.21
Waste disposal - Mixed         58     tonnes   £100.22    £5,812.76
                                        Subtotal:  £27,674.48
                                        VAT (20%): £5,534.89
                                        Total:     £33,209.37
```

**Documented generator behaviour (not a defect):** the invoice-number year prefix is
generated independently of the billing period (`create_invoice_number` draws 2024–2027;
`create_dates` draws the period month). Hence e.g. `INV2026004869` carries a
2025-06 period and `GRN/2027/1879` a 2026-01 period. This is realistic invoice
messiness and is **exactly** the behaviour of the uploaded reference sample
(`PWR/2024/1437` with a March-2025 period), which is itself generator output — good
evidence that the canonical documents sit in the same generator family.
**Rounding:** line items are rounded to 2 decimals; `net_total`/`vat_total` are the
rounded sums of the rounded line values; `gross_total = net_total + vat_total`
(verified for all six).

---

# G. Ground Truth Manifest

Authoritative machine-readable oracle:

```text
$HOME/ct_local_env/demo_lab/corpus/p12-canonical-demo-v1/canonical_manifest.json
repo copy (committed):  tools/demo_lab/p12_canonical_manifest.json
per-document sidecars : <corpus>/ground_truth/<document_id>.json  (schema_version 1.0,
                        emitted by the generator's own GroundTruthBuilder)
```

Because the supplier/customer are bound once at generation time, the sidecars carry
the canonical names directly — **the oracle needs no post-editing**, and extracted
CarbonTally data must be compared against it **as-is** (§10). The manifest adds
SHA-256 of both the PDF and the truth sidecar.

| # | document_id | invoice ref | invoice date | billing period | diff. | items | net | VAT | gross | generation seed | PDF SHA-256 (first 16) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `p12canon_waste_001` | `SVC2025008717` | 2025-04-02 | 2025-03-01 → 2025-03-31 | clean | 3 | 27674.48 | 5534.89 | 33209.37 | 4186588349 | `6142fd3d43156c46` |
| 2 | `p12canon_waste_002` | `SVC2024-8258` | 2025-03-05 | 2025-02-01 → 2025-02-28 | realistic | 4 | 35011.09 | 7002.22 | 42013.31 | 4053412604 | `b384148016dd4ac3` |
| 3 | `p12canon_waste_004` | `INV2026004869` | 2025-07-03 | 2025-06-01 → 2025-06-30 | realistic | 2 | 5318.44 | 1063.69 | 6382.13 | 2113872366 | `c659fb2eaad6322a` |
| 4 | `p12canon_waste_003` | `UTL2025-1409` | 2026-07-02 | 2026-06-01 → 2026-06-30 | clean | 5 | 11628.76 | 2325.76 | 13954.52 | 3956907747 | `f915c9a71a35d275` |
| 5 | `p12canon_waste_005` | `ECO2024006142` | 2026-07-07 | 2026-06-01 → 2026-06-30 | realistic | 3 | 8949.69 | 1789.93 | 10739.62 | 1713775427 | `9b2753cf2147beb3` |
| 6 | `p12canon_waste_006` | `GRN/2027/1879` | 2026-02-02 | 2026-01-01 → 2026-01-31 | difficult | 4 | 36484.57 | 7296.91 | 43781.48 | 1661663628 | `efcc1b223e3cb847` |

Line-item ground truth (all rows `activity_type=waste`, `unit=tonnes`, `vat_rate=0.20`):

| document_id | line items (`description | qty | rate | net`) |
| --- | --- |
| `001` | Recycling services - Mixed \| 90.0 \| 107.639 \| 9687.51 · Waste disposal - General \| 64.0 \| 190.222 \| 12174.21 · Waste disposal - Mixed \| 58.0 \| 100.22 \| 5812.76 |
| `002` | Waste collection - Recycling \| 112.0 \| 178.665 \| 20010.48 · Waste collection - Recycling \| 25.8 \| 189.996 \| 4901.90 · Waste disposal - Hazardous \| 63.5 \| 98.522 \| 6256.15 · Waste disposal - Recycling \| 47.6 \| 80.726 \| 3842.56 |
| `004` | Waste collection - General \| 4.6 \| 64.643 \| 297.36 · Waste disposal - Organic \| 42.8 \| 117.315 \| 5021.08 |
| `003` | Waste disposal - Mixed \| 16.0 \| 186.208 \| 2979.33 · Waste disposal - Mixed \| 29.0 \| 83.741 \| 2428.49 · Recycling services - Organic \| 18.0 \| 94.935 \| 1708.83 · Waste disposal - Mixed \| 26.0 \| 51.864 \| 1348.46 · Waste disposal - Hazardous \| 19.0 \| 166.508 \| 3163.65 |
| `005` | Waste disposal - Recycling \| 36.7 \| 127.074 \| 4663.62 · Waste disposal - General \| 17.2 \| 165.465 \| 2846.00 · Recycling services - Organic \| 8.0 \| 180.009 \| 1440.07 |
| `006` | Recycling services - Organic \| 41.98 \| 93.821 \| 3938.61 · Recycling services - Mixed \| 91.6 \| 141.134 \| 12927.87 · Waste collection - Recycling \| 41.42 \| 84.737 \| 3509.81 · Recycling services - Mixed \| 94.7 \| 170.098 \| 16108.28 |

Distinct across the corpus: **6 distinct invoice references**, **5 distinct billing
periods**, **6 distinct net totals**, **6 distinct gross totals** — i.e. not simple
text replacements (§8). Activity vocabulary is entirely waste/recycling and compatible
with the CarbonTally/DEFRA waste factor family. **No emission factor is invented
here**; mapping to the existing CarbonTally master data is the next task's concern.

## G.1 Per-document provenance bundle

`corpus_provenance.json` records: generator repo URL, checkout path, **commit
`8ade2bf778d518d59924905849ab114ab2d0820a`**, `base_seed 42`, `dirty_at_generation`
(pre-existing untracked files only — proven not caused here by the identical
before/after `git status`), the binding method and its reason, the
`period_selection` method, and a `{document_id: pdf_sha256}` map.

---

# H. Multi-Year Structure

```text
CarbonTally / Consultant-managed client   (tenancy role NOT decided here)
        |
        v
Customer : Sustainable Direct Group          (same organisation, both years)
        |
        v
Supplier : Robinsons Recycling Services Ltd  (same synthetic business entity, both years)
        |
        +-- FY2025 source documents ------------------------------+
        |   p12canon_waste_001  2025-03  3 items  gross 33,209.37 |
        |   p12canon_waste_002  2025-02  4 items  gross 42,013.31 |
        |   p12canon_waste_004  2025-06  2 items  gross  6,382.13 |
        |                                                         |
        +-- FY2026 source documents ------------------------------+
            p12canon_waste_003  2026-06  5 items  gross 13,954.52
            p12canon_waste_005  2026-06  3 items  gross 10,739.62
            p12canon_waste_006  2026-01  4 items  gross 43,781.48
```

The supplier string, supplier address and customer string are bound identically across
all six documents, so **Year 2 documents reference the same synthetic supplier business
entity as Year 1** — the structural precondition for the supplier-recognition/reuse part
of the investor story. Whether CarbonTally can actually *recognise* that sameness is a
separate question (§J, §K G-03/G-04).

**Relationship-model neutrality (§7):** nothing in these documents references a
consultant or a CarbonTally tenant, so the corpus supports both intended readings
without change:

```text
direct              : CarbonTally -> Sustainable Direct Group -> Robinsons Recycling Services Ltd
consultant-managed  : CarbonTally -> Consultant Firm -> Sustainable Direct Group -> Robinsons Recycling Services Ltd
```

The customer is printed under the generator's own label for this document family
(`Buyer:`). **No tenant architecture was modified.**

---

# I. Current-vs-Canonical Comparison

| Property | Existing Step-2 PDF corpus | Canonical generator corpus |
| --- | --- | --- |
| Supplier | **23 distinct pool names across the corpus; a different one per document** (Smart Utilities PLC, Clear Eco PLC, Green Energy Ltd, …). No recurring supplier. | **`Robinsons Recycling Services Ltd` — 1 supplier, identical in all 6 documents** |
| Customer | **21 distinct pool names; a different one per document** (Future Power Ltd, Bright Direct PLC, Pure Direct & Co, …). | **`Sustainable Direct Group` — 1 customer, identical in all 6 documents** |
| Invoice metadata | present in ground truth (`invoice_number`, `invoice_date`) | present in ground truth **and** verifiably printed (`Invoice #`, `Date`) |
| Reporting period | 10 documents spanning 2025-01…2026-08 (5 → 2026, 5 → 2025), one document each | 6 documents: 3 × FY2025, 3 × FY2026, 5 distinct periods |
| Multiple line items | YES — 2–5 per document | YES — 2–5 per document |
| Quantity | YES (`quantity`) | YES (`quantity`, e.g. 90.0 t) |
| Unit | mixed (`t`, `kWh`, `m3`, …) | `tonnes` throughout (waste domain) |
| Rate | YES (`unit_price`) | YES (`unit_price`, e.g. 107.639) |
| Net amount | YES (`net_amount`) | YES (`net_amount`), arithmetic verified |
| Tax | YES (`vat_amount`, 20%) | YES (`vat_amount`, 20%), arithmetic verified |
| Total | YES (`gross_total`) | YES (`gross_total`), arithmetic verified |
| Ground truth | YES — sidecar `schema_version 1.0`; **1 of the 10 has no shipped provenance record** | YES — sidecar `schema_version 1.0` for all 6, **plus SHA-256 of PDF and sidecar**, plus per-document generation seed |
| Supplier identity across years | **NO** — no supplier appears in more than one year for one customer; no stable pairing | **YES** — one supplier, one customer, both years |
| Canonical investor identities | **NO** | **YES** |
| Suitability for the investor demo | **Not suitable as the primary demo corpus** — it cannot show supplier continuity, supplier reuse, or a named recurring relationship. It remains useful as *extraction-hardness* material (difficulty across 8 document types, ambiguous/edge variants, scanned variants) and is untouched. | **Suitable** — see J |

**Verdict (§11):** the previous Step-2 PDFs are **appropriate as a robustness/edge
corpus and as provenance-verified material, but not appropriate as the investor-demo
corpus**, because every document names a different supplier and customer. The canonical
corpus is therefore additive; **the Step-2 corpus was not replaced or modified** (its
EV-01 evidence chain and the 10 queued documents remain exactly as recorded).

---

# J. CarbonTally Extraction Readiness

**Suitable for the next extraction acceptance test? YES — with explicit prerequisites.**

Why it is suitable:

* all six documents are **text-native** (`has_scan=False`), so the acceptance test does
  not depend on the OCR environment;
* they are **structurally representative** — labelled item table
  (`Description / Qty / Unit / Rate / Subtotal`), `Invoice #`, `Date`, `Buyer`,
  `Period`, plus `Subtotal / VAT (20%) / Total`;
* a **complete, unedited machine-readable oracle** exists for every document
  (supplier, customer, invoice ref, date, period, per-line qty/unit/rate/net/VAT/gross,
  document net/VAT/gross, generation seed), with SHA-256 for PDF and sidecar;
* **multi-year** structure exists (3 × FY2025, 3 × FY2026 on one supplier/customer);
* the corpus is **small and reproducible** (6 documents, 28 KB) and sits outside the
  repo, so it does not bloat the application;
* the activity vocabulary (`Recycling services`, `Waste disposal`, `Waste collection`,
  `tonnes`) is compatible with the existing CarbonTally/DEFRA waste factor family, so
  mapping can be tested against real master data.

Prerequisites / what the next task must NOT assume:

1. **Nothing has been proven about the extractor yet.** These documents have never been
   submitted to CarbonTally. There is no ingestion, extraction, mapping, calculation or
   evidence result for them — and this report claims none.
2. **P1 `shadow` mode is unchanged**, so per the Step-2 finding the PDF path may still
   produce a flat payload with `line_items[]` ABSENT (§K G-01). If that happens the
   acceptance test must record it as a product-capability result, not work around it.
3. **Supplier extraction is not implemented for PDFs** (§K G-03) and **no supplier
   matching exists** (§K G-04) — so "Year 2 links to the same supplier as Year 1" is
   very likely to fail *even though the corpus now makes the test possible*. That is
   exactly the outcome the acceptance test should surface.
4. The oracle is authoritative: **extracted CarbonTally data must not be adjusted to
   match it** (§10).

---

# K. Remaining Product Gaps

Referenced unchanged from the P12 Step-2 demo-journey audit
(`CT-PO-P12-DEMO-JOURNEY-AUDIT-20260924.md`). **None of these was fixed here.**

| ID | Gap | Relevance to this corpus |
| --- | --- | --- |
| **G-01** | PDF extraction emits a **flat** payload with `line_items[]` ABSENT (P1 multi-line shaper runs in `shadow`); 10/10 Step-2 PDFs measured | Determines whether the canonical invoices can yield addressable line items + evidence |
| **G-02** | The emission write path never populates `emissions_logs.supplier_id` (documented in `backend/domain/insight_query.py` as **PO C-06 / D-09 unresolved**) | Blocks supplier attribution on calculated rows |
| **G-03** | **Supplier extraction from PDF is NOT IMPLEMENTED** (0/10 Step-2 PDFs carried a `supplier` key), so validation blocks with `EXTRACTION_MISSING_FIELD (supplier)` | The canonical PDFs name the supplier prominently; whether the extractor captures it must be measured, not assumed |
| **G-04** | **Supplier matching / reuse across years is NOT IMPLEMENTED** — no match/resolve/ensure/get-or-create routine anywhere in `backend/` or `frontend/`; association exists only as an operator-supplied `mapped_supplier_id` | The capability the multi-year canonical corpus is designed to exercise, and the one most likely to fail |
| **G-05/G-06** | `final_report_file_name` left empty; duplicated `filename = …` statement in `backend/api/v3_reports.py` | Unrelated to this corpus; still open |
| **G-07** | `t3_scenarios.api()` cannot decode a binary response | Not exercised here (no API calls made) |
| **G-08** | `uk-water` `no_match` vs `EXPECTED_MATCHED` | Unrelated to the waste corpus |

Two further limitations discovered **in this task**:

* **L-01 (external generator, not a CarbonTally defect)** — generator company names
  come from small pools; arbitrary supplier names are unsupported, which is why the
  canonical naming required the documented two-field binding (§F.2).
* **L-02 (documentation/process)** — T3 `corpus_provenance.json` holds records for only
  **11 of its 24** documents because of the disclosed OHD re-sync overwrite (O-D); one
  of the 10 Step-2 PDFs therefore has no shipped provenance record and is attributed as
  **PARTIAL**, not asserted as verified.

---

# L. Changes

| File | Change | Why |
| --- | --- | --- |
| `tools/demo_lab/p12_canonical_corpus.py` | **new** (~270 lines) | Reproducible canonical-corpus generator; uses the pinned external generator as a library, writes outside both repos, emits manifest + provenance |
| `tools/demo_lab/p12_canonical_manifest.json` | **new** (14 KB) | The committed oracle for later extraction acceptance (§10) |
| `docs/architecture/CT-PO-P12-DOC-03-CANONICAL-SYNTHETIC-PDF-CORPUS-20260924.md` | **new** | This mandatory report |

**Not changed:** any product code; any migration; any RLS policy; any Demo Lab
container or database; the external generator repository (**verified UNCHANGED**); the
existing Step-2 T3 corpus and its `corpus_provenance.json`; the 10 queued Step-2
documents; the EV-01 evidence chain.

**External artefacts created (outside both repos):**
`$HOME/ct_local_env/demo_lab/corpus/p12-canonical-demo-v1/` — `documents/` (6 PDF,
28 KB), `ground_truth/` (6 JSON), `manifests/`, `canonical_manifest.json`,
`corpus_provenance.json`.

**Database used:** none. **Production touched:** NO. **Rows written:** none.

---

# M. Commit

| | |
| --- | --- |
| Before SHA | `25873f6` (`docs(p12): fix displaced evidence-manifest table row in demo-journey audit`) |
| After SHA | `3134a59` (`docs(p12-doc-03): canonical synthetic PDF corpus for investor demo …`) |
| Branch | `p8-release-reconciled` |
| Generator repo SHA (unchanged) | `8ade2bf778d518d59924905849ab114ab2d0820a` |
| Product-code diff | `git diff 25873f6..HEAD -- ':!docs' ':!tools/demo_lab'` → **empty** |

---

# N. Acceptance

```text
PDF PROVENANCE: PARTIAL
  9/10 Step-2 PDFs hash-verified against the shipped provenance record, with the pinned
  generator commit 8ade2bf… identified; 1/10 has no shipped per-document record (the
  disclosed OHD re-sync overwrite, O-D). Underlying run = selection_seed 42 via
  /tmp/extgen (deleted); the generator checkout itself survives locally.

GENERATOR CORPUS: PASS
  Generator verified capable of supplier/customer invoices, direct + consultant-client
  organisation pools, multi-period generation, waste/recycling line items, and full
  quantity/unit/rate/net/VAT/total ground truth. Its naming pools cannot produce the
  canonical supplier name (documented limitation L-01).

GROUND TRUTH: PASS
  schema_version 1.0 sidecars for 6/6 documents carrying supplier, customer, invoice
  ref, date, period, per-line qty/unit/rate/net/VAT/gross and document totals, plus
  the per-document generation seed; the manifest adds PDF + sidecar SHA-256.

MULTI-YEAR CORPUS: PASS
  3 x FY2025 + 3 x FY2026, one supplier and one customer across all six, with differing
  references, periods, quantities and totals.

INVESTOR DEMO CORPUS READY: YES
  for the SOURCE-DOCUMENT layer. Extraction / mapping / calculation acceptance for
  these documents is NOT established and is explicitly the next task.

STEP 2: INCOMPLETE
STEP 3: NOT STARTED
```
