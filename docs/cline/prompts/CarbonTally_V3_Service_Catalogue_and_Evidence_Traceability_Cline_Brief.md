# CarbonTally V3 --- Complete Service Catalogue & Evidence Traceability

## Cline Implementation / Product-Architecture Audit Brief

### Version 1.0 --- 2026-08-23

------------------------------------------------------------------------

# 1. Purpose

This document is the authoritative product-service brief for the next
CarbonTally V3 work.

CarbonTally is not being positioned merely as another generic
carbon-accounting dashboard.

The core product proposition is:

> **CarbonTally turns messy business data and documents into traceable,
> calculation-ready carbon data.**

The platform must support the complete chain:

``` text
MESSY BUSINESS DATA / DOCUMENTS
        ↓
INGEST
        ↓
EXTRACT
        ↓
NORMALIZE
        ↓
MAP
        ↓
VALIDATE
        ↓
CALCULATE
        ↓
STORE EVIDENCE
        ↓
REPORT
```

A critical product requirement is:

> **Every emission result must be traceable back to the exact source
> activity data and, where applicable, the exact source document/invoice
> that produced it.**

This document therefore has two purposes:

1.  Define the complete CarbonTally service catalogue.
2.  Require Cline to audit the repository and implement/fix the
    end-to-end evidence/traceability chain where it is incomplete.

Do not invent a second tenancy/workspace architecture. `organizations`
remains the data-tenancy anchor.

Preserve D15, D20, D21, D22, D23, D27, D29, D30 and D31 security and
authorization decisions.

------------------------------------------------------------------------

# 2. Current product actors

CarbonTally currently supports:

-   Direct CarbonTally Customers
-   Consultant Firms
-   Consultant-managed Client Organisations
-   CarbonTally Internal Staff
-   Processing Entities
-   Processing Entity Staff

Commercially:

``` text
Direct Customer
    ↓
CarbonTally

Consultant
    ↓
CarbonTally
    ↓
Consultant-managed Client Organisations

Processing Entity
    ↓
Receives assigned extraction work from CarbonTally
    ↓
Never directly contacts Customers or Consultants
```

The Processing Entity communication rule is absolute:

``` text
Customer ↔ CarbonTally ↔ Processing Entity

NOT:

Customer ↔ Processing Entity

NOT:

Consultant ↔ Processing Entity
```

Clarifications discovered by Processing Entities must be mediated
through CarbonTally.

------------------------------------------------------------------------

# 3. Complete CarbonTally service catalogue

Cline must use this catalogue as the product capability taxonomy.

Each service must be classified during the audit as:

-   IMPLEMENTED
-   PARTIALLY IMPLEMENTED
-   NOT IMPLEMENTED
-   EXTERNAL CONFIGURATION
-   FUTURE / ROADMAP
-   NOT SUPPORTED BY CURRENT DATA MODEL

Do not claim a service is implemented merely because a related table,
endpoint, or placeholder exists.

------------------------------------------------------------------------

## SERVICE FAMILY 1 --- Data Ingestion

### 1.1 Excel ingestion

Supported customer data:

-   `.xlsx`
-   `.xls`

Capabilities:

-   upload
-   inspect workbook
-   identify sheets
-   identify headers
-   normalize rows
-   map fields
-   validate
-   calculate emissions

### 1.2 CSV ingestion

Capabilities:

-   upload
-   delimiter handling
-   header detection
-   field mapping
-   validation
-   factor matching
-   calculation

### 1.3 JSON ingestion

Capabilities:

-   structured upload
-   schema interpretation
-   field mapping
-   validation
-   calculation

### 1.4 PDF ingestion

Capabilities:

-   invoice upload
-   utility bill upload
-   supplier document upload
-   multi-page document handling
-   document storage
-   extraction

### 1.5 Image ingestion

Capabilities:

-   JPG/JPEG
-   PNG
-   scanned documents
-   OCR/extraction pipeline

### 1.6 Bulk ingestion

Capabilities:

-   multiple documents
-   batch processing
-   queueing
-   status tracking
-   processing history

