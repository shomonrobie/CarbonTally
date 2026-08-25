# CarbonTally Pricing Comparison — Market & Baseline Price v2

**Status:** Internal commercial planning baseline  
**Date:** 2026-08-23  
**Purpose:** Compare what relevant carbon-accounting/data platforms publicly charge for their published packages, what those packages contain, and establish a **provisional CarbonTally price baseline**.

> **Important:** CarbonTally prices below are NOT final prices. They are starting hypotheses for commercial testing. They are deliberately based on market positioning and perceived customer value—not on the CarbonTally cost model. Final pricing should later be adjusted using unit economics, customer interviews, conversion data and actual usage.

---

# 1. Executive decision

CarbonTally should **not** price itself as a cheap clone of a full carbon-accounting/reporting platform.

The proposed initial positioning is:

> **CarbonTally — carbon data processing infrastructure and managed data operations for companies, consultants and carbon-accounting/reporting platforms.**

The provisional commercial architecture is:

1. **Platform plans** for organizations
2. **Processing credits / usage** for automated processing
3. **Manual extraction charges** for human data processing
4. **Consultant plans** for multi-client management
5. **B2B/API plans** for carbon-accounting/reporting companies
6. **Enterprise/custom** for high-volume or white-label requirements

The baseline prices below are intentionally designed to be:

- substantially easier to enter than large enterprise platforms
- high enough to communicate that CarbonTally is a professional B2B service
- transparent enough for online/self-serve acquisition
- compatible with metered processing
- suitable for later increases/decreases.

---

# 2. Market price anchors

## 2.1 CarbonAccounting.ai

CarbonAccounting.ai currently publishes planned pricing:

| Plan | Monthly | Annual equivalent | Main scope |
|---|---:|---:|---|
| Ledger | $390 | $312/mo ($3,744/year) | 1 entity, Scope 1+2, spend-based Scope 3 screening, CSV, classification, evidence links, 3 seats |
| Compliance | $1,290 | $1,032/mo ($12,384/year) | Ledger + activity factors, supplier requests, CSRD/CBAM/ISSB packs, reduction targets, audit log, 10 seats |
| Assurance | $3,900 | $3,120/mo ($37,440/year) | Compliance + multi-entity consolidation, methodology history, restatement handling, assurance workspace, unlimited seats |
| Enterprise | Custom | Custom | SSO/SAML, SCIM, approval workflows, EU residency, custom factors, enterprise contracting |

Source: CarbonAccounting.ai pricing page. citeturn0search1

**Important:** CarbonAccounting.ai explicitly labels these as planned launch pricing and states that it is currently in early access with no charges today. citeturn0search0turn0search1

---

# 3. Normative

Normative does not publish a numeric standard price on its current pricing page.

It sells:

- Essential
- Premium
- consultancy/services

The platform includes automated carbon accounting, AI data matching, emissions-factor database, data upload/QA, reporting, dashboards, calculation transparency, audit history, permissions and other carbon-accounting capabilities. Its services also include **Carbon Inventory Managed Services** and data-management support. citeturn0search3

Normative explicitly describes pricing as quote-based and notes that implementation, data services and ongoing expert support are important parts of total cost of ownership. citeturn0search7

### Market anchor

**No public monthly price — quote.**

This is relevant to CarbonTally because it demonstrates that customers already accept paying separately for software + data services + expert operational support.

---

# 4. Persefoni

Persefoni currently offers a **free Pro** tier for companies with low-to-medium complexity.

The published Pro offering includes:

- Scope 1, 2 and 3
- customer/supply-chain requests
- foundational carbon accounting
- reporting functionality
- Copilot
- self-service resources

Advanced is sales/demo based and adds scalable carbon accounting, advanced analytics, decarbonization planning, integrations and stronger controls. citeturn0search5

Persefoni also publishes California compliance services starting at:

- **$25,000** for SB 253 reporting service
- **$25,000** for SB 261 reporting service
- **$40,000** for Advanced in the referenced pricing material. citeturn0search6turn0search8

