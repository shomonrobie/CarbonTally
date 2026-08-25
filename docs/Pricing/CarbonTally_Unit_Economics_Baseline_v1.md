# CarbonTally Unit Economics Baseline v1

**Status:** Internal planning baseline  
**Version:** 1.0  
**Date:** 2026-08-23

## Purpose

Establish a first-pass cost and capacity model for CarbonTally before finalizing commercial pricing, packaging, subscription design, or payment/billing provider selection.

> **Important:** This is a planning model, not accounting data or a production cost statement. Estimates may be materially wrong. The purpose is to establish a quantitative baseline that can later be replaced with measured CarbonTally costs.

## 1. Executive conclusion

CarbonTally's early fixed technology cost is expected to be relatively small compared with the variable cost of delivering processing services.

The most important expected cost drivers are:

1. Human/manual data extraction
2. Quality-control labour
3. AI/OCR processing
4. Processing compute
5. Customer support and operations
6. Payment processing
7. UK company overhead
8. Infrastructure scaling

The commercial direction to investigate is:

**Platform access + processing usage + separately priced manual extraction**, with enterprise/API arrangements potentially priced separately.

No final prices are approved by this document.

## 2. Business and organizational assumptions

Initial commercial entity: **CarbonTally (UK) Limited**

Initial manual-processing operation: **CarbonTally (BD) Limited**

Future possibilities include additional Processing Entities and, if commercially/regulatorily justified, CarbonTally (IE) Limited or CarbonTally (EU) Limited.

CarbonTally is primarily being developed as a **carbon data management and processing platform/service**, rather than a conventional end-to-end carbon-reporting consultancy.

Core services under consideration:

- CSV, Excel and JSON ingestion
- PDF/image ingestion
- automated extraction
- manual extraction
- normalization and mapping
- emission-factor matching
- emissions calculation
- validation
- evidence/provenance traceability
- source-document retention
- emissions-to-source reverse lookup
- reports/exports
- workflow management
- consultant/client collaboration
- Processing Entity workflow
- API/integration capability
- white-label capabilities
- customer data/evidence storage

### Direct customers

One organization can have multiple team members.

### Consultants

A consultant/consulting firm can manage multiple separate client organizations. Clients remain owners of their organizations/data.

### Processing Entities

Processing Entities receive assigned work. They do not own the customer organization or customer data.

## 3. Cost model

Separate:

### Fixed operating cost

- Vercel
- Supabase
- Render
- Resend
- domains/DNS
- monitoring
- accounting/legal/insurance
- software
- management overhead

### Variable cost of revenue

- manual extraction
- QC
- AI
- OCR
- processing compute
- storage/egress
- transactional email
- payment fees
- Processing Entity payments
- customer-support allocation

Core equations:

**Revenue − Cost of Revenue = Gross Profit**

**Gross Profit − Fixed Operating Costs = Operating Profit**

## 4. Initial technology baseline

Published vendor pricing was reviewed on 2026-08-23. Prices can change and must be rechecked before launch.

| Cost | Monthly planning amount |
|---|---:|
| Vercel | $20 |
| Supabase | $25 |
| Render | $125 |
| Resend | $20 |
| Domains/DNS | $20 |
| Monitoring | $20 |
| Miscellaneous | $25 |
| **Initial technology baseline** | **$255/month** |

Notes:

- Vercel: planning assumption based on Pro.
- Supabase: planning assumption based on Pro.
- Render: $25 workspace plus an initial estimated service/compute allowance.
- Resend: planning assumption based on Pro.
- Domains, monitoring and miscellaneous are internal allowances, not vendor quotations.

This excludes salaries, AI/OCR, manual processing, QC, payment fees, accounting, legal, tax, insurance, and other corporate costs.

### Reference vendor pages

- Vercel: https://vercel.com/pricing
- Supabase: https://supabase.com/pricing
- Render: https://render.com/pricing
- Resend: https://resend.com/pricing

## 5. Supabase capacity assumptions

Current published Pro allowances are large enough that authentication, basic storage and Realtime are not expected to be the first early bottleneck.

Relevant published allowances include approximately:

- 100,000 MAU
- 8 GB database disk
- 100 GB file storage
- 250 GB uncached egress
- 250 GB cached egress
- 5 million Realtime messages/month
- 500 peak Realtime connections

Source: https://supabase.com/pricing

