# CarbonTally Assisted and Managed Processing Specification V1

**Filename:** `CARBONTALLY_ASSISTED_AND_MANAGED_PROCESSING_SPECIFICATION_V1.md`  
**Status:** Product/commercial decision draft  
**Date:** 2026-08-23  
**Implementation status:** Specification only — no implementation authorized by this document

---

## Executive Summary

CarbonTally should not be positioned as a system that only succeeds when automated document extraction succeeds.

The core promise should be:

> **Give CarbonTally your carbon-related data. CarbonTally determines the appropriate processing route and gets it to a structured, mapped, calculated and evidence-traceable result.**

Customers have different preferences. Some want to operate the platform themselves. Some want CarbonTally to handle only difficult documents. Others simply want to upload documents and receive completed results.

Therefore V1 should support three customer operating modes:

1. **Self-Service Processing** — customer/team operates the workflow.
2. **Assisted Processing** — CarbonTally automatically processes what it can and offers human processing for documents requiring additional work.
3. **Managed Processing** — customer submits a batch and CarbonTally manages the workflow, including automated processing, human escalation, mapping, validation/QC and completion.

All routes converge on the same data model:

```text
Source Document
      ↓
Extraction
      ↓
Structured Source Line
      ↓
Mapping
      ↓
Emission Factor
      ↓
Calculation
      ↓
Emission Result
      ↓
Evidence / Provenance
```

Extraction method should be preserved, such as `AUTOMATED`, `OCR`, `AI`, `HUMAN`, or `CUSTOMER_ENTERED`.

---

# 1. Product Principle

## 1.1 The outcome, not the extraction technology, is the product

CarbonTally should not promise:

> "Our AI can process every document."

Instead:

> **"CarbonTally gives your documents a path to completion."**

If automated extraction works, use it.

If confidence is insufficient, route to review.

If human processing is appropriate, offer it.

If the customer prefers to do the work themselves, allow customer entry/review.

If the customer wants no operational involvement, Managed Processing takes responsibility for the workflow.

---

# 2. Customer Operating Modes

## 2.1 Self-Service

Customer wants to operate CarbonTally themselves.

They can:

- upload documents/data
- initiate processing
- review extraction
- correct data
- confirm mappings
- resolve issues
- review evidence
- export results.

This is primarily a software/platform experience.

## 2.2 Assisted Processing

Customer wants CarbonTally to handle difficult parts.

Typical flow:

```text
Upload
  ↓
Automatic processing
  ↓
Successful → continue
  ↓
Uncertain/failed → identify documents requiring attention
  ↓
Customer chooses:
    • review themselves
    • request CarbonTally Assisted Processing
  ↓
Human processing
  ↓
QC
  ↓
Mapping / calculation / evidence
```

## 2.3 Managed Processing

Customer says:

> "I don't want to operate the workflow. I'll provide the documents; CarbonTally manages the rest."

Typical flow:

```text
Upload batch
  ↓
Submit for Managed Processing
  ↓
CarbonTally intake analysis
  ↓
Automatic processing where suitable
  ↓
Human escalation where required
  ↓
Mapping
  ↓
Validation / QC
  ↓
Issue handling
  ↓
Completion
  ↓
Customer receives results
```

The customer does not need to classify documents, assign processors, monitor individual extraction tasks or coordinate Processing Entities.

---

# 3. Processing Routes

CarbonTally may use:

| Route | Meaning |
|---|---|
| Automated | Automated extraction/processing |
| OCR | OCR-supported processing |
| AI | AI-assisted extraction |
| Human | CarbonTally/authorized Processing Entity staff |
| Customer-entered | Customer enters or corrects source data |

The customer-facing product should emphasize the result. The evidence record should preserve the actual extraction method.

---

# 4. Processing Decision Logic

Conceptually:

```text
Document received
       ↓
Intake analysis
       ↓
Can reliably process automatically?
       ├── YES → automated processing
       │
       └── NO
            ↓
      Can customer review?
       ├── YES → customer review option
       │
       └── NO / customer requests help
                 ↓
          Assisted/Managed human processing
```

Exact confidence thresholds and routing algorithms require technical definition before implementation.

---

# 5. Document Complexity Classification

Use four categories:

1. **Simple**
2. **Standard**
3. **Complex**
4. **Exceptional**

Classification should use multiple characteristics, not page count alone.

### Simple

Typical:

- clean digital PDF/high-quality image
- standard invoice/document
- roughly 1–2 pages
- straightforward tables
- readable quantities/units
- limited line items
- predictable fields
- little ambiguity

**Commercial baseline:** approximately **$0.99/document** for human-assisted extraction.

### Standard

Typical:

- several pages
- multiple tables
- moderate formatting variation
- moderate line-item count
- mixed data types
- some normalization
- minor ambiguity

**Commercial baseline:** approximately **$1.99/document**.

### Complex

Typical:

- many pages
- complicated tables
- poor scans
- unusual layouts
- difficult units/supplier information
- ambiguous values
- substantial human interpretation

**Commercial baseline:** **from $3.99/document**.

### Exceptional

Examples:

- handwritten
- severely damaged/unreadable
- unusual document types
- extremely large documents
- highly ambiguous information
- information requiring customer clarification
- work outside normal scope

**Commercial treatment:** assessment/quote.

---

# 6. Who Determines Complexity?

The customer should not have to guess.

Recommended hierarchy:

1. CarbonTally automated intake classification
2. Human processor review if classification is uncertain
3. CarbonTally service rules determine commercial category

The customer sees the resulting category and price/estimate.

---

# 7. Fixed vs Estimated Pricing

| Category | Treatment |
|---|---|
| Simple | Fixed |
| Standard | Fixed |
| Complex | Starting price / estimate |
| Exceptional | Quote/assessment |

The customer should see the applicable price or estimate before committing to paid human processing, except under an existing enterprise/managed contract.

---

# 8. Customer Approval

For Assisted Processing, show:

- documents requiring assistance
- document count
- complexity
- price/estimate
- expected service/SLA
- inclusions
- rework/refund terms

Example:

> **75 documents require CarbonTally Assisted Processing**  
> Estimated service: **$149.25**  
> `[Approve Processing] [Select Documents] [I'll Process Them Myself]`

For Managed Processing, approval can be at batch/service level.

---

# 9. Customer-Entered Fallback

Always provide a self-processing path where practical.

If CarbonTally cannot reliably extract:

> **Processing requires attention**

Options:

- Try Again
- Process with CarbonTally
- Enter Data Myself
- Contact Support

Customer-entered data must still enter the normal mapping, calculation and evidence architecture.

---

# 10. Automated Processing Credits

Subscriptions may include processing credits/units.

Example:

**Professional — $149/month → 500 processing credits**

Credits should primarily represent resource-consuming automated processing.

Generally do **not** charge credits for:

- login
- dashboard viewing
- evidence viewing
- document viewing
- team management
- normal report viewing
- normal exports
- evidence traceability itself

Exact credit-consuming operations must be finalized before billing implementation.

---

# 11. Human Processing and Credits

Human processing should be commercially separate from ordinary automated credits.

```text
Automated Processing
    → subscription/processing credits

Human Assisted Processing
    → separate service purchase

Managed Processing
    → service/batch/contract pricing
```

A customer should not lose automated credits merely because CarbonTally determined that human intervention was necessary, unless a combined managed-service package explicitly says otherwise.

---

# 12. Managed Processing Commercial Model

Possible models:

- per document
- per batch
- recurring managed-service allowance
- enterprise/custom contract

For large customers, batch or contractual pricing is likely more suitable than a simple per-document price.

The final Managed Processing price is intentionally not fixed by this specification.

---