### Market anchor

**Free entry → enterprise/managed-services pricing.**

This demonstrates the value of having a low-friction entry product while charging substantially more for high-value managed/compliance services.

---

# 5. Greenly

Greenly is a relevant market reference for carbon accounting + expert services.

Its published LCA material states that pricing depends on:

- carbon-only vs multicriteria assessment
- product complexity
- number of activity lines
- custom emission factors

It uses a three-year contract structure with setup included. Exact standard pricing is not publicly specified in that document. citeturn0search36

### Market anchor

**Quote/complexity based.**

---

# 6. Watershed

Watershed is primarily enterprise-oriented and does not provide a simple public standard price comparable to CarbonAccounting.ai's published tiers.

### Market anchor

**Enterprise/custom quote.**

Therefore this document does NOT invent a Watershed price.

---

# 7. What the market tells us

The market contains several pricing patterns:

| Pattern | Examples | Lesson for CarbonTally |
|---|---|---|
| Free entry | Persefoni Pro | Low-friction acquisition is possible |
| Transparent ~$400/mo entry | CarbonAccounting.ai Ledger | Customers can accept several-hundred-dollar monthly SaaS |
| $1k+/mo compliance | CarbonAccounting.ai Compliance | Compliance/data complexity commands higher price |
| $3k+/mo assurance | CarbonAccounting.ai Assurance | Audit/enterprise value supports premium pricing |
| Quote-based | Normative, Watershed, Greenly | Complex organizations accept custom pricing |
| High-priced managed reporting | Persefoni services | Human services can command substantially higher prices |

---

# 8. CarbonTally service catalogue for pricing

CarbonTally should price the following distinct value areas.

## A. Platform

Customer receives:

- organization workspace
- team members
- document storage
- data processing workspace
- processing status
- dashboards
- emissions data
- evidence traceability
- source-document access
- reverse evidence lookup
- exports
- issues/validation
- notifications
- reports
- collaboration
- security/RLS.

## B. Automated data processing

Customer can submit:

- CSV
- Excel
- JSON
- PDF
- images/scans

for automated extraction/mapping/calculation where supported.

## C. Human/manual extraction

CarbonTally or Processing Entities can:

- extract data from documents
- structure line items
- perform data entry
- handle difficult documents
- QC results
- return structured data to the CarbonTally workflow.

## D. Mapping/calculation

CarbonTally:

- normalizes extracted activity data
- maps to emission factors
- calculates emissions
- preserves calculation lineage.

## E. Evidence/provenance

Customer can see:

- exact source document
- extracted line
- calculation
- emission factor
- resulting emission
- source page/location where available
- technical identifiers
- original vs derived information.

## F. Consultant platform

Consultants can:

- manage multiple client organizations
- work across clients
- assign team members
- process client data
- monitor client status.

## G. Processing Entity network

External processors can:

- receive assigned extraction work
- process assigned documents
- return structured extraction results
- operate within entity-level permissions.

## H. B2B/API

Carbon-accounting/reporting companies can potentially use CarbonTally as:

- extraction backend
- mapping backend
- evidence backend
- managed data-processing service
- human processing capacity.

---

# 9. Proposed CarbonTally baseline prices

These are **market-value hypotheses**, not cost-derived prices.

## 9.1 CarbonTally Starter

### Proposed baseline: **$49/month**

For small organizations beginning carbon-data management.

Includes:

- 1 organization
- 3 users
- source-document storage
- CSV/Excel upload
- basic processing
- emissions calculation
- evidence traceability
- dashboard
- exports
- limited monthly processing credits

### Why $49?

It creates a much lower entry point than CarbonAccounting.ai's $390 Ledger tier while still positioning CarbonTally as professional B2B software.

---

# 10. CarbonTally Professional

### Proposed baseline: **$149/month**

For active organizations processing carbon data regularly.

Includes:

- 10 users
- larger processing allowance
- CSV/Excel/JSON
- PDF/image processing
- automated extraction
- mapping/calculation
- evidence traceability
- reports
- issues/validation
- team workflow
- priority support
- larger document storage allowance.

This should be the **primary self-serve customer plan**.

---

# 11. CarbonTally Business

### Proposed baseline: **$399/month**

This deliberately sits around the same headline price as CarbonAccounting.ai Ledger while offering a different value proposition.

Includes:

- 25 users
- larger processing allowance
- advanced workflow
- consultant collaboration where appropriate
- evidence/provenance
- advanced reporting
- team assignment
- API access allowance
- priority processing
- enhanced support.

### Strategic positioning

CarbonAccounting.ai Ledger:

**$390/month**

focuses on the carbon-accounting ledger itself. citeturn0search1

CarbonTally Business at approximately:

**$399/month**

would instead emphasize:

> **data processing + extraction + mapping + evidence infrastructure**

rather than competing directly on regulatory reporting.

---

# 12. CarbonTally Enterprise

### Proposed baseline: **from $999/month**

For:

- larger organizations
- multiple entities
- high document volume
- multiple teams
- API integrations
- advanced permissions
- white-label workflows
- dedicated support
- custom processing arrangements.

Actual enterprise pricing should be quote-based.

---

# 13. Consultant plan

This deserves its own commercial model because consultants can manage multiple clients.

## CarbonTally Consultant

### Proposed baseline: **$299/month**

Includes:

- consultant workspace
- multiple client organizations
- team assignment
- client workspace access
- client-level reporting
- processing management
- evidence access according to grants
- client onboarding/workflow tools
- base processing credits.

### Consultant Business

### Proposed baseline: **$699/month**

For larger consulting firms.

Includes:

- larger client portfolio
- consultant team
- more processing credits
- API
- white-label options
- advanced client reporting
- priority support.

Additional client/processing usage can be metered.

---

# 14. Automated processing credits

Credits should represent **processing consumption**, not simply storage.

Initial baseline:

### **1 credit = 1 standard automated document-processing unit**

Proposed credit packs:

| Pack | Baseline price |
|---|---:|
| 100 credits | $15 |
| 500 credits | $60 |
| 1,000 credits | $100 |
| 5,000 credits | $400 |
| 10,000 credits | $700 |

This creates declining unit prices for volume.

The exact definition of a "standard document-processing unit" must be finalized later.

---

# 15. Manual extraction pricing

Manual extraction should be separate from normal platform subscription.

Initial market-value baseline:

| Service | Proposed baseline |
|---|---:|
| Simple document | **$0.99/document** |
| Standard document | **$1.99/document** |
| Complex document | **$3.99/document** |
| Very complex / exception | **from $7.50/document** |
| Manual QC/rework | included according to service level |

These are **commercial hypotheses**.

They are intentionally not based on the current internal $0.40 planning cost.

The reason is that the customer is buying:

- human labour
- managed service
- workflow
- extraction
- QC
- structured output
- evidence linkage
- platform processing.

The final price should be validated against willingness-to-pay and actual productivity.

---

# 16. Bulk manual extraction

For customers with large volumes:

| Monthly manual volume | Baseline commercial direction |
|---:|---|
| <100 docs | standard list price |
| 100–999 | 10–20% volume discount |
| 1,000–4,999 | 20–30% volume discount |
| 5,000+ | custom Processing Entity rate |

The customer should see a clear economic benefit from committing volume.

---

# 17. Evidence/provenance

### Proposed baseline

**Included in all paid plans.**

Do NOT charge separately for:

> "Where did this emission come from?"

Evidence traceability should be a core CarbonTally value proposition.

This includes:

- document
- extracted line
- source location where available
- factor
- calculation
- emission result
- reverse lookup.

This is strategically important because CarbonAccounting.ai also advertises evidence links in its entry Ledger tier. citeturn0search1

