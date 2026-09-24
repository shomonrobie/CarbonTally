# CT-PO-P12-DATA-01 — Canonical PDF Precision Contract

**1. Task Identity**

| Item | Value |
| --- | --- |
| Task ID | `P12-DATA-01-20260924-CANONICAL-PDF-PRECISION-CONTRACT` |
| Date | 2026-09-24 |
| Repository / branch | `/home/shomonrobie/ct_93d5cdd` @ `p8-release-reconciled` |
| Baseline commit (before analysis) | `ad07cd4` (`feat(p12-impl-01): PDF extraction foundation …`) |
| Type | **Forensics / data-contract / design — no implementation** |
| Corpus under analysis | `p12-canonical-demo-v1` (**FROZEN**) |
| Oracle under analysis | `tools/demo_lab/p12_canonical_manifest.json` (**FROZEN**, unmodified) |
| Artifact | `docs/architecture/artifacts/p12_data_01_precision_analysis_20260924.json` |
| Analysis tool | `tools/demo_lab/p12_data_01_precision_analysis.py` (read-only) |

**2. Scope and Safety**

Read-only analysis. **Nothing was changed**: no product code, no calculation logic, no supplier
logic, no waste semantics, no reporting, no Insight, no schema, no migration, no RLS, no
production, no test/QA environment, no supplier record, **no canonical PDF, no corpus, no
oracle**; P1 not promoted; corpus not expanded; P12-IMPL-02 not started; Step 3 not started.
**No database was touched** — no query was issued against any database, and the artifact records
`database_touched: false`. The analysis tool is demo-lab tooling (not the product implementation
path) and only reads files.

**3. Sources Inspected**

| # | Source | Used for |
| --- | --- | --- |
| 1 | `CT-PO-P12-DOC-03-…-CORPUS-20260924.md` | corpus provenance, generator pin, layout variety |
| 2 | `CT-PO-P12-GAP-02-…-SUPPLIER-REUSE-20260924.md` | pre-P1 measurements, incl. the "5.0 vs 4.6" observation |
| 3 | `CT-PO-P12-DECISION-01-…-CONTRACT-20260924.md` | "no silent normalisation" rule (§19) |
| 4 | `CT-PO-P12-IMPL-01-…-FOUNDATION-20260924.md` + its artifact | the extracted values and metrics reconciled here |
| 5 | `CT-PO-P12-DEMO-JOURNEY-AUDIT-20260924.md` | CSV/EV-01 provenance baseline |
| 6 | `CT-PO-P12-STEP2-FINAL-VERIFICATION-20260924.md` | Step-2 gate state |
| 7 | `tools/demo_lab/p12_canonical_manifest.json` | oracle / generator ground truth |
| 8 | `tools/demo_lab/p12_canonical_corpus.py` | how the corpus was produced (`decimal_places=2` was requested) |
| 9 | `$HOME/ct_local_env/demo_lab/corpus/p12-canonical-demo-v1/` | the six PDFs + `corpus_provenance.json` |
| 10 | generator repo @ `8ade2bf…` | `generator/data_factory.py`, `generator/reportlab_renderer.py` — the precision mechanism |
| 11 | `pdftotext -layout` output of all six PDFs | the PDF-**visible** text, independent of product code |

**4. Canonical Corpus Frozen-State Verification**

| Item | Value |
| --- | --- |
| Oracle SHA-256 | `0c478b716903a26376c83378ce9a4fdd3c55b1a4b62489c4b629ba0793149035` |
| `001` | `6142fd3d43156c467860802614d03b14895976af58be65b229a6c58feb01dc7f` |
| `002` | `b384148016dd4ac3c270c1572ac2ce3d7a9e17035baf8fa4502181311ff506fa` |
| `003` | `f915c9a71a35d275882675743149759e13902a1f5201c5f5e613477758070361` |
| `004` | `c659fb2eaad6322a394bf6b586dffc83da6021aacfa884b439ac6ca9bb28fd0f` |
| `005` | `9b2753cf2147beb3f5c45a718b9a30d55e2b5e30720a0b35ccc6f31bfcfa7dde` |
| `006` | `efcc1b223e3cb8473abfc0e3a1349283b14b8c792ed941a293b7a6d215b1777e` |

All six recomputed hashes **match `corpus_provenance.json`**; generator pin
`8ade2bf778d518d59924905849ab114ab2d0820a`; working tree showed only the pre-existing
`.gitignore` and pre-existing untracked PO artifacts — **no task-side modification**.

**5. Six-PDF Inventory**

| Document | FY | Invoice ref | Lines | Display precision (dp) from the printed total | Pipeline |
| --- | --- | --- | --- | --- | --- |
| `p12canon_waste_001` | 2025 | SVC2025008717 | 3 | **2** | `v3-auto-1.2` |
| `p12canon_waste_002` | 2025 | SVC2024-8258 | 4 | **0** | `v3-auto-1.2` |
| `p12canon_waste_004` | 2025 | INV2026004869 | 2 | **0** | `v3-auto-1.2` |
| `p12canon_waste_003` | 2026 | UTL2025-1409 | 5 | **2** | `v3-auto-1.2` |
| `p12canon_waste_005` | 2026 | ECO2024006142 | 3 | **3** | `v3-auto-1.2` |
| `p12canon_waste_006` | 2026 | GRN/2027/1879 | 4 | **4** | `v3-auto-1.2` |
| **Total** | | | **21** | corpus spans **0/2/3/4 dp** | |

