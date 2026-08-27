# CarbonTally — Evidence Traceability & Provenance Principles

**Status:** Ratified Product Principle  
**Purpose:** Permanent product/architecture reference  
**Origin:** D33 / D33.1 evidence-traceability work  
**Date:** 2026-08-23

---

## 1. Core Principle

CarbonTally is a carbon data processing and evidence infrastructure platform.

Every calculated emission should be explainable through a provenance chain connecting:

SOURCE EVIDENCE
→ EXTRACTION
→ MAPPING
→ EMISSION FACTOR
→ CALCULATION
→ EMISSION RESULT

The customer should not have to contact CarbonTally staff to understand where an emission value came from.

---

## 2. Customer Question

CarbonTally must be able to answer:

> "Where did this emission come from?"

The answer should provide, where available:

- source document
- invoice/reference number
- source page
- extracted source line
- original extracted quantity
- original extracted unit
- mapped activity
- emission factor
- factor source
- factor reporting year
- calculation inputs
- calculation result
- stable provenance identifiers

---

## 3. Original vs Derived Data

CarbonTally must clearly distinguish between:

### Original source data

Information extracted from the customer's source material.

Example:

`Electricity — 500 kWh`

### CarbonTally-derived data

Information created by CarbonTally's processing:

- normalized activity
- emission-factor selection
- mapping
- calculation
- CO2e result

The UI must never imply that a CarbonTally mapping or factor was present in the customer's original document.

---

## 4. Evidence Chain

The authoritative conceptual chain is:

Document
→ Extracted Item
→ Mapped Activity
→ Emission Factor
→ Calculation Snapshot
→ Emission Result

The chain should be navigable in both directions.

### Forward

Document
→ extracted lines
→ emissions

### Reverse

Emission
→ calculation
→ factor
→ extracted line
→ document

---

## 5. Database Visibility Principle

CarbonTally does NOT expose its database directly.

Customers must never receive:

- SQL access
- database credentials
- unrestricted table browsing
- service-role credentials
- internal secrets

Instead, CarbonTally provides an authorized:

**Evidence Record / Technical Provenance View**

This is a human-readable representation of the authoritative persisted records underlying an emission.

---

## 6. Stable Record Identifiers

Where appropriate, the Evidence Record may expose stable identifiers such as:

- organization_file_id
- manual_extraction_item_id
- calculation_snapshot_id
- emission_log_id
- emission_factor_id

These identifiers help advanced users, auditors, CarbonTally support, and integrations establish lineage.

---

## 7. Source Precision by Input Type

### PDF

Target provenance:

Document
→ Page
→ Extracted line/text
→ Emission

Coordinates/bounding boxes may be exposed only when reliably available.

### Excel

Target provenance:

Workbook
→ Sheet
→ Row
→ Cell/Range
→ Emission

### CSV

Target provenance:

File
→ Row
→ Column
→ Emission

### JSON

Target provenance:

File
→ JSONPath
→ Emission

### Manual extraction

Target provenance:

Source document
→ Page/line where available
→ Extraction item
→ Processor
→ Mapping
→ Factor
→ Calculation
→ QC/review
→ Emission

---

## 8. No Fabricated Evidence

CarbonTally must never invent:

- page numbers
- row numbers
- cells
- coordinates
- source text
- document relationships

If precise provenance does not exist, CarbonTally must say so.

Examples:

`Source document available; exact source location unavailable.`

`Extracted line available; page location unavailable.`

---

## 9. Evidence Completeness

Evidence should be classified as:

### COMPLETE

Sufficient source and processing provenance exists to reconstruct the result.

### PARTIAL

The source document and processing lineage exist, but some source-location precision is unavailable.

### UNAVAILABLE

Reliable source provenance cannot be established.

The status must be derived from actual persisted information.

---

## 10. Evidence UI

Customer-facing evidence should include:

- CO2e result
- quantity
- unit
- calculation
- activity
- factor
- factor source
- reporting year
- source document
- invoice/reference number
- source page if available
- source line if available
- evidence completeness
- source record identifiers
- source document viewer

---

## 11. Document Reverse Lookup

Customers should also be able to open a document and see:

> "What emissions were generated from this document?"

This establishes bidirectional evidence navigation.

---

## 12. Evidence Access Audit

Evidence access may be audited using:

- actor
- organization
- emission/calculation identifier
- source document identifier
- action
- timestamp

Never record secrets, signed URLs, credentials, or unnecessary document contents.

---

## 13. Export

Where available, exports should contain:

- snapshot_id
- source_item_id
- source_file
- source_page
- source_line/text
- source_sheet
- source_row
- source_column/cell/range
- source_json_path
- evidence_status

---

## 14. Product Positioning

CarbonTally should not position itself merely as a system that calculates carbon emissions.

Its stronger proposition is:

> CarbonTally turns messy source data into structured, calculated, traceable carbon data.

The evidence chain is part of the product's core value.

---

## 15. Customer Value

A customer should be able to answer:

> "Why is this number 0.140 kg CO2e?"

without requiring CarbonTally support.

The customer should be able to see:

`500 kWh`

then:

`Electricity`

then:

`DEFRA 2025 — 0.00028 kg CO2e/kWh`

then:

`500 × 0.00028 = 0.140 kg CO2e`

then:

`INV-10482.pdf — Page 2 — Electricity 500 kWh`

This is the intended CarbonTally evidence experience.

---

## 16. Architectural Constraint

Evidence traceability must reuse the existing CarbonTally architecture.

Do not introduce:

- a generic workspace/tenant abstraction
- a second calculation engine
- a second extraction engine
- a parallel provenance architecture

`organizations` remains the tenancy anchor.

Existing D15/D20/D21/D22/D27/D32/D33 authorization and security boundaries remain authoritative.

---

## 17. Future Enhancements

Potential future enhancements include:

- PDF visual line highlighting
- precise PDF bounding boxes
- Excel cell-level provenance
- richer evidence packages
- signed evidence exports
- advanced auditor workflows

These are enhancements, not reasons to compromise the core provenance principle.

---

## 18. Final Product Principle

> **Every CarbonTally emission should be explainable.**

A customer should be able to move from:

**Emission → Calculation → Factor → Extracted Data → Source Evidence**

and understand exactly how CarbonTally arrived at the number.

CarbonTally does not expose its database.

CarbonTally exposes the **authorized evidence record representing the authoritative data behind the result**.