CarbonTally therefore should not treat provenance as an optional premium feature.

---

# 18. Storage

### Proposed baseline

Include reasonable document storage in every paid plan.

Do not charge immediately per GB.

Possible future model:

- included storage
- additional storage packs
- enterprise storage pricing.

The customer is primarily buying **data processing**, not cloud storage.

---

# 19. API pricing

Initial baseline:

### Professional

Small API allowance included.

### Business

Larger API allowance included.

### Enterprise

Custom.

Possible future:

**$99/month API add-on**

for customers who need API access but don't require Enterprise.

---

# 20. White-label pricing

White-label should be a premium feature.

Initial baseline:

### **$199/month add-on**

or included in higher consultant/enterprise packages.

Potential components:

- custom branding
- custom sender
- custom domain
- branded reports
- client-facing identity.

Large white-label deployments should be custom priced.

---

# 21. High-volume B2B / carbon-platform pricing

This may become one of CarbonTally's most important commercial products.

Potential model:

### Carbon Data Processing API

**Starting around $499/month**

plus usage.

For example:

- API access
- automated extraction
- mapping
- calculation
- evidence identifiers
- webhooks
- structured output.

Large carbon-reporting companies:

**Custom annual contract**

This is where CarbonTally could become infrastructure rather than merely another SaaS application.

---

# 22. Direct comparison — baseline positioning

| Service | CarbonAccounting.ai | Normative | Persefoni | CarbonTally baseline |
|---|---:|---:|---:|---:|
| Entry platform | $390/mo | Quote | Free Pro | **$49/mo** |
| Main SMB/mid-market | $390–$1,290/mo | Quote | Advanced quote | **$149/mo** |
| Business | $1,290/mo Compliance | Quote | Advanced quote | **$399/mo** |
| Assurance/enterprise | $3,900/mo | Quote | Advanced/quote | **from $999/mo** |
| Manual extraction | Not a headline metered service | Managed services | Professional services | **$0.99–$3.99+ / document** |
| Automated document processing | Included within platform | Included | Included | **credits + plan allowance** |
| Evidence traceability | Included Ledger | Included audit/calculation capabilities | Audit trail | **Included** |
| Consultant multi-client | Assurance shape | Services/platform | Enterprise/services | **$299/mo+** |
| Processing Entity network | No equivalent core proposition | Managed service | Professional services | **Core differentiator** |
| Carbon-platform API | Enterprise/custom | Enterprise | Enterprise | **from ~$499/mo + usage** |
| White-label | Enterprise/custom | Custom | Enterprise | **$199/mo add-on / Enterprise** |

**Interpretation:** The CarbonTally figures are proposed baselines, not market facts.

---

# 23. Why the $49 / $149 / $399 ladder is useful

It creates three psychologically distinct levels:

### $49

"I can try this without a major procurement decision."

### $149

"This is a serious operational tool for my organization."

### $399

"This is becoming part of our carbon-data infrastructure."

This also leaves room above $399 for:

- Enterprise
- consultants
- API customers
- high-volume customers
- white-label.

---

# 24. Why CarbonTally should not launch at $390 as its entry plan

CarbonAccounting.ai can justify $390 because its entry product is positioned as a carbon-accounting ledger.

CarbonTally's initial wedge is different.

We want customers to say:

> "I'll upload my messy data and let CarbonTally process it."

A $49/$149 entry structure lowers the barrier to trying the processing workflow.

Once customers depend on CarbonTally's data pipeline, processing volume and higher-value services can expand revenue.

---

# 25. Why we should not make manual extraction free

A customer with:

**5,000 invoices**

could create a substantial service workload.

Manual extraction must therefore remain commercially visible.

The customer should understand:

> Software subscription ≠ unlimited human labour.

---

# 26. The strongest commercial package to test first

If we had to launch tomorrow with these as hypotheses:

### Starter

**$49/month**

### Professional

**$149/month**

### Business

**$399/month**

### Consultant

**$299/month**

### Consultant Business

