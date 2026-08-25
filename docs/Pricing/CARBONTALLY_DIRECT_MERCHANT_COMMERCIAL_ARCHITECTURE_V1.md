# CarbonTally Direct Merchant Commercial Architecture V1

**Status:** Reference decision document  
**Date:** 23 August 2026  
**Decision owner:** CarbonTally Product Owner  
**Purpose:** Record the current commercial/billing architecture decision for future validation.  
**Important:** This is a working product decision, not legal, tax, accounting, or financial advice.

---

## 1. Executive Decision

CarbonTally's current preferred commercial architecture is:

> **CarbonTally (UK) Limited will be the direct merchant and customer-facing service provider.**

CarbonTally will own the commercial relationship with customers and the delivery of its software and processing services.

A separate payment provider may be used as payment infrastructure. The payment provider is **not assumed to be the Merchant of Record**.

The decision will be validated again when CarbonTally enters real commercial operations and has actual customer, payment, VAT, tax, accounting, refund and international-sales requirements.

---

## 2. Why This Decision Was Made

CarbonTally is not intended to be only a conventional SaaS reporting application.

Its planned commercial offering combines:

- SaaS/data-management functionality
- automated data processing
- automated extraction and mapping
- emission-factor matching
- emission calculation
- evidence/provenance
- human-assisted processing
- Managed Processing
- consultant workspaces
- Processing Entity operations
- future B2B/API processing services

Because of this hybrid model, CarbonTally benefits from controlling the customer relationship, service definition, pricing, entitlements and processing services.

The preferred direction is therefore to make CarbonTally itself the merchant while outsourcing specialist payment/accounting infrastructure where appropriate.

---

# 3. Commercial Ownership Model

## CarbonTally (UK) Limited owns

### Customer relationship

- customer account
- organization
- team
- consultant relationships
- customer support
- service terms
- customer-facing pricing
- customer-facing subscription
- customer-facing processing orders

### Product/service

- CarbonTally software
- document/data storage
- extraction
- mapping
- emission factors
- calculations
- evidence traceability
- reports/data outputs
- automated processing
- Assisted Processing
- Managed Processing

### Commercial entitlements

- plans
- credits
- credit balance
- credit consumption
- rollover
- emergency processing allowance
- human-processing orders
- Managed Processing orders
- service status

### Billing records

CarbonTally should maintain the authoritative application-level state for:

- customer subscription
- plan
- entitlement
- credit ledger
- usage
- processing orders
- service charges
- payment status/reference
- refunds/status where applicable

---

# 4. Payment Provider Role

The payment provider is intended to be infrastructure.

It may provide:

- payment processing
- card/payment authorization
- payment tokenization
- recurring payment execution
- payment failure handling
- payment webhooks
- payment security
- potentially customer payment methods and payment-related portals

The exact provider is **not yet selected**.

Possible providers include:

- Stripe
- PayPal
- other suitable payment infrastructure providers

Paddle and Lemon Squeezy remain possible alternatives if later research demonstrates that a Merchant-of-Record model is materially better for CarbonTally.

---

# 5. External Accounting and Tax Support

CarbonTally may appoint an external UK accountant/tax adviser.

Expected responsibilities may include:

- bookkeeping
- statutory accounts
- VAT administration
- corporation-tax support
- tax returns
- tax reporting
- international VAT/tax advice
- accounting treatment of subscriptions, credits and service revenue
- advice on refunds, chargebacks and other commercial transactions

The use of an external accountant does **not** remove the company's ultimate legal responsibilities.

Exact responsibilities must be agreed with the appointed professional adviser.

---

# 6. Commercial Model Already Agreed as Baseline

The working CarbonTally model is:

```text
Subscription
     +
Automated Processing Credits
     +
Assisted/Human Processing
     +
Managed Processing
     +
Enterprise / B2B / API services
```

This is a baseline commercial architecture and remains subject to real-market validation.

---

# 7. Customer Operating Modes

CarbonTally will support three conceptual operating modes.

## Self-Service

Customer operates the workflow.

## Assisted Processing

CarbonTally automatically processes what it can and offers human processing where additional work is required.

## Managed Processing

Customer uploads documents and CarbonTally manages the processing workflow through completion.

This allows CarbonTally to sell both:

> **software**

and:

> **the outcome/service.**

---

# 8. Credit System

Credits are CarbonTally's internal automated-processing entitlement mechanism.

The external payment provider does **not** become the authoritative credit ledger.

Example:

```text
Customer pays
      ↓
Payment provider confirms payment
      ↓
CarbonTally records payment event
      ↓
CarbonTally grants plan/package credits
      ↓
Processing consumes CarbonTally credits
```

CarbonTally therefore retains control over:

- credit issuance
- credit consumption
- credit rollover
- credit adjustments
- promotional credits
- emergency allowances
- audit history

---

# 9. Credit Rollover

Current decision:

> **Customers should not lose paid processing value merely because a billing period ends.**

Unused paid credits should be eligible for rollover, subject to final commercial/accounting rules.