**6. PDF-Visible Numeric Values**

Read with `pdftotext -layout` from the shipped PDFs — the values a real extractor can recover:

```text
001 (dp=2)  Recycling services - Mixed     90   tonnes £107.64       £9,687.51
            Waste disposal - General       64   tonnes £190.22     £12,174.21
            Waste disposal - Mixed         58   tonnes £100.22       £5,812.76
            Subtotal: £27,674.48   VAT (20%): £5,534.89   Total: £33,209.37

002 (dp=0)  Waste collection - Recycling - Qty: 112.0 ...            112  t  £179  £20,010
            Waste collection - Recycling - Qty: 25.8 t...             26  t  £190   £4,902
            Waste disposal - Hazardous - Qty: 63.5 tonnes             64  t   £99   £6,256
            Waste disposal - Recycling - Qty: 47.6 tonnes             48  t   £81   £3,843
            Subtotal: £35,011      VAT: £7,002        Total: £42,013

003 (dp=2)  Waste disposal - Mixed          16   tonnes  £186.21    £2,979.33
            Waste disposal - Mixed          29   tonnes   £83.74    £2,428.49
            Recycling services - Organic    18   tonnes   £94.94    £1,708.83
            Waste disposal - Mixed          26   tonnes   £51.86    £1,348.46
            Waste disposal - Hazardous      19   tonnes  £166.51    £3,163.65
            Net Amount: £11,628.76  VAT (20%): £2,325.76  Total: £13,954.52

004 (dp=0)  Waste collection - General (ID: None)      5  tonnes  £65    £297
            Waste disposal - Organic (ID: None)       43  tonnes  £117  £5,021
            Subtotal: £5,318     Tax (20%): £1,064     Total Due: £6,382

005 (dp=3)  Waste disposal                  36.700  t  £127   £4,664
            Waste disposal                  17.200  t  £165   £2,846
            Recycling services                8    t  £180   £1,440
            Net Total: £8,949.690  GST: £1,789.930  Net Payable: £10,739.620

006 (dp=4)  Recycling services - Organic   41.9800  tonnes  £93.8210   £3,938.6100
            Recycling services - Mixed     91.6000  tonnes £141.1340  £12,927.8700
            Waste collection - Recycling   41.4200  tonnes  £84.7370   £3,509.8100
            Recycling services - Mixed     94.7000  tonnes £170.0980  £16,108.2800
            Subtotal: £36,484.5700  Tax (20%): £7,296.9100  Total Due: £43,781.4800
```

**7. Generator / Oracle Numeric Values**

From `p12_canonical_manifest.json` (unmodified): full generator precision — e.g. `001` L1
`90.0 × 107.639 = 9687.51`; `002` L2 `25.8 × 189.996 = 4901.8968`; `004` L1
`4.6 × 64.643 = 297.3578`; `006` L1 `41.98 × 93.821 = 3938.60…`. Complete set: artifact
`line_comparisons[].oracle` and `document_comparisons[].oracle`.

**8. P12-IMPL-01 Extracted Values**

From the P12-IMPL-01 real-product artifact (actual product output, not reconstructed):
artifact `line_comparisons[].extracted` / `document_comparisons[].extracted`.

**9. Full 21-Line Comparison — all lines, all three layers**

`PDF → oracle → extracted` per field. **Rnd** = PDF display rounding of the oracle at the
document's `dp`, proven because `render(oracle, dp) == printed == extracted` using the
generator's own `f"{value:,.{dp}f}"` formatting.

