CarbonTally v3 — Consolidated Report: What Was Wrong

Scope: Two real invoice PDFs (border_double_fuel.pdf, scan_extreme_gen.pdf) failed to extract, map, and calculate emissions in the CarbonTally v3 UI. This report consolidates the root‑cause audit and the subsequent verification pass against the real PDFs and a 144‑file corpus.

Bottom line: The failures are not caused by OCR, missing pages, or downstream calculation bugs. They are caused by two deterministic parser defects that block nearly every invoice in the corpus, plus three latent defects in mapping, supplier resolution, and the disabled P1 shaper that would cause silent errors if enabled.
1. Executive Summary
Area	Verdict
PDF extraction	❌ Broken. The table parser rejects Item … headers and ISO currency codes (GBP, EUR, USD). Only 12 of 144 corpus invoices (8.3%) produce any line item.
Mapping to DEFRA	⚠️ Partial. Physical units (litres, kWh) map correctly, but line‑item documents receive no per‑line factor candidates, the interactive path ignores the invoice date for vintage selection, and spend‑based factors (kgCO₂e per £) do not exist.
Currency handling	✅ Supported (parser‑side). Currency is never treated as a unit. No FX conversion exists (out of scope).
Supplier extraction & mapping	⚠️ Partial. Names extract for clean text‑layer invoices, but the resolution engine is unwired, address fields are never populated, and no UI affordance exists to add a supplier.
End‑to‑end pipeline	⚠️ Partial. The worker auto‑advances past extraction and calculation is server‑side, but both target PDFs die at the completeness gate (0.33 and 0.00, below 0.50). The P1 shaper is disabled and contains a confirmed quantity bug.

Verified against real PDFs: All quantitative claims about the fuel PDF are confirmed. The scanned services PDF is worse than originally reconstructed — it yields no supplier, completeness 0.00, and is not even classified multi‑line.
2. The Two Failing Invoices
2.1 border_double_fuel.pdf — Fuel invoice from Pure Resources Group

    Header: Item Quantity Unit Price Amount

    Rows:

        Diesel supply - Premium 2,200 litres GBP1.40 GBP3,071.20

        Diesel delivery - REF-65245 1,500 litres GBP1.31 GBP1,965.00

        Diesel supply - Ultra Low Sulfur 3,400 litres GBP1.61 GBP5,491.00

    Supplier address: 40 Eco Drive, Edinburgh, ML24 4EV, UK

    Invoice date: 04/10/2025 → DEFRA 2025 vintage

2.2 scan_extreme_gen.pdf — Services invoice from Bright Energy Group

    Header (OCR): ItemQuantityUnit PriceAmount (squashed)

    Rows (OCR): 600units29.2417545.80, General services-REF-642121,000 units 7.597,592.00, etc.

    Supplier address: 242 Green Lane, Birmingham, CP29 8BV, UK

    Invoice date: 08/08/2025 → DEFRA 2025 vintage

    Unit: units (not a physical unit; requires spend‑based factor)

3. Root Causes — Extraction
3.1 RC‑1: Table header regex rejects Item … headers

    File: backend/engines/invoice_extraction.py:213 (_TABLE_HEADER_RE)

    Problem: Anchored on the literal word description. The PDF prints Item Quantity Unit Price Amount.

    Impact: extract_invoice_lines() returns [] before examining any row.

    Verified: _TABLE_HEADER_RE.match("Item Quantity Unit Price Amount") → False. Corpus: 0 of 46 parser‑compatible headers start with Item. 98 of 144 corpus files are blocked at this step alone.

3.2 RC‑2: Row regex rejects ISO currency codes

    File: backend/engines/invoice_extraction.py:218 (_ROW_RE)

    Problem: Currency class is [£$€]? — only symbols. The PDF prints GBP1.40, GBP3,071.20.

    Impact: Even if RC‑1 were fixed, all three rows would still fail.

    Verified: _ROW_RE.match('…2,200 litres GBP1.40 GBP3,071.20') → False. Corpus: 25 of 34 row‑failures contain ISO codes.

3.3 RC‑3: units is not a known unit in the table parser

    File: backend/engines/invoice_extraction.py:241‑261 (_KNOWN_UNITS_PARSER)

    Problem: The services invoice uses unit units; canonical_unit("units") returns None, so rows are dropped.

    Impact: 8 of 34 corpus row‑failures. multi_gen extracted only 2 of 5 lines for this reason.

    Verified: canonical_unit("units") → None in both the table parser and the P1 shaper vocabularies.