This is based on the customer-trust principle:

> **Customers should not feel that CarbonTally deliberately makes them lose paid value.**

---

# 10. Emergency Processing Allowance

Current working decision:

If a customer exhausts purchased credits while completing an active job, CarbonTally may provide a temporary allowance to allow the active job to finish.

The previously discussed baseline is approximately:

> **up to 10% additional processing allowance**

This should be treated as an advance/controlled allowance rather than unrestricted free usage.

Final reconciliation rules remain to be defined before production billing implementation.

---

# 11. Human/Assisted Processing

Human processing is commercially separate from ordinary automated processing credits.

Working baseline:

| Complexity | Baseline customer price |
|---|---:|
| Simple | ~$0.99/document |
| Standard | ~$1.99/document |
| Complex | ~$3.99+/document |
| Exceptional | Quote/assessment |

These are **baseline hypotheses**, not final public prices.

Human-processing orders should preferably be grouped into batches/orders rather than creating a separate payment transaction for every $0.99 document.

Example:

```text
75 Simple documents
75 × $0.99
= $74.25

One Assisted Processing order
```

This is commercially and operationally more sensible than processing 75 independent payment transactions.

---

# 12. Managed Processing

Managed Processing is a separate service.

The customer may simply:

> Upload documents and ask CarbonTally to manage the work.

CarbonTally can then coordinate:

- automated processing
- human escalation
- mapping
- validation
- QC
- rework
- evidence/provenance
- completion

Managed Processing may eventually be sold through:

- batch pricing
- monthly managed service
- enterprise contract
- custom SLA

Final pricing remains open.

---

# 13. Provider-Neutral Billing Architecture

CarbonTally should not hard-code the product architecture around one payment company.

Recommended architecture:

```text
                  CarbonTally
                       │
                Billing Service
                       │
              Provider Adapter
                 /          \
                /            \
           Stripe           PayPal
                \
                 \
            Future Provider
```

Provider-specific details should remain isolated:

- external customer ID
- external subscription ID
- product/price ID
- checkout/session ID
- webhook format
- provider API calls

CarbonTally should use provider-neutral internal concepts.

---

# 14. Recommended Internal Model

Conceptually:

```text
CarbonTally Customer
        │
        ├── Subscription
        │
        ├── Plan
        │
        ├── Entitlements
        │
        ├── Credit Ledger
        │
        ├── Usage
        │
        ├── Assisted Processing Orders
        │
        └── Managed Processing Orders
```

External payment provider:

```text
CarbonTally Customer
        │
        └── External Billing Identity
                ├── Provider
                ├── Customer ID
                ├── Subscription ID
                └── Payment references
```

---

# 15. Switching Payment Providers

CarbonTally should be designed so that the payment provider can be changed later.

For example:

```text
Current provider: Stripe

New customers → Stripe
Existing customers → Stripe
```

Later:

```text
Current provider: PayPal

New customers → PayPal
Existing customers → existing provider
```

A provider switch should **not** imply automatic migration of existing subscriptions.

Existing subscriptions may remain attached to their original provider until a controlled migration is performed.

---

# 16. One-Click Provider Selection

A future administration interface may expose:

> **Active Payment Provider**

- ● Stripe
- ○ PayPal
- ○ Other configured provider

However, this setting should control **new commercial transactions** unless a formal subscription migration has been implemented.

It should not silently cancel or recreate existing customer subscriptions.

---

# 17. Billing Event Flow

Recommended architecture:

```text
Customer
   ↓
CarbonTally checkout
   ↓
Payment provider
   ↓
Payment confirmation/webhook
   ↓
CarbonTally Billing Service
   ↓
Validate event
   ↓
Update subscription/payment state
   ↓
Grant/update entitlement
   ↓
Update credit ledger
   ↓
Customer receives CarbonTally service
```

Webhook processing must be idempotent.

A payment event must not accidentally grant credits twice.

---

# 18. CarbonTally Invoice/Order Model

CarbonTally should maintain customer-facing commercial records appropriate to the service.

Examples:

- subscription
- credit purchase
- Assisted Processing order
- Managed Processing order
- refund/credit adjustment
- service status

The exact legal invoice format, VAT wording and accounting treatment must be confirmed by the UK accountant/tax adviser.

---

# 19. Important Difference: Payment vs Entitlement

The payment provider answers:

> **Did the customer pay?**

CarbonTally answers:

> **What is this customer entitled to receive?**

This distinction is fundamental.

For example:

```text
Payment provider:
Payment successful: £149

CarbonTally:
Plan = Professional
Credits granted = 500
Subscription = Active
```

CarbonTally should not require the payment provider to understand CarbonTally's processing economics.

---

# 20. Customer Experience

The customer should primarily experience:

> **CarbonTally**

not the payment provider.

Customer-facing CarbonTally surfaces should include:

- plan
- subscription status
- credits
- usage
- processing orders
- invoices/receipts where applicable
- payment status
- billing history
- cancellation/upgrade options