------------------------------------------------------------------------

# SERVICE FAMILY 2 --- Automated Document Extraction

### 2.1 OCR/document extraction

Extract, where present:

-   supplier
-   invoice number
-   invoice date
-   billing period
-   account number
-   meter/reference number
-   activity
-   quantity
-   unit
-   currency
-   financial amount
-   location
-   other relevant activity attributes

### 2.2 Multi-line extraction

A single invoice may contain:

``` text
Electricity — 500 kWh
Natural Gas — 800 kWh
Water — 120 m³
Waste — 2.5 tonnes
```

Each activity line must remain individually traceable to the source
document and invoice.

### 2.3 Difficult document handling

Audit support for:

-   scanned documents
-   rotated pages
-   noisy documents
-   blurred documents
-   multi-page documents
-   tables
-   irregular layouts

------------------------------------------------------------------------

# SERVICE FAMILY 3 --- Human-Assisted Extraction

CarbonTally provides managed extraction through:

-   CarbonTally internal staff
-   authorized Processing Entities

Processing assignment must remain entity-scoped.

Processing Entity staff may process only work assigned to their entity.

They must not receive broad customer-organisation access.

Human extraction must preserve:

-   source document
-   extraction batch
-   extraction item
-   extracted values
-   processor identity
-   timestamps
-   changes/revisions
-   review/QC state

------------------------------------------------------------------------

# SERVICE FAMILY 4 --- Data Normalization

Normalize:

-   units
-   dates
-   supplier names
-   activity descriptions
-   currencies where applicable
-   structured fields

Examples:

``` text
British Gas
British Gas Ltd
British Gas Trading
```

may be normalized to a canonical supplier identity where the matching
rules support it.

Examples:

``` text
Natural Gas
Gas Consumption
Gas
```

may be normalized toward a canonical activity classification.

Do not silently change customer data without preserving provenance.

------------------------------------------------------------------------

# SERVICE FAMILY 5 --- Emission-Factor Mapping

### 5.1 Automatic factor matching

Map activity data to appropriate emission factors.

### 5.2 Candidate factor selection

Where ambiguity exists, expose candidate factors and preserve the
selected factor.

### 5.3 Factor-set support

The platform must support the factor sets actually loaded into the
CarbonTally database, including the existing DEFRA and SEAI data.

### 5.4 Factor provenance

Every calculation must retain enough information to identify:

-   factor
-   factor source
-   factor year
-   factor set
-   unit
-   scope
-   multiplier/methodology

The factor must be linked to the calculation, not merely looked up
transiently.

------------------------------------------------------------------------

# SERVICE FAMILY 6 --- Emissions Calculation

The calculation chain is:

``` text
Activity quantity
        +
Selected emission factor
        ↓
CarbonTally calculation engine
        ↓
CO₂e result
```

Support applicable:

-   Scope 1
-   Scope 2
-   Scope 3

Calculations must preserve their inputs and provenance.

A calculated result must never become an orphan numeric value with no
explanation of how it was produced.

------------------------------------------------------------------------

# SERVICE FAMILY 7 --- Validation, Review and QC

### Automated validation

Detect, where applicable:

-   missing quantity
-   invalid unit
-   missing invoice date
-   invalid activity
-   missing factor
-   factor mismatch
-   unit mismatch
-   suspicious values
-   duplicate documents
-   duplicate invoices
-   incomplete extraction
-   mapping issues

### Human review

Questionable records can enter review.

### QC

CarbonTally staff can approve/reject processing output.

### Issues

Problems must remain linked to the underlying work item and source
context.

------------------------------------------------------------------------

# SERVICE FAMILY 8 --- Evidence & Auditability

## THIS IS A CORE CARBONTALLY REQUIREMENT

CarbonTally must support an evidence chain like:

``` text
Emission Result
     ↓
Calculation
     ↓
Activity Record
     ↓
Mapped Activity
     ↓
Extracted Quantity
     ↓
Invoice / Source Document
     ↓
Original File
     ↓
Page / Line / Evidence Location where available
```

For example:

``` text
1,250 kg CO₂e
    ↓
Calculation ID
    ↓
Activity: Electricity
    ↓
Quantity: 4,500 kWh
    ↓
Factor: DEFRA 2025 electricity
    ↓
Invoice: INV-12345
    ↓
Supplier: Example Energy Ltd
    ↓
Original PDF
    ↓
Page 2
```

## 8.1 Mandatory traceability requirement

Cline must determine whether the current implementation actually
provides this chain.

The audit must answer:

1.  Can an emission result identify its calculation record?
2.  Can the calculation identify the exact activity/input record?
3.  Can the activity/input identify the extraction item or source data
    row?
4.  Can the extraction item identify the extraction batch?
5.  Can the extraction batch identify the original customer
    document/upload?
6.  Can the original document identify the exact source file?
7.  Can the system identify invoice number?
8.  Can the system identify source page?
9.  Can the system identify source line/table/cell when available?
10. Can the system identify the emission factor used?
11. Can the system identify factor source/year/set?
12. Can the system identify who extracted the data?
13. Can the system identify who reviewed/QC-approved it?
14. Can the system reconstruct the calculation after the fact?
15. Can an authorised customer/staff user navigate from an emission
    result to the source evidence?

## 8.2 Traceability must work in both directions

Forward:

``` text
Source Document
    ↓
Extraction
    ↓
Mapping
    ↓
Calculation
    ↓
Emission
```

Backward:

``` text
Emission
    ↓
Calculation
    ↓
Activity
    ↓
Extraction
    ↓
Source Document
    ↓
Original Evidence
```

Both directions are required.

## 8.3 Exact-document requirement

Where an emission is derived from an uploaded invoice/PDF/image:

> The system must be able to identify the exact source document from
> which the activity was extracted.

Do not rely only on:

-   supplier name
-   invoice number
-   filename
-   timestamp

if a stable database relationship can be maintained.

The underlying relational lineage must be authoritative.

## 8.4 Multi-line invoice requirement

If one invoice produces five activity lines:

``` text
Invoice PDF
 ├── Line 1 → Activity → Calculation → Emission
 ├── Line 2 → Activity → Calculation → Emission
 ├── Line 3 → Activity → Calculation → Emission
 ├── Line 4 → Activity → Calculation → Emission
 └── Line 5 → Activity → Calculation → Emission
```

Every line must remain linked to the same source document while
retaining its own activity/calculation lineage.

## 8.5 Evidence location

If the extraction technology provides:

-   page number
-   bounding box
-   table row
-   cell
-   OCR coordinates
-   source text

preserve it.

Do not fabricate evidence locations where the extraction engine does not
provide them.

------------------------------------------------------------------------

# SERVICE FAMILY 9 --- Document & Evidence Storage

CarbonTally provides storage for:

-   original uploaded documents
-   PDFs
-   images
-   extracted records
-   mapped records
-   calculation history
-   reports
-   audit history

Storage is part of evidence management, not merely generic file storage.

A document should remain associated with the organisation and its
processing history.

------------------------------------------------------------------------

# SERVICE FAMILY 10 --- Reporting & Analytics

### Customer

-   total emissions
-   emissions by scope
-   monthly trend
-   processing status
-   document status
-   mapped/unmapped
-   completion percentage
-   open issues
-   needs-attention items
-   member activity

### Consultant

-   portfolio health
-   client status
-   per-client processing
-   stage breakdown
-   emissions
-   issues
-   reports

### Internal Operations

-   platform overview
-   queue status
-   queue aging
-   SLA
-   processing stages
-   failed/rejected
-   review/QC
-   entity performance

### Reviewer

-   workload
-   aging
-   SLA
-   issues generated

### QC

-   QC approval/rejection
-   quality
-   processor/entity performance

### CarbonTally Admin

-   platform overview
-   audit reporting
-   operational metrics
-   authentication/event reporting where supported by external
    infrastructure

### Processing Entity

-   assigned work
-   completion
-   SLA
-   quality indicators

------------------------------------------------------------------------