3.4 RC‑4: Squashed OCR text is not normalised

    Problem: Scanned invoices produce cells like 600units29.2417545.80. _ROW_RE requires whitespace between every column.

    Impact: The entire scan_extreme_gen.pdf family yields 0 rows, 0 candidate lines, and is not classified multi‑line.

3.5 RC‑5: Space‑separated thousands cause silently wrong quantities

    File: backend/engines/invoice_extraction.py:218,247

    Problem: (?P<qty>\d[\d,]*(?:\.\d+)?) does not accept spaces. A row like 2 200 litres is parsed as quantity = 200.0 (the leading 2 becomes part of the description).

    Impact: Not exercised by the two target PDFs (they use 2,200), but reproducible in code. Silent under‑reporting of emissions.

4. Root Causes — Mapping & Calculation
4.1 RC‑6: mapping_options ignores line_items[]

    File: backend/api/v3_processing_workflow.py:1228

    Problem: Reads only top‑level extracted_data.activity and extracted_data.unit. When a document has line items, those top‑level keys are deliberately unset.

    Impact: Even a correctly parsed multi‑line invoice returns factors: []. The UI has no per‑line candidates to offer.

4.2 RC‑7: Interactive mapping ignores the invoice date for factor vintage

    Files: v3_processing_workflow.py:1234, v3_operations.py:1043,1654

    Problem: No year= parameter is passed. The factor store falls back to ORDER BY reporting_year DESC, selecting the newest vintage rather than the invoice’s year (2025).

    Impact: An invoice dated 2025 could map to a 2026 factor if a newer batch exists.

4.3 RC‑8: No spend‑based factor path for services

    Problem: The DEFRA/SEAI factor sets are physical‑unit based. There is no kgCO₂e per £ factor for units‑style services rows.

    Impact: The services invoice has no factor to map to, even after extraction is fixed. The UI returns a neutral “no matching factor” message, not spend‑specific guidance.

4.4 RC‑9: No FX/currency conversion

    Problem: No currency conversion exists anywhere in the backend. Spend‑based mapping would require it.

    Status: Out of scope until a spend factor source exists.

4.5 RC‑10: Calculation is correctly gated but unreachable

    File: backend/api/v3_processing_workflow.py:887

    Problem: calculate_item requires quantity, unit, and emission_factor_used. All three are missing.

    Impact: calculated_emissions_kg_co2e remains null. This is honest and correct — there is nothing to calculate.

5. Root Causes — Supplier
5.1 RC‑11: Supplier address is extracted but discarded

    File: backend/engines/invoice_extraction.py:164 (extract_supplier_header)

    Problem: Returns only the supplier name. The address block is used for scoring evidence and then discarded.

    Impact: supplier_address_line1, supplier_city, supplier_postcode, supplier_country are never populated.

5.2 RC‑12: Supplier resolution engine is implemented but unreachable

    File: backend/engines/supplier_resolution.py

    Problem: The full matching engine (normalisation, scoring, VAT/postcode signals) exists and is unit‑tested, but is not imported by any production caller and is not exported in engines/__init__.py.

    Impact: mapped_supplier_id is never derived. The supplier provenance chain is broken.

5.3 RC‑13: No UI to add a supplier from the workspace

    Problem: Supplier creation exists only in the admin tab. The extraction/mapping workspace offers no “Add supplier” affordance.

    Impact: Even if a name were extracted, the user cannot link or create it from the processing screen.

5.4 RC‑14: Address columns exist in the DB but are unused

    Problem: The schema has address_line1, address_line2, city, county, postcode, country (see init_schema.sql:500), but _SUPPLIER_COLUMNS and SuppliersRepository.create omit them.

    Impact: Even a correctly parsed address could not be stored. No migration is needed to fix this.

6. The P1 Shaper — A Latent, Dangerous Bug
6.1 P1 is disabled by default

    File: backend/services/extraction_fidelity.py:106 (shape_mode)

    Status: shadow mode; allowlist empty. Line items are only emitted when explicitly enabled per organisation.

6.2 P1 contains a confirmed quantity bug

    File: backend/services/extraction_fidelity.py:73,239,325

    Problem: _NUMBER has no end anchor, so REF-65245 matches 652. _quantity_column compares units by exact equality ("tonnes" != "tonne"), so it falls back to the first number in the line.

    Impact: For the real fuel PDF, Diesel delivery - REF-65245 1,500 litres … yields quantity: 652.0 instead of 1500.0. If P1 were enabled, the invoice would pass the completeness gate with completeness 1.0 while silently under‑reporting a fuel quantity by 2.3×.

    Second symptom: _NUMBER also truncates amounts: GBP1,965.00 → 965.00.