**$699/month**

### Enterprise

**from $999/month**

### Automated credits

**$15 / 100 → declining with volume**

### Manual extraction

**$0.99 / $1.99 / $3.99+**

### White-label

**$199/month add-on**

### Carbon-platform API

**from $499/month + usage**

Again:

> **These are baseline commercial hypotheses, not final prices.**

---

# 27. What should remain free

To reduce acquisition friction:

- landing page
- product tour
- documentation
- demo
- basic account creation
- perhaps a small processing trial
- perhaps a limited number of automated documents.

Do not give away substantial human extraction for free.

---

# 28. What should NOT be separately priced initially

Avoid nickel-and-diming customers for:

- normal team members
- evidence traceability
- normal dashboards
- normal exports
- basic document storage
- normal calculation
- basic validation
- normal notifications.

The customer should understand the bill.

---

# 29. Recommended initial commercial architecture

```text
                    CARBONTALLY
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
    PLATFORM          PROCESSING        SERVICES
       │                 │                 │
   $49 / $149 /       Credits          Manual extraction
      $399             usage             $0.99+
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                Enterprise / API
                   $999+ / custom
```

Consultants have a separate workspace subscription and can purchase additional processing capacity.

Carbon-accounting/reporting companies can consume CarbonTally through API/data-processing contracts.

---

# 30. The key strategic question

The next question is NOT:

> "Can we charge $149?"

It is:

> **"Which CarbonTally service will customers pay for first?"**

There are three likely entry wedges:

### Wedge A — Data processing

"I have messy data and need it converted into carbon-ready data."

### Wedge B — Managed extraction

"I have thousands of invoices/PDFs and don't want my staff to extract them."

### Wedge C — Infrastructure

"I already have a carbon-reporting platform and need a reliable data-processing backend."

CarbonTally should test all three, but Wedge C could ultimately have the highest strategic value.

---

# 31. Final baseline price book — NOT FINAL

| Product/service | Baseline hypothesis |
|---|---:|
| Starter | **$49/mo** |
| Professional | **$149/mo** |
| Business | **$399/mo** |
| Enterprise | **from $999/mo** |
| Consultant | **$299/mo** |
| Consultant Business | **$699/mo** |
| 100 automated credits | **$15** |
| 500 automated credits | **$60** |
| 1,000 automated credits | **$100** |
| 5,000 automated credits | **$400** |
| 10,000 automated credits | **$700** |
| Simple manual document | **$0.99** |
| Standard manual document | **$1.99** |
| Complex manual document | **$3.99** |
| Exception document | **from $7.50** |
| White-label add-on | **$199/mo** |
| Carbon-platform API | **from $499/mo + usage** |

---

# 32. Relationship to the Unit Economics Baseline

This document intentionally uses a **different decision lens** from:

`CarbonTally_Unit_Economics_Baseline_v1.md`

Unit Economics asks:

> **What does CarbonTally need to charge to remain economically viable?**

This document asks:

> **What does the market appear willing to pay for comparable value, and what price architecture should CarbonTally test?**

The final price must satisfy BOTH.

---

# 33. Next commercial step

Now combine:

**Market price benchmark**

+

**CarbonTally unit economics**

+

**customer willingness-to-pay**

to produce:

### CarbonTally Commercial Pricing v1

That document should determine:

- final plan names
- included usage
- credit definition
- manual extraction tiers
- overage pricing
- consultant pricing
- API pricing
- enterprise pricing
- annual discount
- trial
- free tier
- payment-provider requirements.

Only after that should we decide whether Stripe, Paddle, Lemon Squeezy or another provider is the best fit.

---

# 34. Final status

**CARBONTALLY PRICING COMPARISON — BASELINE V2 COMPLETE**

Competitor prices are market research and should be rechecked before publication.

CarbonTally prices are **provisional commercial hypotheses only**.

No pricing is final.

No billing provider is selected.

No billing implementation should be triggered from this document alone.