Provider-specific branding may appear where legally or technically required.

---

# 21. Why We Are Not Selecting a Merchant of Record Now

Paddle and Lemon Squeezy remain useful options.

However, the current preference is:

> **CarbonTally should remain the direct merchant.**

The reason is that CarbonTally's service includes:

- software
- automated processing
- human processing
- Managed Processing
- potentially B2B/API services.

A direct-merchant architecture gives CarbonTally greater control over this hybrid commercial model.

This decision should be reconsidered if real-world tax, compliance, administrative or provider requirements make the Merchant-of-Record model materially better.

---

# 22. What Must Be Professionally Validated

Before production billing launch, CarbonTally should obtain professional advice on:

1. UK VAT registration and obligations
2. B2B vs B2C treatment
3. UK vs EU customer treatment
4. international customer taxation
5. digital-service VAT rules
6. human-processing service taxation
7. Managed Processing taxation
8. invoice requirements
9. credit/unused-credit accounting
10. refunds
11. chargebacks
12. subscription revenue recognition/accounting
13. future CarbonTally IE/EU structures
14. payment-provider contractual requirements

This document intentionally does not attempt to make legal or tax determinations.

---

# 23. Future Company Structure

The current commercial entity decision is:

> **CarbonTally (UK) Limited**

Future entities may be created if commercially/tax/legal appropriate, such as:

- CarbonTally (IE) Limited
- CarbonTally (EU) Limited
- CarbonTally (BD) Limited

The need, structure and inter-company relationships are **not finalized** by this document.

Any future structure must be reviewed professionally.

---

# 24. Relationship With Processing Entities

Processing Entities may perform human extraction work for CarbonTally.

The customer relationship remains with CarbonTally.

Conceptually:

```text
Customer
   ↓
CarbonTally
   ↓
Processing Entity
   ↓
Human extraction
   ↓
QC
   ↓
CarbonTally
   ↓
Customer
```

Processing Entity compensation is an internal CarbonTally commercial arrangement.

It is not the customer's responsibility.

---

# 25. Current Decisions

| Decision | Status |
|---|---|
| CarbonTally (UK) Limited as direct merchant | **APPROVED — current preference** |
| CarbonTally customer-facing service provider | **APPROVED** |
| External accountant/tax adviser | **APPROVED IN PRINCIPLE** |
| Payment provider as infrastructure | **APPROVED** |
| Provider-neutral billing architecture | **APPROVED** |
| CarbonTally-owned credit ledger | **APPROVED** |
| Subscription + credits model | **APPROVED AS BASELINE** |
| Separate human processing | **APPROVED AS BASELINE** |
| Managed Processing | **APPROVED AS BASELINE** |
| Credit rollover | **APPROVED IN PRINCIPLE** |
| Emergency allowance | **APPROVED IN PRINCIPLE** |
| Paddle as MoR | **NOT SELECTED** |
| Lemon Squeezy as MoR | **NOT SELECTED** |
| Stripe | **CANDIDATE PAYMENT PROVIDER** |
| PayPal | **CANDIDATE PAYMENT PROVIDER** |
| Final payment provider | **NOT SELECTED** |
| Final tax structure | **NOT SELECTED** |
| Final public pricing | **NOT SELECTED** |

---

# 26. What This Document Does NOT Authorize

This document does not authorize:

- production billing implementation
- Stripe implementation
- PayPal implementation
- Paddle implementation
- Lemon Squeezy implementation
- final public pricing
- VAT/tax assumptions
- production subscription terms
- production invoice templates
- automatic provider switching
- creation of additional CarbonTally companies

Those require subsequent decisions.

---

# 27. Future Revalidation Trigger

This architecture should be reviewed when any of the following occurs:

- first real customer
- first real payment
- VAT registration
- significant international sales
- significant B2C sales
- first large Managed Processing contract
- first enterprise contract
- launch of CarbonTally IE/EU
- material payment-provider restrictions
- significant billing volume
- accountant/tax adviser recommends a different structure

The architecture is intentionally **revisable**.

---

# 28. Product Owner Summary

### Current decision

> **CarbonTally (UK) Limited will initially act as the direct merchant and customer-facing service provider.**

### Payment provider

> Use a payment provider as infrastructure, not automatically as Merchant of Record.

### Billing ownership

> CarbonTally owns plans, subscriptions/entitlements, credits, processing usage and service orders.

### Accounting/tax

> Use an external UK accountant/tax adviser.

### Commercial model

> Subscription + automated processing credits + Assisted Processing + Managed Processing + Enterprise/B2B.

### Provider strategy

> Provider-neutral architecture so the payment provider can be changed later.

### Validation

> Revisit the decision when real-world customers, payments, tax obligations and operational data become available.

---

## Final Principle

> **CarbonTally owns the customer relationship and the service outcome. Payment providers provide payment infrastructure. Professional advisers handle specialist accounting and tax work.**

This is the current CarbonTally commercial architecture and should be treated as a **working baseline, not an irreversible commitment**.

---

**END OF DOCUMENT**