# 13. Managed Batch Intake

For example:

```text
1,000 documents received

742 → automatic processing
183 → customer review
52  → human-assisted processing
23  → exceptional / assessment required
```

Assisted customers can choose what to approve.

Managed customers can have CarbonTally handle routing according to the agreed service.

---

# 14. Batch Creation

A processing batch should conceptually contain:

- customer organization
- source documents
- processing mode
- requested service
- intake status
- processing status
- complexity
- automated/manual route
- Processing Entity
- assigned processor
- QC status
- issue status
- completion status
- commercial status
- evidence/provenance references

Reuse existing CarbonTally workflow architecture rather than building a parallel processing system.

---

# 15. Processing Entity Assignment

Human work may be assigned to:

- CarbonTally internal staff
- CarbonTally (BD) Limited initially
- authorized external Processing Entities later

Customer interacts with CarbonTally as service provider.

Internally record:

- entity
- processor/staff
- assignment time
- completion time
- QC result
- rework history

---

# 16. Processing Entity Compensation

Processor payout is an internal CarbonTally commercial arrangement.

Possible models:

- per document
- per complexity class
- per batch
- per accepted line
- hourly/contractual
- SLA-based

Customer price and processor payout should not be assumed to be identical.

Final payout should come from the unit-economics/service-cost model.

---

# 17. Quality Control

Human extraction should normally require QC:

```text
Human extraction
      ↓
QC
      ↓
PASS → continue
FAIL → rework → QC
```

QC should check, as applicable:

- required fields
- extraction accuracy
- units
- supplier/document reference
- line completeness
- mapping readiness
- evidence linkage
- acceptable error threshold

---

# 18. Rework Policy

If CarbonTally/Processing Entity made the error:

> **Customer does not pay again for correction.**

If customer changes source information after extraction or requests new scope:

> Rework may be billable according to service terms.

The system should distinguish:

- CarbonTally error
- customer correction
- new scope
- ambiguous source
- additional requested work

---

# 19. SLA

Assisted/Managed services should eventually have explicit SLAs.

Possible levels:

- Simple
- Standard
- Complex
- Exceptional
- Large Managed batch

Exact hours/days should be finalized from actual operational capacity.

Record, where supported:

- submitted_at
- accepted_at
- assigned_at
- processing_started_at
- completed_at
- QC_completed_at
- delivered_at

---

# 20. Cancellation and Refunds

Recommended principles:

- before work starts: cancellation subject to terms
- after human work begins: refund depends on work performed
- CarbonTally error: correction without additional charge
- unprocessable source: reassessment, fallback or appropriate unused-service refund
- enterprise contracts may override generic rules

Exact monetary policy must be finalized before public launch.

---

# 21. Evidence and Provenance

Every route must converge on:

```text
Source document
      ↓
Extracted source line
      ↓
Mapping
      ↓
Emission factor
      ↓
Calculation
      ↓
Emission result
```

Evidence should preserve:

- source document/file ID
- extracted item/line
- source location where reliably available
- extraction method
- mapping/factor
- calculation
- emission result
- stable technical IDs
- completeness status

Human processing must not create a weaker evidence chain.

---

# 22. Evidence Completeness

Continue the existing D33/D33.1 principle:

**COMPLETE** — reliable document + line + calculation + factor + required source location where available.

**PARTIAL** — valid provenance chain but source-location precision unavailable.

**UNAVAILABLE** — no reliable provenance relationship.

Never fabricate a page, row, cell or other location.

---

# 23. Extraction Method Transparency

Evidence may state:

> Extraction method: Human

or:

> Extraction method: Automated

or:

> Extraction method: Customer entered

This gives transparency without forcing customers to understand internal architecture.

---

# 24. Complete Automated Failure

Never silently fail.

Customer-facing status:

> **Processing requires attention**

Self-Service:
- customer reviews/enters data

Assisted:
- customer requests human processing