6.3 P1 cannot see units rows

    File: backend/services/extraction_fidelity.py:61,211

    Problem: _UNIT_TOKENS does not include units.

    Impact: The services invoice yields 0 candidate lines and cannot be shaped even if enabled.

7. Corpus‑Wide Impact (144 PDFs)

A sweep of the *_fuel.pdf and *_gen.pdf families (72 each) produced:
Outcome	Count	Share
≥1 line item extracted	12	8.3%
Header‑blocked (RC‑1)	98	68.1%
Row‑blocked (RC‑2/RC‑3)	34	23.6%
of which ISO currency (RC‑2)	25	—
of which units vocabulary (RC‑3)	8	—

Conclusion: The Item‑header and ISO‑currency defects — not the P1 shaper — are the dominant, currently‑shipping cause of zero‑line extractions.
8. What the Verification Against Real PDFs Changed
Finding	Audit prediction	Reality (real PDF)
Fuel PDF: rows, completeness, gate	0 rows, 0.33, blocked	Confirmed exactly.
Services PDF: supplier	Bright Energy Group	None — OCR de‑spaces to BrightEnergyGroup, single token scores 0.
Services PDF: completeness	0.3333	0.00 — activity also unresolved.
Services PDF: multi‑line suspect	Yes	No — candidate_lines: 0.
P1 REF-65245 bug	Predicted on reconstructed row	Confirmed on real PDF (652.0 vs 1500.0).
units vocabulary gap	Attributed to P1 only	Also in the deterministic table parser (8 of 34 row‑failures).
_NUMBER amount truncation	Not reported	New finding: GBP1,965.00 → 965.00.
Currency grep	“0 hits”	7 vendored hits in .venv/.../pip/_vendor/rich/live.py; 0 in application code.

Bottom line: The two example PDFs fail exactly as the audit described, but the services PDF is worse than reconstructed, and the units/_NUMBER defects broaden the fix scope.
9. What Works (Do Not Break)

    Supplier‑name detection for clean text‑layer invoices (Pure Resources Group).

    Invoice‑number and date extraction (INV-20279073, 2025-10-04).

    Day‑first date normalisation to ISO.

    The confidence gate itself (0.33 → truthful MANUAL_REVIEW with unresolved‑field list).

    Currency‑is‑not‑a‑unit in the table parser (canonical_unit("GBP") → None).

    Year‑keyed factor store; worker derives vintage from the invoice date.

    Spend dead‑end messaging (no_factors_reason, spend_mapping_suggestion).

    Server‑side calculation gated on quantity/unit/factor.

    Per‑line calculation and summation (once factors exist).

    P1 rollout safety design (fail‑safe shadow, allowlist‑gated).

    91 relevant unit tests pass (but none cover the failing real‑world forms).

10. Recommended Fix Order (Dependency‑Aware)

    FIX‑1 (P0) — Parser header + currency + units vocabulary.

        Update _TABLE_HEADER_RE to accept Item/Description variants.

        Update _ROW_RE to accept ISO codes (GBP|EUR|USD) and space‑thousands.

        Add units to _KNOWN_UNITS_PARSER.

        Add de‑squash normalisation for OCR text.

        Unblocks 123 of 144 corpus files.

    FIX‑4 (P0) — P1 quantity bug + amount truncation.

        Anchor _NUMBER with a proper end boundary and exclude REF‑, INV‑, etc.

        Fix _quantity_column to compare canonical units, not raw tokens.

        Required before any P1 promotion. Without it, enabling P1 trades a visible block for a silent 2.3× error.

    FIX‑2 (P1) — Mapping.

        Pass year= from the invoice date on all interactive mapping endpoints.

        Make mapping_options line‑item‑aware.

        Add loaded flag to the UI to distinguish “not fetched” from “empty”.

        PO decision required: spend‑based factor path (implement or declare out of scope).

    FIX‑3 (P1) — Supplier.

        Emit structured address fields from extract_supplier_header.

        Wire engines/supplier_resolution.py into the mapping/workspace payload.

        Add address columns to _SUPPLIER_COLUMNS, SuppliersRepository.create, and SupplierCreate.

        Add an “Add supplier” affordance in the workspace, pre‑filled from extracted data.

    Verification harness.

        Add a corpus sweep test over the 144‑file family as an acceptance criterion.

        Add regression tests for the real header/currency/squashed/REF‑/units forms.