| Doc | Ln | Description | qty | rate | line net | Class |
| --- | --- | --- | --- | --- | --- | --- |
| 001 | 1 | Recycling services - Mixed | 90 → 90.0 → 90.0 | 107.64 → 107.639 → 107.64 | 9,687.51 → 9687.51 → 9687.51 | qty/net exact · rate **Rnd** |
| 001 | 2 | Waste disposal - General | 64 → 64.0 → 64.0 | 190.22 → 190.222 → 190.22 | 12,174.21 → 12174.21 → 12174.21 | qty/net exact · rate **Rnd** |
| 001 | 3 | Waste disposal - Mixed | 58 → 58.0 → 58.0 | 100.22 → 100.22 → 100.22 | 5,812.76 → 5812.76 → 5812.76 | **all exact** |
| 002 | 1 | Waste collection - Recycling | 112 → 112.0 → 112.0 | 179 → 178.665 → 179.0 | 20,010 → 20010.48 → 20010.0 | qty exact · rate/net **Rnd** |
| 002 | 2 | Waste collection - Recycling | 26 → 25.8 → 26.0 | 190 → 189.996 → 190.0 | 4,902 → 4901.8968 → 4902.0 | **all Rnd** |
| 002 | 3 | Waste disposal - Hazardous | 64 → 63.5 → 64.0 | 99 → 98.522 → 99.0 | 6,256 → 6256.147 → 6256.0 | **all Rnd** |
| 002 | 4 | Waste disposal - Recycling | 48 → 47.6 → 48.0 | 81 → 80.726 → 81.0 | 3,843 → 3842.5576 → 3843.0 | **all Rnd** |
| 003 | 1 | Waste disposal - Mixed | 16 → 16.0 → 16.0 | 186.21 → 186.208 → 186.21 | 2,979.33 → 2979.33 → 2979.33 | qty/net exact · rate **Rnd** |
| 003 | 2 | Waste disposal - Mixed | 29 → 29.0 → 29.0 | 83.74 → 83.741 → 83.74 | 2,428.49 → 2428.49 → 2428.49 | qty/net exact · rate **Rnd** |
| 003 | 3 | Recycling services - Organic | 18 → 18.0 → 18.0 | 94.94 → 94.935 → 94.94 | 1,708.83 → 1708.83 → 1708.83 | qty/net exact · rate **Rnd** |
| 003 | 4 | Waste disposal - Mixed | 26 → 26.0 → 26.0 | 51.86 → 51.864 → 51.86 | 1,348.46 → 1348.46 → 1348.46 | qty/net exact · rate **Rnd** |
| 003 | 5 | Waste disposal - Hazardous | 19 → 19.0 → 19.0 | 166.51 → 166.508 → 166.51 | 3,163.65 → 3163.65 → 3163.65 | qty/net exact · rate **Rnd** |
| 004 | 1 | Waste collection - General | 5 → 4.6 → 5.0 | 65 → 64.643 → 65.0 | 297 → 297.3578 → 297.0 | **all Rnd** |
| 004 | 2 | Waste disposal - Organic | 43 → 42.8 → 43.0 | 117 → 117.315 → 117.0 | 5,021 → 5021.08 → 5021.0 | **all Rnd** |
| 005 | 1 | Waste disposal | 36.700 → 36.7 → 36.7 | 127 → 127.074 → 127.0 | 4,664 → 4663.62 → 4664.0 | qty exact · rate/net **Rnd** |
| 005 | 2 | Waste disposal | 17.200 → 17.2 → 17.2 | 165 → 165.465 → 165.0 | 2,846 → 2846.0 → 2846.0 | qty/net exact · rate **Rnd** |
| 005 | 3 | Recycling services | 8 → 8.0 → 8.0 | 180 → 180.009 → 180.0 | 1,440 → 1440.07 → 1440.0 | qty exact · rate/net **Rnd** |
| 006 | 1 | Recycling services - Organic | 41.9800 → 41.98 → 41.98 | 93.8210 → 93.821 → 93.821 | 3,938.6100 → 3938.61 → 3938.61 | **all exact** |
| 006 | 2 | Recycling services - Mixed | 91.6000 → 91.6 → 91.6 | 141.1340 → 141.134 → 141.134 | 12,927.8700 → 12927.87 → 12927.87 | **all exact** |
| 006 | 3 | Waste collection - Recycling | 41.4200 → 41.42 → 41.42 | 84.7370 → 84.737 → 84.737 | 3,509.8100 → 3509.81 → 3509.81 | **all exact** |
| 006 | 4 | Recycling services - Mixed | 94.7000 → 94.7 → 94.7 | 170.0980 → 170.098 → 170.098 | 16,108.2800 → 16108.28 → 16108.28 | **all exact** |

**Across 63 line-item fields: 34 exact agreement · 29 PDF display rounding · 0 extraction error ·
0 unknown.** The 34 exact fields decompose exactly as P12-IMPL-01 reported:
quantities 16 + rates 5 + line nets 13.

> **`002` also contains a conflicting quantity representation.** Its descriptions print
> `Qty: 112.0 ...`, `Qty: 25.8 t...`, `Qty: 63.5 tonnes`, `Qty: 47.6 tonnes` — higher-precision
> fragments that **contradict its own Qty column** (112 / 26 / 64 / 48) and are **truncated with
> `...`**. The extractor correctly used the Qty column. This is *ambiguous source document*
> (§12), not rounding.

**10. Document-Level Comparison**

| Doc | Field | PDF-visible | Oracle | Extracted | Class |
| --- | --- | --- | --- | --- | --- |
| 001 | subtotal | 27,674.48 | 27674.48 | £27,674.48 | exact |
| 001 | VAT | 5,534.89 | 5534.89 | £5,534.89 | exact |
| 001 | total | 33,209.37 | 33209.37 | £33,209.37 | exact |
| 002 | subtotal | 35,011 | 35011.09 | £35,011 | **Rnd** |
| 002 | VAT | 7,002 | 7002.22 | £7,002 | **Rnd** |
| 002 | total | 42,013 | 42013.31 | £42,013 | **Rnd** |
| 003 | subtotal | 11,628.76 | 11628.76 | £11,628.76 | exact |
| 003 | VAT | 2,325.76 | 2325.76 | £2,325.76 | exact |
| 003 | total | 13,954.52 | 13954.52 | £13,954.52 | exact |
| 004 | subtotal | 5,318 | 5318.44 | £5,318 | **Rnd** |
| 004 | VAT | 1,064 | 1063.69 | £1,064 | **Rnd** |
| 004 | total | 6,382 | 6382.13 | £6,382 | **Rnd** |
| 005 | subtotal (Net Total) | 8,949.690 | 8949.69 | £8,949.690 | exact |
| 005 | VAT (GST) | 1,789.930 | 1789.93 | £1,789.930 | exact |
| 005 | total (Net Payable) | 10,739.620 | 10739.62 | £10,739.620 | exact |
| 006 | subtotal | 36,484.5700 | 36484.57 | £36,484.5700 | exact |
| 006 | VAT | 7,296.9100 | 7296.91 | £7,296.9100 | exact |
| 006 | total | 43,781.4800 | 43781.48 | £43,781.4800 | exact |