Managed:
- CarbonTally routes it automatically under the service agreement

The document remains in the same workflow.

---

# 25. Customer Notifications

Important events should generate notifications:

- batch received
- intake analysis complete
- processing started
- assistance required
- price approval required
- human processing started
- processing complete
- QC failed/rework
- batch completed
- exceptional document requires assessment

Do not expose unnecessary sensitive document content in notifications.

---

# 26. Customer Dashboard

Show batch status:

```text
1,000 documents

742 completed
183 under review
52 human processing
23 require attention
```

Also show:

- automated usage/credits
- human-processing approval status
- managed batch progress
- outstanding customer actions
- estimated/approved service charges

---

# 27. Large Batch Processing

Recommended flow:

```text
Upload
  ↓
Intake
  ↓
Classification
  ↓
Price/service estimate
  ↓
Customer approval
  ↓
Processing
```

Enterprise contracts may govern approval thresholds.

---

# 28. Managed Processing as a Product

Potential positioning:

> **CarbonTally Managed Processing**  
> Upload your carbon documents. CarbonTally manages extraction, mapping, validation, human processing and evidence-ready results for you.

This is especially valuable for organizations without internal data-processing capacity.

---

# 29. Customer Segments

| Customer | Recommended mode |
|---|---|
| Small company | Self-Service |
| Technical sustainability team | Self-Service |
| Finance team | Assisted |
| Consultant | Self-Service + Assisted |
| Large organization | Assisted + Managed |
| High-volume document customer | Managed |
| Carbon-reporting platform | API/Managed/B2B |
| Internal data team | Self-Service |
| No data-processing capacity | Managed |

---

# 30. Commercial Baseline

Current provisional market-value baseline:

| Service | Baseline |
|---|---:|
| Starter | $49/month |
| Professional | $149/month |
| Business | $399/month |
| Enterprise | from $999/month |
| Consultant | $299/month |
| Consultant Business | $699/month |
| Simple human extraction | ~$0.99/document |
| Standard human extraction | ~$1.99/document |
| Complex human extraction | from ~$3.99/document |
| Exceptional | quote |
| Managed Processing | batch/service/contract based |

These are hypotheses, not final prices.

---

# 31. Credit Rollover

Current decision:

> **Customers should not lose paid processing value simply because a billing period ended.**

Unused credits should roll over.

Exact ledger/accounting rules are still to be finalized.

---

# 32. Emergency Processing Allowance

Current decision:

If a customer exhausts purchased processing credits while completing an active job, CarbonTally should avoid leaving the job stranded.

Proposed principle:

> **CarbonTally may provide a temporary processing allowance of up to approximately 10% of the relevant purchased allocation to complete an active job.**

Treat this as an advance rather than unconditional free credits.

At the next payment/top-up, reconcile the applicable advance.

This requires anti-abuse controls and precise ledger implementation before production.

---

# 33. Customer Trust Principle

Avoid:

> "You have run out of credits. Come back after paying."

Prefer:

> "Your current processing allowance has been exhausted. We have temporarily extended processing to help complete your active job. Additional usage will be reconciled with your next purchase."

Goal:

**continuity + transparency + trust.**

---

# 34. Free vs Paid

Generally included:

- dashboard
- evidence viewing
- document viewing
- team management according to plan
- normal exports
- standard validation
- evidence traceability
- processing history

Metered:

- defined automated processing operations

Separately purchased:

- human-assisted extraction
- exceptional processing
- managed processing beyond plan/service allowance

---

# 35. Billing Provider Requirements

The eventual provider should support/integrate with:

- recurring subscriptions
- one-time purchases
- upgrades/downgrades
- customer portal
- webhooks
- refunds
- failed payments
- international customers
- UK merchant
- VAT/tax handling
- recurring plans
- credit/package purchases
- manual-service purchases
- enterprise/custom invoicing where possible