# SERVICE FAMILY 11 --- Collaboration & Messaging

### Customer ↔ Consultant

Supported where the commercial relationship allows it.

### CarbonTally ↔ Customer

Platform notifications and customer communication.

### Processing Entity ↔ CarbonTally

Processing clarification workflow.

### Processing Entity ↔ Customer

PROHIBITED.

### Processing Entity ↔ Consultant

PROHIBITED.

Messages generated by CarbonTally for consultant-managed clients may use
the authorised consultant brand context where the commercial mode
permits it.

------------------------------------------------------------------------

# SERVICE FAMILY 12 --- White-Label Platform

CarbonTally supports consultant branding.

Modes:

### Mode A --- Managed Service

Consultant uses CarbonTally behind the scenes.

Client does not need CarbonTally access.

### Mode B --- Co-branded

Consultant + CarbonTally branding.

### Mode C --- White-label

CarbonTally technology presented under consultant branding.

Capabilities include, where implemented:

-   consultant brand
-   logo
-   colours
-   custom domain
-   sender configuration
-   branded reports/PDFs
-   branded platform presentation

Custom domain/email infrastructure remains subject to external
DNS/provider configuration.

CarbonTally should not assume responsibility for operating the
consultant's own domain/email infrastructure.

------------------------------------------------------------------------

# SERVICE FAMILY 13 --- Customer Onboarding & Data Discovery

Customer onboarding includes:

-   account creation
-   organisation creation
-   membership
-   customer verification
-   existing-data discovery

If a new customer application discovers existing CarbonTally data
belonging to that customer:

The customer is the ultimate owner of its data and decides whether to:

``` text
USE ALL
USE PART
DISCARD
```

Discard means:

> Do not adopt/use the discovered data.

It does not automatically mean destructive deletion of historical
records.

If the customer becomes a Direct CarbonTally Customer:

-   they initiate the process like any other customer
-   existing organisation identity may be adopted in place
-   historical provenance must remain intact
-   consultant access ends according to the approved lifecycle rules

------------------------------------------------------------------------

# SERVICE FAMILY 14 --- Data Portability

### Export

Potential/exported capabilities:

-   activity data
-   emissions
-   mappings
-   reports
-   documents
-   provenance
-   audit information

### Import

Customer-owned historical data import is a separate capability.

Do not confuse customer data import with the normal D19 direct-customer
transition.

------------------------------------------------------------------------

# SERVICE FAMILY 15 --- API & External Integrations

Current/future interfaces may include:

-   REST API
-   structured JSON
-   CSV
-   Excel
-   bulk ingestion

Future integrations may include accounting/ERP/data platforms.

Do not build speculative integrations during this task.

------------------------------------------------------------------------

# SERVICE FAMILY 16 --- Commercial / Billing

Billing is a separate commercial layer.

Initial direction:

-   Stripe or similar billing provider
-   CarbonTally subscription
-   processing credits / usage entitlement
-   consultant commercial plans
-   free/trial capability where appropriate

CarbonTally should not implement its own payment gateway.

Billing/entitlement implementation is separate from evidence
traceability.

------------------------------------------------------------------------

# 17. CLINE TASK --- TRACEABILITY AUDIT FIRST

Before modifying code, perform a read-only audit of the current
implementation.

Inspect:

-   database schema
-   migrations
-   `emissions_logs`
-   `calculation_snapshots`
-   activity/input tables
-   manual extraction tables
-   upload/document tables
-   organization files
-   report tables
-   audit trail
-   repositories
-   calculation engine
-   factor matching engine
-   extraction pipeline
-   mapping pipeline
-   validation pipeline
-   reporting APIs
-   report generation
-   PDF rendering
-   frontend evidence/report surfaces
-   RLS policies
-   API authorization
-   existing tests

Trace an actual path:

``` text
Customer upload
→ document
→ upload batch
→ manual extraction batch/item
→ extracted data
→ mapped data
→ validation
→ calculation
→ emissions_logs
→ report
```

Also trace structured CSV/Excel input if it follows a different path.

------------------------------------------------------------------------