String fields (supplier, customer, invoice ref, date, period start/end) are **36/36 exact**;
nothing was fabricated or altered. Money fields: **15 exact · 3 rounded (in `002` and `004`)** —
54 document-level comparisons in total: **48 exact · 6 PDF display rounding · 0 unexplained**.

**11. Arithmetic Verification**

**Line level (`quantity × rate` vs `line net`), independent calculation:**

| Basis | Consistent (|Δ| < 0.01) | Detail |
| --- | --- | --- |
| **Generator / oracle precision** | **21 / 21** | e.g. `4.6 × 64.643 = 297.3578 ≈ 297.36`; `25.8 × 189.996 = 4901.8968 ≈ 4901.90` |
| **PDF-visible rounded values** | **6 / 21** | only `001` L3, `005` L2 and all four `006` lines |

Worst PDF-visible deviations (display artefacts, not extraction errors):

| Doc/line | PDF `qty × rate` | PDF line net | Δ | oracle `qty × rate` | oracle net |
| --- | --- | --- | --- | --- | --- |
| `002` L3 | 64 × 99 = 6336.0 | 6,256 | **80.0** | 6256.147 | 6256.15 |
| `002` L4 | 48 × 81 = 3888.0 | 3,843 | **45.0** | 3842.5576 | 3842.56 |
| `002` L1 | 112 × 179 = 20048.0 | 20,010 | **38.0** | 20010.48 | 20010.48 |
| `002` L2 | 26 × 190 = 4940.0 | 4,902 | **38.0** | 4901.8968 | 4901.9 |
| `004` L1 | 5 × 65 = 325.0 | 297 | **28.0** | 297.3578 | 297.36 |
| `001` L1 | 90 × 107.64 = 9687.6 | 9,687.51 | 0.09 | 9687.51 | 9687.51 |

**Document level (Σ line nets vs subtotal; subtotal + VAT vs gross):**

| Doc | dp | Σ printed line nets | Printed subtotal | Δ | Σ = subtotal | sub+VAT = gross | oracle Σ = net | oracle net+VAT = gross |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | 2 | 27674.48 | 27,674.48 | 0.00 | yes | yes | yes | yes |
| 002 | 0 | 35011.00 | 35,011 | 0.00 | yes | yes | yes | yes |
| 003 | 2 | 11628.76 | 11,628.76 | 0.00 | yes | yes | yes | yes |
| 004 | 0 | 5318.00 | 5,318 | 0.00 | yes | yes | yes | yes |
| **005** | 3 | **8950.00** | **8,949.690** | **0.31** | **NO** | yes | yes | yes |
| 006 | 4 | 36484.57 | 36,484.5700 | 0.00 | yes | yes | yes | yes |

**Finding:** the *printed* document reproduces its own arithmetic in 5/6 documents at document
level and only 6/21 lines at line level; **generator precision reproduces it in 6/6 documents and
21/21 lines**. `005` is the clearest case: its line nets are printed at 0 dp while its total is
printed at 3 dp, so the printed lines sum to `8950.00` against a printed `Net Total` of
`8,949.690` — a **£0.31 internal inconsistency present in the document itself**, which vanishes
at generator precision (`4663.62 + 2846.00 + 1440.07 = 8949.69`).

**12. Discrepancy Classification**

| Classification | Count | Where | Evidence |
| --- | --- | --- | --- |
| exact agreement | **82** (34 line + 48 doc) | all six | extracted == oracle |
| PDF display rounding | **35** (29 line + 6 doc) | `001`×2 rates; `002` all 12; `003`×5 rates; `004` all 6; `005` 2 rates+2 nets; `002`/`004` doc totals | `render(oracle, dp) == printed == extracted`; printed strings in §6 |
| PDF display truncation | **0** | — | (the `002` description fragments are separately classified below) |
| generator/rendering precision loss | **0** | — | the renderer rounds for display only; the oracle keeps the unrounded value |
| extraction error | **0** | — | every extracted value equals the printed text (and its recorded `source_line`) |
| fixture/oracle error | **0** | — | the oracle is correct *as generator ground truth*; it is a different layer |
| arithmetic inconsistency (document-internal) | **1** | `005` Σ printed nets vs printed net total, Δ 0.31 | §11 |
| ambiguous source document | **1** | `002` descriptions print `Qty: 112.0 ...` / `Qty: 25.8 t...` / `Qty: 63.5 tonnes` / `Qty: 47.6 tonnes` while the Qty column prints 112/26/64/48, and the fragments are truncated | the document carries two conflicting quantity representations |
| unknown | **0** | — | nothing unexplained |

**13. Root-Cause Analysis**

**VERIFIED mechanism (generator source at the pinned commit):**