CarbonTally remains authoritative for:

- processing entitlements
- credit balance
- credit transactions
- processing consumption
- human-processing orders
- service status
- evidence

---

# 36. CarbonTally Internal Credit Ledger

CarbonTally should maintain an auditable ledger.

Example:

| Event | Credits | Balance |
|---|---:|---:|
| Subscription allowance | +500 | 500 |
| Rollover | +200 | 700 |
| Automated processing | -12 | 688 |
| Automated processing | -8 | 680 |
| Emergency allowance | +50 | 730 |
| Emergency reconciliation | -50 | 680 |

Every debit should reference a CarbonTally operation/job where practical.

This is an entitlement ledger, not a replacement for the external payment provider.

---

# 37. Human Processing Order

Conceptually contain:

- organization
- source documents
- processing mode
- complexity
- customer-approved price
- service status
- Processing Entity
- processor
- QC status
- rework count
- evidence links
- delivery status
- billing reference

---

# 38. No Duplicate Processing System

Do not create a disconnected "Human Processing System."

Human processing should be another route through:

**document → item → mapping → calculation → evidence**

---

# 39. Future Automation

The same customer-facing Managed Processing service can survive improving automation.

Example:

```text
Today:   80% automated / 20% human
Later:   90% automated / 10% human
Future:  95% automated / 5% human
```

The customer buys the outcome, not the automation percentage.

---

# 40. Core Product Decision

> **"You choose how much work you want to do. CarbonTally handles the rest."**

This is stronger than selling AI extraction as the product.

---

# 41. Decisions for Product Owner

Approve/revise:

1. Self-Service / Assisted / Managed
2. Human processing separate from automated credits
3. Customer-entered fallback
4. Automatic complexity classification
5. Simple/Standard/Complex/Exceptional
6. Fixed Simple/Standard pricing
7. Estimated/starting Complex pricing
8. Exceptional quote
9. QC for human processing
10. CarbonTally error = free rework
11. New customer scope = potentially billable
12. Managed Processing as a formal service
13. Credit rollover
14. Emergency allowance principle
15. Internal credit ledger
16. External provider handles payment/subscription lifecycle
17. Existing evidence/provenance applies to every route

---

# 42. Intentionally Not Finalized

This document does not finalize:

- exact credit definition
- credits included in each plan
- final human extraction prices
- Managed Processing price
- exact complexity algorithm
- SLA values
- processor payout rates
- exact refund schedule
- emergency allowance accounting
- final billing provider
- tax/legal wording
- enterprise terms

These follow after commercial pricing and billing-platform research.

---

# 43. Recommended Customer-Facing Language

**Self-Service**

> Process your data yourself with CarbonTally's data-processing workspace.

**Assisted**

> Let CarbonTally handle documents that need additional processing.

**Managed**

> Just upload your documents. CarbonTally manages extraction, mapping, validation and evidence-ready results for you.

**Core promise**

> **From messy documents to structured, traceable carbon data — with CarbonTally doing as much or as little of the work as you want.**

---

# 44. Final Recommendation

Approve the three-mode operating model before selecting the billing provider.

Recommended commercial architecture:

```text
Subscription
    +
Automated processing allowance
    +
Optional human-assisted processing
    +
Managed processing
    +
Enterprise/API services
```

This serves both:

> **"I want software."**

and:

> **"I want the result; please do the work."**

That distinction is central to CarbonTally's data-management and processing-company positioning.

---

# 45. Decision Sequence

1. Approve/revise this specification.
2. Finalize service catalogue.
3. Finalize baseline pricing architecture.
4. Define exact credit unit.
5. Define human-processing commercial rules.
6. Define Managed Processing packages.
7. Compare Paddle vs Lemon Squeezy vs Stripe against the approved model.
8. Select billing/subscription provider.
9. Define billing integration architecture.
10. Authorize implementation.

---

**END OF SPECIFICATION**