# 18. REQUIRED AUDIT OUTPUT

Create:

``` text
docs/audit/cline/CARBONTALLY_V3_EVIDENCE_TRACEABILITY_AUDIT.md
```

The document must contain:

## A. Current architecture

Show the real lineage currently implemented.

## B. Traceability matrix

  --------------------------------------------------------------------------
  Stage          Current        Source link    Destination    Status
                 table/object                  link           
  -------------- -------------- -------------- -------------- --------------
  Source         ...            ...            ...            ...
  document                                                    

  Upload         ...            ...            ...            ...

  Extraction     ...            ...            ...            ...
  batch                                                       

  Extraction     ...            ...            ...            ...
  item                                                        

  Activity       ...            ...            ...            ...

  Mapping        ...            ...            ...            ...

  Factor         ...            ...            ...            ...

  Calculation    ...            ...            ...            ...

  Emission       ...            ...            ...            ...
  result                                                      

  Report         ...            ...            ...            ...
  --------------------------------------------------------------------------

Use actual repository evidence.

## C. Gap classification

Every gap must be classified:

-   P0 --- blocks trustworthy emission evidence
-   P1 --- important production traceability gap
-   P2 --- useful improvement
-   P3 --- future enhancement

## D. Required implementation plan

For every P0/P1 gap specify:

-   schema impact
-   migration required
-   backend changes
-   repository changes
-   API changes
-   RLS implications
-   frontend changes
-   test requirements
-   migration safety
-   backward compatibility

------------------------------------------------------------------------

# 19. IMPLEMENTATION RULE

After the audit:

### If complete

Do not modify the architecture unnecessarily.

Add tests proving end-to-end lineage.

### If incomplete

Implement the minimum architecture required to make the lineage
authoritative.

Do NOT create:

-   generic `workspace`
-   generic tenant abstraction
-   duplicate provenance systems
-   parallel assignment systems
-   unnecessary new storage architecture

Prefer existing CarbonTally relationships.

------------------------------------------------------------------------

# 20. Evidence UI requirement

The user must eventually be able to perform something equivalent to:

``` text
Reports
   ↓
Emission Result
   ↓
View calculation
   ↓
View activity
   ↓
View source document
   ↓
Open original PDF/image
   ↓
View relevant page/evidence
```

The UI should show, where available:

-   document name
-   invoice number
-   supplier
-   invoice date
-   billing period
-   activity
-   quantity
-   unit
-   emission factor
-   factor source
-   factor year
-   scope
-   calculation
-   resulting CO₂e
-   extraction provenance
-   processor/reviewer/QC information

Do not expose sensitive internal information to customers unless
authorized.

Processing Entity staff must never gain access to unrelated customer
data.

------------------------------------------------------------------------

# 21. Security requirements

Traceability must respect all existing authorization decisions.

### Customer

Can trace only its own organisation's data.

### Consultant

Can trace only currently ACTIVE granted client organisations.

Ended/suspended access must not expose customer evidence.

### Internal CarbonTally staff

Access according to existing staff permissions.

### Processing Entity

Can trace only documents/work assigned to its own Processing Entity.

It must never gain broad organisation access.

### Direct entity/customer communication

Never introduce it.

------------------------------------------------------------------------

# 22. Required tests

At minimum add tests proving:

### T1 --- Basic lineage

Source document → emission.

### T2 --- Reverse lineage

Emission → exact source document.

### T3 --- Multi-line invoice

Each emission line points to the same invoice while retaining
independent activity/calculation lineage.

### T4 --- Multiple documents

Two invoices from the same supplier produce separate traceable
emissions.

### T5 --- Structured data

CSV/Excel-originated emissions remain traceable to the source
dataset/row.

### T6 --- Factor provenance

Calculation identifies factor/source/year/set.

### T7 --- Consultant isolation

Consultant can trace only ACTIVE granted clients.

### T8 --- Ended grant

Consultant cannot trace ended client's evidence.

### T9 --- Processing Entity isolation

Entity A cannot trace Entity B's documents.

### T10 --- Customer isolation