```text
generator/data_factory.py:372        "decimal_places": rng.choice([0, 2, 3, 4])
generator/reportlab_renderer.py:507  decimal_places = self._attr(v, doc_data, 'decimal_places', 2)
generator/reportlab_renderer.py:530  f = f"{val:,.0f}" if number_format == 'compact' else f"{val:,.{decimal_places}f}"
generator/reportlab_renderer.py:542  qty = f"{int(item.quantity):,}" if item.quantity.is_integer() else f"{item.quantity:,.{decimal_places}f}"
generator/reportlab_renderer.py:604  decimal_places = self._attr(v, doc_data, 'decimal_places', 2)
generator/reportlab_renderer.py:605  fmt = lambda val: f"{currency}{val:,.{decimal_places}f}"
```

1. `DataFactory._generate_variations()` picks each document's `decimal_places` from
   `{0, 2, 3, 4}` (seeded by `seed + 9999`) — display precision is a **document variation**, not
   a corpus-wide decision.
2. `create_document()` sets `variations = self._generate_variations(spec, seed)`, which
   **replaces** any precision the caller requested. This is why
   `tools/demo_lab/p12_canonical_corpus.py` passed `decimal_places=2` and the corpus still
   rendered at 0/2/3/4 dp.
3. The renderer formats every printed number at that precision (integer quantities printed bare),
   while `DocumentData` / the ground-truth sidecar keep the unrounded values.
4. Extraction reads the printed text faithfully, so
   `extracted == printed == render(oracle, decimal_places(document))` for **every** numeric field
   — proven for 117/117 comparisons.

**Conclusion:** no defect exists in the extractor, the renderer behaves exactly as designed, and
the oracle is correct as generator ground truth. The two layers answer different questions, and
the earlier acceptance contract conflated them.

**14. PDF Precision Characteristics**

* Display precision is **uniform within each document** across quantity, rate, line net, subtotal,
  VAT and gross — observed 0/2/3/4 dp for the six documents.
* Integer quantities print without decimals (`90`, `58`, `8`) even in 3–4 dp documents.
* The corpus therefore spans four precisions; **no single global precision describes it.**
* Labels vary (`Subtotal`/`Net Amount`/`Net Total`; `VAT`/`VAT (20%)`/`Tax (20%)`/`GST`;
  `Total`/`Total Due`/`Net Payable`) without changing the numeric precision within a document.
* `002` prints two conflicting quantity representations (description fragment vs column) and
  truncates the fragments with `...`; `005` carries a £0.31 internal total inconsistency (mixed
  column precision).

**15. Generator Precision Characteristics**

* Ground truth is full precision: rates carry 3 decimals (`107.639`, `178.665`, `64.643`),
  quantities 1–2 (`25.8`, `4.6`, `41.98`), line nets 2–4.
* It is **internally arithmetic-consistent 21/21 at line level and 6/6 at document level** — it is
  the invoice's intended arithmetic.
* Correct authority for **generation-level** validation ("what did the generator intend?"), and the
  wrong authority for "what does this PDF print?".

**16. Extraction Precision Characteristics**

* `det:pdf_table` extraction preserves the **printed** value exactly, including its precision
  (`36.700` → `36.7`, `41.9800` → `41.98`, `£107.64` → `107.64`), and records the raw printed
  string (`source_line`), the printed unit (`unit_raw`) and an `arithmetic_ok` flag.
* It performs **no** precision completion and no rounding — the fail-closed behaviour required by
  P12-DECISION-01 §19 ("never silently normalise").
* Result: **0 unexplained mismatches** against document fidelity; the only differences are digits
  the document does not contain.

**17. Acceptance Contract Options**

| Option | Means | Validates | Cannot validate | Effect on IMPL-01 | Effect on IMPL-02 | Effect on calculation | Effect on evidence | Effect on corpus regen | False-failure risk | Hidden-defect risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **A** PDF-visible authoritative | compare to printed values | document fidelity | generator intent; exact arithmetic (printed arithmetic fails 15/21 lines) | all 117 pass | unaffected | emissions drift from intent | displayed values only | oracle re-derived from renders | none | **HIGH** — misreads become undetectable |
| **B** Oracle authoritative | compare to full precision | generator fidelity; exact arithmetic | document fidelity (29 line fields impossible) | 35 false failures | evidence judged on invisible digits | validates generator, not document | provenance claims absent values | all docs must render at max precision | **HIGH** | low for arithmetic |
| **C** Split by question | extraction ↔ printed; generation/calculation ↔ generator | both | nothing material (needs a mechanism) | 117/117 reconcile | clean | each test declares its layer | three labelled layers | none for v1 | low | low |
| **D** Tolerance | `abs(extracted − oracle) ≤ tol` | nothing specific | which layer governs; rounding vs misread | tolerance must cover 9.4% to pass `004` | loosens evidence comparisons | silently accepts inconsistencies | tolerance is not provenance | none | low | **HIGH** (9.4% / £80 observed) |
| **E** Field-specific precision | compare exactly at the document's own precision | document fidelity precisely | nothing (it is C's mechanism) | 0 unexplained mismatches | gives IMPL-02 a precision context | tests declare their layer | precision becomes recorded provenance | none | low | low |

**18. Document Fidelity Contract**

A PDF extraction test asserts **what the document prints**:

* the extracted value must equal the printed value **exactly at that document's display
  precision**, derived from the document itself (e.g. from its printed total);