Storage illustrations at 1 MB/document:

| Documents | Approx. storage |
|---:|---:|
| 10,000 | 10 GB |
| 50,000 | 50 GB |
| 100,000 | 100 GB |
| 500,000 | 500 GB |
| 1,000,000 | 1 TB |

Actual document size and database growth must be measured.

## 6. AI baseline

Actual cost depends on provider, model, tokens, image processing, calls and retries.

Initial planning allowance:

**$0.030/document**

Sensitivity:

- 70%: $0.021
- 100%: $0.030
- 130%: $0.039

Preferred processing hierarchy:

**Native text/data extraction → OCR when necessary → AI extraction when necessary → human extraction when necessary.**

This is intended to minimize unnecessary AI spend.

## 7. OCR baseline

Initial planning allowance:

**$0.020/document**

Sensitivity:

- 70%: $0.014
- 100%: $0.020
- 130%: $0.026

Not every document requires OCR.

## 8. Human extraction baseline

Founder-provided planning assumption:

**$600/person/month fully loaded**

This should ultimately cover compensation plus reasonable overhead such as workspace, internet/electricity, equipment, supervision, leave/absence and operations.

Initial productivity scenarios:

| Productivity | Docs/hour | Docs/month at 160 productive hours | Labour cost/doc |
|---|---:|---:|---:|
| Efficient | 30 | 4,800 | $0.125 |
| Baseline | 20 | 3,200 | $0.188 |
| Conservative | 10 | 1,600 | $0.375 |

These are planning assumptions only.

## 9. Manual extraction complexity

A single universal document price is likely unsafe.

Investigate:

- **Simple:** 1–2 pages, clear document, limited lines
- **Standard:** multiple pages/moderate complexity
- **Complex:** many pages, poor scans, complicated tables
- **Exception:** unusual/missing/ambiguous data requiring investigation

Actual processing time should eventually determine cost.

## 10. QC baseline

Initial planning allowance:

**$0.030/document**

Sensitivity:

- 70%: $0.021
- 100%: $0.030
- 130%: $0.039

Actual QC productivity, sampling percentage and rework rate must replace this estimate.

## 11. Compute/storage/other variable baseline

| Driver | Baseline/document | 70% | 130% |
|---|---:|---:|---:|
| Compute | $0.020 | $0.014 | $0.026 |
| Storage/egress | $0.010 | $0.007 | $0.013 |
| Other variable allocation | $0.010 | $0.007 | $0.013 |

The other-variable allowance is a placeholder for small per-document effects such as notifications, logging, minor APIs and support allocation.

## 12. Baseline manual-document cost

| Component | Baseline |
|---|---:|
| Extraction labour | $0.188 |
| QC | $0.030 |
| AI | $0.030 |
| OCR | $0.020 |
| Compute | $0.020 |
| Storage/egress | $0.010 |
| Other variable allocation | $0.010 |
| **Subtotal** | **$0.308** |
| Approx. 30% contingency | **~$0.092** |
| **Planning baseline** | **~$0.40/document** |

> **~$0.40/document is a planning baseline for a normal manual-processing document, not an approved selling price.**

Complex documents may cost substantially more.

## 13. Worker capacity

At 20 documents/hour and 160 productive hours/month:

**3,200 documents/month/worker**

| Workers | Approx. manual docs/month |
|---:|---:|
| 1 | 3,200 |
| 5 | 16,000 |
| 10 | 32,000 |
| 25 | 80,000 |
| 50 | 160,000 |

Real capacity must account for training, idle time, assignment, QC, exceptions, communication, management, leave and demand variability.

## 14. Processing Entity economics

Processing Entity payments should initially be treated as **Cost of Revenue**.

Potential models:

1. per document
2. per complexity class
3. per batch
4. negotiated service rate

A future complexity-based model is likely useful:

- Simple → internal rate X
- Standard → internal rate Y
- Complex → internal rate Z
- Exception → negotiated/internal review

CarbonTally then adds the required commercial margin.

## 15. Customer-volume scenarios

These are illustrative, not capacity guarantees.

### Scenario A

100 customers × 500 documents/month:

- 500 users at 5 users/customer
- 50,000 documents/month

### Scenario B

500 customers × 500 documents/month:

- 2,500 users
- 250,000 documents/month

### Scenario C

1,000 customers × 1,000 documents/month:

- 5,000 users
- 1,000,000 documents/month

Application throughput must be load-tested before making capacity promises.

## 16. Manual workforce scenarios

If 30% of documents require manual processing:

| Total docs/month | Manual share | Manual docs | Workers @ 3,200 docs/month |
|---:|---:|---:|---:|
| 50,000 | 30% | 15,000 | ~5 |
| 250,000 | 30% | 75,000 | ~24 |
| 1,000,000 | 30% | 300,000 | ~94 |

This illustrates why automation and Processing Entity scaling matter.

## 17. Revenue models to evaluate

### A — Subscription only

Simple, but risky if processing is unlimited.

### B — Credits

Subscription includes credits; additional credits can be purchased.

### C — Subscription + usage

Base platform subscription plus processing usage.

### D — Subscription + manual extraction

Platform subscription plus separately charged human extraction.

### E — Hybrid

**Platform subscription + included automated processing + additional usage + manual extraction + enterprise/API pricing.**

This is currently the leading hypothesis to investigate, not a final decision.

## 18. Why manual extraction should probably be separate

Manual processing has a direct labour cost. Unlimited manual processing inside a low-cost subscription can make a customer commercially unprofitable.

Manual extraction should therefore probably be a metered, credit-based or service charge.

## 19. Margin framework

Pricing should be derived from:

**Unit cost + risk allowance + desired margin = minimum viable price**

Then compared with:

- customer value
- competitor pricing
- willingness to pay
- target segment

Do not simply copy competitor prices.

## 20. 70% / 100% / 130% sensitivity

| Driver | 70% | Baseline | 130% |
|---|---:|---:|---:|
| Worker monthly loaded cost | $420 | **$600** | $780 |
| Worker productivity | 26 docs/hour | **20 docs/hour** | 14 docs/hour |
| AI/document | $0.021 | **$0.030** | $0.039 |
| OCR/document | $0.014 | **$0.020** | $0.026 |
| QC/document | $0.021 | **$0.030** | $0.039 |
| Compute/document | $0.014 | **$0.020** | $0.026 |
| Storage/egress/document | $0.007 | **$0.010** | $0.013 |
| Other variable/document | $0.007 | **$0.010** | $0.013 |

The 130% case should be used as a safety test when assessing launch pricing.

## 21. Missing inputs

Before final pricing, replace estimates with:

1. actual Vercel plan/usage
2. Render service sizes/usage
3. Supabase usage
4. database growth
5. egress
6. Resend volume
7. actual AI provider/model
8. actual AI tokens/calls/document
9. actual OCR provider
10. actual processing time
11. worker productivity
12. QC productivity
13. error/rework rate
14. support time/customer
15. UK accounting/legal/insurance
16. payment-provider fees
17. backup/DR
18. customer acquisition cost
19. sales cost
20. founder/management replacement cost

## 22. Commercial decision sequence

**Service catalogue**

↓

**Customer problem/value**

↓

**Unit costs**

↓

**Operating overhead**

↓

**Margin target**

↓

**Minimum viable price**

↓

**Customer willingness-to-pay**

↓

**Packaging**

↓

**Subscription model**

↓

**Usage/credits model**

↓

**Manual extraction pricing**

↓

**Billing requirements**

↓

**Stripe vs Paddle vs Lemon Squeezy**

↓

**Final commercial specification**

Do not reverse this order.

## 23. Technical relationship

This document is an **internal business-planning artifact**.

It does not instruct Cline to:

- change the database
- implement billing
- implement subscriptions
- modify pricing
- change infrastructure
- create APIs
- change UI
- change RLS

Its purpose is to support founder-level commercial decisions.

## 24. Current working hypothesis

CarbonTally should investigate selling a combination of:

**platform access + processing services + separately priced/manual extraction**

while supporting:

- direct customer organizations with teams
- consultants managing multiple client organizations
- CarbonTally internal staff
- Processing Entities performing assigned work.

The commercial model must protect CarbonTally against high-cost manual processing while keeping the basic platform accessible.

## 25. Final status

**UNIT ECONOMICS BASELINE V1 — ESTABLISHED**

Next business work:

**Cost refinement → service/value analysis → margin → pricing → packaging → subscription model → payment provider selection.**

No final price has been approved.

No billing provider has been selected.

No billing implementation should be triggered solely from this document.