Customer A cannot trace Customer B's documents.

### T11 --- Audit history

Extraction/review/QC changes preserve provenance.

### T12 --- Report traceability

Report emission values can navigate to their evidence.

### T13 --- Missing evidence

System fails safely/clearly when legacy data has no source document.

### T14 --- Backward compatibility

Existing emissions without complete provenance are not silently
destroyed.

------------------------------------------------------------------------

# 23. Synthetic corpus compatibility

The existing synthetic-document generator provides document-level ground
truth.

Do not regenerate or modify the existing synthetic corpus during this
task.

Do not start the 5,787-document workload.

The corpus should eventually be used as a benchmark because it provides:

-   invoice numbers
-   supplier information
-   activity lines
-   quantities
-   units
-   billing periods
-   ground-truth JSON
-   consultant/client hierarchy

For this task, use only a small controlled fixture if necessary.

------------------------------------------------------------------------

# 24. Product-service audit

In addition to traceability, produce a second table in the audit:

  Service                Status   Evidence   Gap   Priority
  ---------------------- -------- ---------- ----- ----------
  Excel ingestion                                  
  CSV ingestion                                    
  JSON ingestion                                   
  PDF ingestion                                    
  Image ingestion                                  
  Bulk ingestion                                   
  Automated extraction                             
  Human extraction                                 
  Normalization                                    
  Factor matching                                  
  Calculation                                      
  Validation                                       
  QC                                               
  Evidence management                              
  Document storage                                 
  Reporting                                        
  Messaging                                        
  White-label                                      
  Customer onboarding                              
  Data discovery                                   
  Export                                           
  Import                                           
  API                                              
  Billing foundation                               

Use actual implementation evidence, not assumptions.

------------------------------------------------------------------------

# 25. Documentation requirements

Update the authoritative architecture documentation only after
implementation is verified.

Clearly distinguish:

-   IMPLEMENTED
-   PARTIALLY IMPLEMENTED
-   EXTERNAL CONFIGURATION REQUIRED
-   FUTURE
-   NOT SUPPORTED

Never write "implemented" merely because a route exists.

For every implementation, record:

-   files changed
-   migration
-   API
-   RLS
-   frontend
-   tests
-   verification
-   known limitations

------------------------------------------------------------------------

# 26. Testing and environment safety

Do NOT run destructive integration tests against the main application
database.

The dedicated `carbontally_test` database must remain the
integration-test target.

Do not truncate the main CarbonTally development/demo database.

Do not delete:

-   synthetic corpus
-   demo users
-   demo organisations
-   existing legitimate data

Do not modify the separate synthetic-document-generator repository.

------------------------------------------------------------------------

# 27. Completion criteria

The task is complete only when:

1.  Complete service catalogue has been audited against the real code.
2.  Evidence traceability audit is documented.
3.  All P0/P1 traceability gaps are implemented or explicitly shown to
    require a business decision.
4.  Every supported document-derived emission has authoritative
    source-document lineage.
5.  Every supported calculation has factor provenance.
6.  Reverse navigation from emission → source evidence is available
    through an authorized API/UI path.
7.  Customer/consultant/entity isolation is tested.
8.  Existing D15/D20/D21/D22/D27 security boundaries remain intact.
9.  Backend tests pass.
10. Frontend tests/build pass.
11. Dedicated RLS integration tests pass without touching the main DB.
12. Evidence UI is visually verified.
13. Documentation accurately records implemented vs future capabilities.
14. No synthetic 5,787-document processing run is performed.

------------------------------------------------------------------------

# 28. Final Cline report

Return a formal report containing:

## Executive summary

## Complete service catalogue status

## Evidence traceability architecture

## Exact gaps found

## Exact files changed

## Schema/migrations

## API changes

## RLS changes

## Frontend/UI changes

## Tests

## Verification results

## Security verification

## Screenshot evidence

## Remaining limitations

## Recommended next product milestone

HARD STOP after the report.

Do not start unrelated billing, synthetic-corpus processing, or
speculative integrations unless explicitly instructed.