* the printed source string must be preserved (`source_line`, `unit_raw`, `date_raw`,
  `billing_period_raw`, `extraction_evidence`) so a reviewer can see the digits;
* a difference at a place the document **does** print is a **defect**, even by one minor unit;
* a difference at a place the document does **not** print is **not** an extraction defect.

**19. Generator Fidelity Contract**

A generator test asserts **what the generator intended**:

* compare the ground-truth sidecar against the generator's own rules at full precision
  (arithmetic consistency, requested precision, layout);
* it is a **corpus** test and never runs against extracted values;
* a failure there means the corpus/oracle is wrong, not the extraction.

**20. Calculation Fidelity Contract**

A calculation test must state its layer:

* **Document lane** — calculation from extracted printed numbers, demonstrating the product
  journey on the document as received. Results will differ from generator intent for
  sub-maximum-precision documents (up to 9.4% on one `004` line); that difference must be
  **declared**, never hidden.
* **Generator lane** — calculation seeded from ground-truth precision, validating the engine
  against intended values.
* Neither lane may assert the other's numbers; no calculation acceptance may mix bases.

**21. Recommended Precision Contract**

> **Contract C (split by question), implemented through E (per-document precision rules).**

Justification from the measured evidence:

1. **B is impossible** — 29 of 63 line fields physically cannot match full-precision oracle
   values because those digits are not printed; accepting B means permanently failing correct
   extraction (35 false failures).
2. **A is unsafe** — it discards the only internally consistent arithmetic (21/21 → 6/21 at line
   level) and removes the ability to detect a real misread, because a wrong value would have to
   equal a printed value the oracle no longer records.
3. **D is unsafe standalone** — the deviations are not a small epsilon: 28.0 on a 297.0 net
   (9.4%) and 80.0 on a 6256.0 net. Any tolerance wide enough to absorb `004` would also absorb
   genuinely wrong extractions.
4. **C + E fits the evidence exactly** — 117/117 field comparisons reconcile at the document's own
   precision with **zero** unexplained mismatches, while generator precision remains available as
   the only basis that satisfies the invoice arithmetic.
5. **Nothing needs regenerating and nothing needs hiding** — the extractor's behaviour is already
   correct under this contract.

**22. Field-Specific Precision Rules**

Measured facts (not invented requirements):

| Field | Observed PDF-visible precision | Rule |
| --- | --- | --- |
| quantity | integer rule (bare) or the document's dp (0/3/4 observed) | compare exactly at the document's dp; an integer has no fractional part to compare |
| rate / unit price | 0 / 2 / 3 / 4 dp = the document's dp | compare exactly at the document's dp |
| line net | same as rate | compare exactly at the document's dp |
| subtotal | same as rate | compare exactly at the document's dp |
| VAT / tax | same as rate | compare exactly at the document's dp |
| gross / total | same as rate | compare exactly at the document's dp |

Precision is **uniform within each document**, so **no field requires a rule different from its
document's own precision**; the only field-specific behaviour is the quantity integer rule, which
is a property of the document, not a new policy.

**23. Raw vs Normalized Value Policy**

Preserve all layers, distinctly labelled:

| Layer | Where it lives today | Status |
| --- | --- | --- |
| raw printed text | `line_items[].source_line`, `unit_raw`, `date_raw`, `billing_period_raw`, `extraction_evidence` | **already preserved** by P12-IMPL-01 |
| normalized numeric value | `line_items[].quantity/unit_price/net_amount` (floats at printed precision) | **already present** |
| display precision | **not recorded in the product payload** | **PROPOSED** — record the document's inferred display precision so a consumer can compare correctly |
| generator precision | oracle / ground-truth sidecar (outside the product) | exists; keep out of the product payload |
| provenance of the conversion | `extraction_method = det:pdf_table`, `arithmetic_ok`, `arithmetic_deviation` | **already present** |

**24. Oracle Policy**

`tools/demo_lab/p12_canonical_manifest.json` is **NOT changed**. Its values remain authoritative
for **generator-level** validation; for extraction acceptance they must be interpreted through
each document's display precision.

**Fields that conflict with document-visible values (recorded, not corrected):**

| Document | Conflicting oracle fields | Why they conflict | Still useful as generator ground truth? |
| --- | --- | --- | --- |
| `001` | L1 `unit_price` 107.639, L2 `unit_price` 190.222 | printed at 2 dp | **yes** |
| `002` | all 4 lines' `quantity`/`unit_price`/`net_amount`; `net_total` 35011.09; `vat_total` 7002.22; `gross_total` 42013.31 | printed at 0 dp | **yes** |
| `003` | all 5 `unit_price` values | printed at 2 dp | **yes** |
| `004` | both lines' `quantity`/`unit_price`/`net_amount`; all three document totals | printed at 0 dp | **yes** |
| `005` | 2 `unit_price`, 2 `net_amount` values; `net_total` 8949.69 vs printed `8,949.690` | printed at 0/3 dp | **yes** |
| `006` | none | 4 dp printing matches the oracle exactly | **yes** |

A **future oracle version** should additionally record each document's display precision (or
equivalent tolerance metadata) so extraction acceptance can be computed without re-deriving
precision from the PDF. That is a proposal; the current oracle must not be edited.

**25. Frozen v1 Policy**

**`p12-canonical-demo-v1` remains FROZEN.** It is a valid, hard, realistic regression set spanning
four display precisions and containing two genuine document-level ambiguities (the `002`
conflicting quantity representations and the `005` mixed-precision total). Those properties make it
*valuable* — an "easy" corpus would hide exactly these cases. Its hashes (§4) match
`corpus_provenance.json`, and nothing about it needs to change for the recommended contract.

**26. Potential v2 Corpus Policy**

**Not required by the evidence; recommended** for investor-facing clarity.

| Aspect | Detail |
| --- | --- |
| Why v2 would be considered | a demo document printing `Qty: 25.8 t...` beside a `26` column invites an "is this a bug?" question presenters should not have to answer live |
| What would change | request **uniform 4 dp** for all documents and ensure the description carries no second quantity representation; keep structure identical |
| What would NOT change | supplier (`Robinsons Recycling Services Ltd`), customer (`Sustainable Direct Group`), the two fiscal years, the layout family, the waste/recycling vocabulary, the one-supplier/one-customer multi-year shape |
| Versioning | new id `p12-canonical-demo-v2` in a **new** directory; `p12-canonical-demo-v1` stays intact as the regression corpus |
| Oracle for v2 | produced by the same pinned generator (`8ade2bf…`) via the same driver, with `decimal_places` **pinned** rather than taken from the variation picker (the driver must set it after `_generate_variations`, since `create_document()` replaces the caller's value) |
| Hashing | freeze PDF + sidecar SHA-256 into the v2 manifest/provenance exactly as v1 does |
| v1 availability | retained unchanged; both corpora can coexist under `corpus/` |

**v2 is explicitly NOT created in this task.**

**27. P12-IMPL-01 Reconciliation**

Every P12-IMPL-01 observation is **CONFIRMED**; the precision contract changes how the *numeric*
ones should be **reported**, not what was observed.

| P12-IMPL-01 observation | Confirmed? | Evidence |
| --- | --- | --- |
| 6/6 supplier extraction | **CONFIRMED** | 6/6 `exact agreement` (§10) |
| 6/6 customer extraction | **CONFIRMED** | 6/6 `exact agreement` |
| 6/6 invoice reference | **CONFIRMED** | 6/6 `exact agreement` |
| 6/6 invoice date | **CONFIRMED** | 6/6 `exact agreement` |
| 6/6 billing period | **CONFIRMED** | 6/6 `exact agreement` (start + end) |
| 21/21 line structure | **CONFIRMED** | 63 line-field comparisons over 21 lines; per-document counts exact |
| 21/21 units | **CONFIRMED** | not a numeric-precision field; 21/21 |
| 16/21 quantity exact | **CONFIRMED** (oracle basis) | 16 exact + 5 rounding |
| 5/21 rate exact | **CONFIRMED** (oracle basis) | 5 exact + 16 rounding |
| 13/21 line-net exact | **CONFIRMED** (oracle basis) | 13 exact + 8 rounding |
| 4/6 document-total exact | **CONFIRMED** (oracle basis) | 4 exact + 2 rounding |

**Metric restatement:**

| Metric | OLD | NEW | REASON |
| --- | --- | --- | --- |
| quantities | 16/21 | **document-exact 21/21** at each document's dp; oracle-exact 16/21 | 5 values differ only by the document's own display rounding |
| rates | 5/21 | **document-exact 21/21**; oracle-exact 5/21 | 16 rates printed with fewer decimals than the oracle |
| line nets | 13/21 | **document-exact 21/21**; oracle-exact 13/21 | 8 nets printed rounded |
| document totals | 4/6 | **document-exact 6/6**; oracle-exact 4/6 | `002`/`004` print 0-decimal totals |
| supplier / customer / ref / date / period | 6/6 each | unchanged 6/6 | no precision semantics |
| line structure / units / false positives | 21/21 / 21/21 / 0 | unchanged | no precision semantics |
| arithmetic consistency | *not measured* | **oracle 21/21 · printed 6/21** (line); **oracle 6/6 · printed 5/6** (document) | new measurement required by this contract |

No P12-IMPL-01 number was reinterpreted without the field-level evidence in §9–§11.

**28. Code-Change Decision**

> **Does P12-DATA-01 justify changing P12-IMPL-01 extraction code? — NO.**

| Test | Finding |
| --- | --- |
| Defect definition | an extraction defect = a value differing from **what the document prints** |
| Measured extraction defects | **0** across 117 field comparisons |
| Are the two anomalies extraction defects? | **No.** `002`'s conflicting quantity representations and `005`'s £0.31 total inconsistency are properties of the **document**; the extractor chose the Qty column (correct) and preserved printed values (correct) |
| Would any plausible code change improve fidelity? | No — the printed digits are already recovered exactly, including their precision |
| Would any change be manufacturing precision? | Yes — recovering `4.6` from a document that prints `5` would require reading the oracle, which P12-IMPL-01 §37 forbids |

**No code change is proposed; no code was changed in this task.**

**29. Future Implementation Impact**

| Consumer | Impact |
| --- | --- |
| Extraction acceptance harness | needs a **precision-aware comparator** (derive the document's dp, compare exactly at that precision, label each difference as oracle-exact vs display-rounding). Demo-lab tooling only — no product change |
| Product extraction payload | **optional** addition of the document's display precision (§23) so consumers need not re-derive it |
| P12-IMPL-02 (waste semantics) | substantively unaffected — it consumes printed descriptions and printed quantities; treat the *printed* value as the document-lane value |
| Calculation acceptance | must declare its lane per §20; `004` demonstrates a ≥9% lane divergence on one line |
| Evidence / provenance | unchanged mechanism; printed value + `source_line` is already correct provenance |
| Reporting / Insight | unaffected |

**30. Risks and Failure Modes**

| # | Risk | Mitigation |
| --- | --- | --- |
| R1 | A future agent "fixes" extraction to satisfy the oracle, manufacturing invisible precision | §21/§24 forbid it; the artifact records per-field proof |
| R2 | A blanket tolerance adopted, hiding real misreads | §17 D analysis; tolerance rejected standalone |
| R3 | Oracle edited to match printed values, destroying generator ground truth | §24: not changed; conflicts enumerated |
| R4 | Display precision re-derived incorrectly by a consumer | §23 proposal to record it; cross-checked across 117/117 comparisons |
| R5 | v1 replaced by a "cleaner" corpus, losing the two hard cases | §25 freeze policy; v2 must be additive |
| R6 | Calculation tests silently mixing lanes, producing unexplained emission differences | §20 requires each test to declare its lane |
| R7 | A future parser treats the `002` description fragments as the authoritative quantity | recorded as *ambiguous source document*; the Qty column is the correct source |

**31. Required Follow-Up Tasks**

| # | Task | Owner | Notes |
| --- | --- | --- | --- |
| 1 | **PO decision** on the recommended contract (C + E) | Product Owner | §21; this task recommends, does not decide |
| 2 | **PO decision** on the `002`/`005` document ambiguities and whether v2 is wanted | Product Owner | §26 |
| 3 | Make the acceptance harness precision-aware | implementation (demo-lab) | no product change |
| 4 | Record the document's display precision in the extraction payload | implementation (P12-IMPL-02 or small follow-on) | optional; §23 |
| 5 | Re-run the T3 edge corpus and diff payloads | implementation | carried from P12-IMPL-01 §22 |
| 6 | Locate or add the application read path for extraction items | implementation | carried from P12-IMPL-01 L5 |

**32. Final Acceptance**

```text
all six canonical PDFs inspected ............................ DONE (§5-§6)
all 21 line items compared .................................. DONE (§9: 63 field comparisons)
PDF-visible values recorded ................................. DONE (§6)
oracle/generator values recorded ............................ DONE (§7)
P12-IMPL-01 extracted values recorded ....................... DONE (§8, §10)
every numeric discrepancy classified ........................ DONE (82 exact / 35 rounding / 0 unexplained)
arithmetic independently checked ............................ DONE (line 21/21 vs 6/21; doc 6/6 vs 5/6)
PDF rounding/truncation behaviour documented ................ DONE (§13-§14)
extraction vs fixture/oracle differences distinguished ...... DONE (§12: 0 extraction errors)
document / generator / calculation fidelity defined ......... DONE (§18-§20)
precision contract options analysed ......................... DONE (A-E with trade-offs)
recommended contract documented ............................. DONE (C + E)
oracle policy documented .................................... DONE (unchanged; conflicts enumerated)
frozen v1 policy documented ................................. DONE (remains frozen)
future v2 policy documented ................................. DONE (not required; recommended)
P12-IMPL-01 metrics reconciled .............................. DONE (all confirmed; new framing)
explicit decision on extraction code changes ................ DONE (NO)
machine-readable JSON artifact created ...................... DONE
mandatory Markdown report created ........................... DONE (this file)
product code changed ........................................ NONE
database writes ............................................. NONE
canonical corpus changes .................................... NONE
oracle changes .............................................. NONE
production untouched ........................................ CONFIRMED
```

**Result: `DATA-CONTRACT-ISSUE` — resolved by contract, not by code.**
The extraction is correct (0 defects), the corpus and oracle are correct at their own layer, and
the previous acceptance statement was measuring the wrong layer. The recommended contract (C + E)
reconciles all 117 field comparisons without changing a single product behaviour, a single PDF, or
a single oracle value.

**Reproducibility (task §19)**

| Item | Value |
| --- | --- |
| Baseline commit | `ad07cd4` |
| Corpus | `p12-canonical-demo-v1` @ `$HOME/ct_local_env/demo_lab/corpus/p12-canonical-demo-v1/` (hashes §4) |
| Oracle | `tools/demo_lab/p12_canonical_manifest.json` SHA-256 `0c478b71…` |
| Generator | `8ade2bf778d518d59924905849ab114ab2d0820a` (read-only) |
| Command | `./backend/.venv/bin/python tools/demo_lab/p12_data_01_precision_analysis.py` |
| Analysis timestamp | recorded in the artifact (`analysis_timestamp`) |
| Database touched | **NO** (`database_touched: false`) |
| Product code modified | **NO** (`product_code_modified: false`) |

**STOP.** P12-IMPL-02 and Step 3 are not started. No extraction, calculation, supplier, waste,
reporting, schema, corpus or oracle change was made.