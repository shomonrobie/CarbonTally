# CT-SUB-001 — CarbonTally Configurable Subscription & Billing Product Specification

**Document ID:** CT-SUB-001  
**Version:** 0.1  
**Date:** 2026-10-04  
**Status:** **PROPOSED — PO REVIEW REQUIRED — NOT YET AUTHORIZED FOR IMPLEMENTATION**  
**Owner:** CarbonTally Product Owner  
**Purpose:** Authoritative product and UX specification for a configurable, database-driven Subscription & Billing module.

---

## 1. Executive Summary

CarbonTally requires a **configurable Subscription & Billing module**, not a hard-coded collection of pricing pages.

The module must allow authorized Platform Administrators to configure commercial plans, prices, billing intervals, features, limits, add-ons, trials, discounts, availability, and payment-provider selection without requiring code changes for ordinary commercial configuration.

The architecture must remain **server-authoritative**:

> **Admin configuration → validated database state → server-side entitlement/price resolution → payment-provider checkout → provider webhook → CarbonTally subscription state → entitlement enforcement**

A customer-facing UI may display a price, but the displayed price is never the authority for charging. At purchase time, the backend must resolve the currently valid price from CarbonTally's database/configuration and use that authoritative value when creating the payment-provider checkout/subscription transaction.

Manual Processing is a subscription entitlement/service inside this broader module. It is **not a separate billing system**.

This document intentionally does not hard-code final commercial values such as £79, £249, a 14-day trial, or Stripe as the permanent provider. Those are configurable/product decisions. The system must support configuring them.

---

## 2. Governance Status

### 2.1 Current status

**PROPOSED — NOT YET PO APPROVED**

This document is a product specification, not an implementation authorization.

### 2.2 Required sequence

1. Complete `CT-DISC-SUB-001` current-state discovery.
2. Reconcile this specification against the actual repository and discovery findings.
3. Resolve any architecture conflicts or PO decisions.
4. PO approves the reconciled specification.
5. Create a bounded implementation prompt.
6. Cline implements.
7. Independent verification is performed.
8. PO makes final acceptance/closure decision.
9. Production migration/deployment only after explicit authorization.

### 2.3 Authority hierarchy

For this module:

1. Explicit PO-approved decisions.
2. Existing verified CarbonTally architecture and security model.
3. This specification after PO approval.
4. Existing implementation, where consistent with the approved design.
5. Market research and competitor material as product input only.

The external DeepSeek proposal is **reference material, not authority**.

---

# 3. Product Objectives

The module must:

- provide a coherent subscription experience across Public, Customer, Consultant, and Platform Admin surfaces;
- support configurable plans;
- support configurable prices;
- support monthly/annual or other configured billing intervals;
- support versioned commercial configurations;
- support configurable feature entitlements;
- support configurable limits and usage allowances;
- support configurable add-ons;
- support configurable trials;
- support configurable discounts/promotions where enabled;
- support one or more payment providers through a provider abstraction;
- allow an authorized Admin to select the active payment provider;
- keep payment-provider details and secrets secure;
- resolve purchase price server-side from the database;
- synchronize subscription lifecycle through provider events/webhooks;
- maintain CarbonTally's own subscription state;
- centrally resolve entitlements;
- integrate Manual Processing without creating parallel billing;
- preserve existing RLS/security and organization-scoped billing architecture;
- provide auditability for commercial changes;
- avoid hard-coded commercial values in frontend code.

---

# 4. Non-Goals

This specification does not authorize:

- a new payment provider contract being purchased;
- final pricing;
- final plan names;
- final plan count;
- final trial duration;
- final limits;
- final discount policy;
- final tax/VAT policy where not already defined;
- production migration;
- production payment-provider credentials;
- production deployment;
- replacing existing subscription infrastructure without discovery justification;
- a second parallel billing/subscription system;
- arbitrary manual entitlement bypasses without audited governance.

---

# 5. Current UI Baseline — Demo Lab Evidence

The current Demo Lab customer experience already contains a **Billing** page. This page must be treated as an existing product surface to preserve and extend, not as a blank slate.

The supplied Demo Lab screenshot shows the customer Billing page containing:

- Plan / active subscription status;
- Billing mode;
- Credits;
- Storage;
- Credit history;
- Assisted Processing estimate;
- Managed Processing request;
- Orders.

The current example shows **No active subscription**, `CREDIT` billing mode, zero available credits, storage usage, and existing Assisted/Managed Processing and Orders sections.

### Current UI status

| Persona / surface | Current state | CT-SUB-001 target |
|---|---|---|
| Customer | **EXISTS** — Billing page | **EXTEND/PRESERVE** |
| Consultant workspace | **NO billing/subscription UI identified** | **ADD** |
| Platform Admin / Platform Owner | **NO subscription/billing management UI identified** | **ADD** |
| Public website | Subscription/pricing/checkout not yet established as a complete flow | **ADD** |

### Existing Customer Billing principle

The existing Customer Billing page must not be replaced merely because CT-SUB-001 introduces a broader Subscription & Billing module.

Instead, the implementation must first map the existing sections:

```text
CURRENT CUSTOMER BILLING
────────────────────────────────────
Plan
Billing mode
Credits
Storage
Credit history
Assisted Processing estimate
Managed Processing
Orders
```

into the target commercial architecture:

```text
TARGET CUSTOMER SUBSCRIPTION & BILLING
────────────────────────────────────────
Subscription
 ├── Current Plan
 ├── Billing / Renewal
 ├── Usage & Limits
 ├── Payment Method
 ├── Invoices
 ├── Plan Change
 └── Entitlements

Processing Services
 ├── Assisted Processing
 ├── Managed Processing
 └── Orders / service history
```

Existing functionality must be preserved where it remains valid. The implementation must identify whether `Billing mode`, `Credits`, `Storage`, `Orders`, Assisted Processing, and Managed Processing are subscription entitlements, usage/credits, operational services, or legacy commercial constructs before changing their semantics.

**Evidence note:** The current Demo Lab screenshot is supplied as product-state evidence. It does not by itself establish the backend implementation or database model; `CT-DISC-SUB-001` remains responsible for verifying those details.

---

# 6. Existing-First Architecture Principle

CarbonTally already has subscription-related infrastructure. The implementation must extend/reuse it rather than create a parallel architecture.

The current architecture identified for reconciliation includes:

- `public.customer_subscriptions`
- `public.billing_plans`
- versioned plan configuration
- `features` JSONB
- existing subscription lifecycle/status concepts
- organization-scoped billing
- `backend/data/billing.py::get_active_for_org`
- existing Platform Admin commercial plan management
- legacy `assisted_processing_available`
- existing `features.manual_processing.enabled`

These items must be verified by `CT-DISC-SUB-001` before implementation.

### Rule

> **Do not create a new Subscription model merely because a conceptual specification contains one.**

If existing tables/services already provide the required capability, extend them.

---

# 7. Commercial Architecture

## 6.1 Core model

The commercial model is:

```text
PLAN CATALOG
    │
    ├── Plan versions
    │      ├── features
    │      ├── limits
    │      ├── prices
    │      ├── billing intervals
    │      └── availability
    │
    ├── Add-ons
    │
    └── Promotions / trials
            │
            ▼
CUSTOMER SUBSCRIPTION
            │
            ▼
CENTRAL ENTITLEMENT RESOLUTION
            │
            ├── Product features
            ├── Usage limits
            ├── Processing services
            └── Manual Processing
```

---

# 8. Configurable Plans

Platform Admin must be able to create and manage plan definitions.

A plan may have:

- internal identifier;
- display name;
- description;
- marketing summary;
- status;
- visibility;
- sort order;
- billing intervals;
- prices;
- features;
- limits;
- add-ons;
- trial eligibility;
- target customer segment;
- provider mapping where required;
- effective dates;
- version history.

### Example

```text
Platform Admin
┌───────────────────────────────────────────────┐
│ PLAN: Professional                            │
├───────────────────────────────────────────────┤
│ Name:        [ Professional                 ] │
│ Status:      [ ACTIVE ▼ ]                    │
│ Public:      [ ✓ ]                            │
│ Sort order:  [ 20 ]                           │
│                                               │
│ Description                                   │
│ [ Evidence-grade carbon accounting...       ] │
│                                               │
│ Billing                                      │
│ [✓] Monthly      Price [ £______ ]           │
│ [✓] Annual       Price [ £______ ]           │
│                                               │
│ Features                                      │
│ [✓] Scope 1                                    │
│ [✓] Scope 2                                    │
│ [✓] Scope 3                                    │
│ [✓] Evidence chain                            │
│ [✓] Manual Processing                         │
│ [ ] API                                       │
│                                               │
│ Limits                                        │
│ Documents/month [ ______ ]                    │
│ Users          [ ______ ]                     │
│ Entities       [ ______ ]                     │
│                                               │
│ [ Save Draft ] [ Publish New Version ]        │
└───────────────────────────────────────────────┘
```

---

# 9. Price Configuration

Prices must be stored/configured in CarbonTally's authoritative commercial data.

### Mandatory principle

**The frontend must never be the source of truth for purchase price.**

Purchase flow:

```text
Customer clicks Subscribe
        │
        ▼
Backend receives plan/version/interval selection
        │
        ▼
Backend validates plan availability
        │
        ▼
Backend resolves authoritative current price from DB
        │
        ▼
Backend validates currency/tax/commercial rules
        │
        ▼
Backend creates provider checkout/subscription
        │
        ▼
Provider charges/reserves configured amount
```

A client-submitted amount such as:

```json
{
  "price": 1.00
}
```

must never be trusted.

The backend must ignore client-supplied price values and resolve its own authoritative amount.

---

# 10. Price Versioning

Commercial changes must be auditable.

Where an existing customer has subscribed under a previous price/version, changing the catalog price must not silently rewrite historical subscription terms.

Conceptually:

```text
Professional v1
£79/month
ACTIVE FOR EXISTING SUBSCRIPTIONS

Professional v2
£99/month
CURRENT FOR NEW PURCHASES
```

The exact implementation must reuse existing versioning capabilities where possible.

---

# 11. Billing Intervals

The system should support configurable billing intervals.

Initial expected candidates:

- monthly;
- annual.

The architecture should not make those values impossible to extend later.

The Admin UI should allow only intervals supported by the implementation/provider.

---

# 12. Feature Entitlements

Features must be data/configuration driven.

Conceptually:

```text
features:
  scope_1:
    enabled: true
  scope_2:
    enabled: true
  scope_3:
    enabled: true
  evidence_chain:
    enabled: true
  manual_processing:
    enabled: true
  api_access:
    enabled: false
```

The canonical Manual Processing entitlement is:

`features.manual_processing.enabled`

`assisted_processing_available` remains a backward-compatible legacy alias where required by the existing system. It must not become a competing commercial truth.

---

# 13. Usage Limits

The module should support configurable limits where a feature is naturally quota-based.

Potential dimensions include:

- documents/uploads;
- users/seats;
- entities;
- API requests;
- processing units;
- other product-specific usage.

Limits must be:

- database-configured;
- enforced server-side;
- visible to the customer where appropriate;
- auditable;
- reset according to configured billing/usage period.

The exact initial dimensions and values remain PO/product decisions.

---

# 14. Add-Ons

The architecture should support independently configurable add-ons.

Potential examples:

- additional processing capacity;
- Manual Processing coverage;
- additional users;
- additional entities;
- API capacity;
- other future services.

An add-on must have:

- identifier;
- name;
- description;
- status;
- price(s);
- billing interval;
- entitlement effect;
- availability;
- provider mapping where required.

---

# 15. Manual Processing Integration

Manual Processing is part of the Subscription module.

Commercial entitlement remains separate from operational activation:

```text
Subscription
     │
     ▼
Commercial Entitlement
     │
     ▼
FIN-06 Governance
     │
     ▼
Processing / Routing
     │
     ▼
Processing Entity
```

The already-approved Manual Processing commercial design remains authoritative.

Supported commercial paths:

### A. Direct customer subscription

Customer's organization has an active subscription containing Manual Processing entitlement.

### B. Consultant-sponsored subscription

Consultant firm's organization purchases Manual Processing coverage for eligible consultant clients.

Coverage modes:

- `SELECTED_CLIENTS`
- `ALL_ELIGIBLE_CLIENTS`

Direct and sponsored entitlement combine as:

```text
effective_manual_processing_entitlement
    =
DIRECT
OR
SPONSORED
```

This does not automatically assign a Processing Entity.

Consultant sponsorship is commercial entitlement, not automatic operational activation.

---

# 16. Consultant Commercial UX

```text
Consultant Portal
┌─────────────────────────────────────────────┐
│ Dashboard                                   │
│ Clients                                     │
│ Subscription  ◄                             │
│ Billing                                     │
└─────────────────────────────────────────────┘

Subscription
┌─────────────────────────────────────────────┐
│ Firm Subscription                           │
│ Plan: [Configured Plan]                     │
│ Status: ACTIVE                              │
│                                             │
│ Manual Processing Coverage                 │
│                                             │
│ ○ SELECTED CLIENTS                          │
│   Purchased capacity: 25                    │
│   Allocated: 18                             │
│   Available: 7                              │
│                                             │
│ ○ ALL ELIGIBLE CLIENTS                      │
│   Coverage: Active                          │
│                                             │
│ [ Manage Coverage ] [ Billing ]             │
└─────────────────────────────────────────────┘
```

For selected clients:

```text
Manual Processing Capacity
────────────────────────────────
Purchased:     25
Allocated:     18
Available:      7

Clients
☑ Client A
☑ Client B
☐ Client C
☑ Client D

[ Allocate ]
[ Release Allocation ]
```

The UI must not expose consultant commercial information to client organizations.

---

# 17. Public Website UX

The public website must be capable of presenting the currently published commercial catalogue.

```text
CarbonTally
────────────────────────────────────────────
Evidence-grade carbon accounting

[ Product ] [ How It Works ] [ Pricing ] [ Login ]

Pricing
────────────────────────────────────────────

                 Monthly     Annual

STARTER          £XX         £XX
                 [ Get Started ]

PROFESSIONAL     £XX         £XX
                 [ Get Started ]

BUSINESS         £XX         £XX
                 [ Get Started ]

ENTERPRISE       Custom      Custom
                 [ Contact Us ]

────────────────────────────────────────────
✓ Evidence-grade traceability
✓ Auditable calculations
✓ Configurable processing
✓ Carbon reporting
```

Prices displayed here must come from the published commercial configuration/API.

No price should be hard-coded into the frontend.

---

# 18. Public Pricing Page Requirements

The public pricing surface should support:

- published plans;
- current published prices;
- monthly/annual toggle where available;
- feature comparison;
- included limits;
- add-on information where appropriate;
- enterprise/contact route;
- FAQ;
- legal/commercial disclosures;
- sign-in;
- sign-up;
- CTA.

Unpublished, retired, internal, or test plans must not appear publicly.

---

# 19. Signup Flow

```text
Public Pricing
      │
      ▼
[ Get Started ]
      │
      ▼
Create Account
      │
      ▼
Create/Select Organization
      │
      ▼
Confirm Plan
      │
      ▼
Checkout
```

The backend must revalidate the selected plan and price at every commercially meaningful boundary.

---

# 20. Checkout UX

```text
Checkout
┌──────────────────────────────────────────────┐
│ Your subscription                            │
├──────────────────────────────────────────────┤
│ Professional                                │
│ Billing: Monthly                             │
│                                              │
│ Current configured price                    │
│ £XX.XX                                       │
│                                              │
│ VAT/tax: calculated according to policy      │
│ Total: £XX.XX                                │
│                                              │
│ Payment                                     │
│ [ Provider-controlled checkout ]             │
│                                              │
│ [ Pay & Subscribe ]                          │
└──────────────────────────────────────────────┘
```

### Security rule

The displayed amount is not trusted.

Before creating the checkout session:

```text
request
  → validate plan
  → resolve version
  → resolve price
  → validate currency/interval
  → create provider session
```

---

# 21. Payment Provider Abstraction

CarbonTally must not architecturally depend on Stripe as the only possible provider.

Conceptually:

```text
                 CarbonTally
                     │
             Payment Provider
                Abstraction
                     │
          ┌──────────┴──────────┐
          │                     │
       Stripe              Provider B
          │                     │
       checkout              checkout
       webhooks              webhooks
```

The initial provider may be Stripe or another selected provider.

The Platform Admin should be able to select the active provider from supported providers.

---

# 22. Admin Payment Provider UX

```text
Platform Admin
Commercial
 └── Payment Providers

┌─────────────────────────────────────────────┐
│ Payment Providers                           │
├─────────────────────────────────────────────┤
│                                             │
│ Active Provider                             │
│ [ Stripe ▼ ]                                │
│                                             │
│ Providers                                   │
│                                             │
│ ● Stripe                                    │
│   Status: Connected                         │
│   [ Configure ] [ Test Connection ]         │
│                                             │
│ ○ Provider B                                │
│   Status: Not configured                    │
│   [ Configure ]                             │
│                                             │
│ [ Save Active Provider ]                    │
└─────────────────────────────────────────────┘
```

Provider secrets must be stored securely and never rendered back in plaintext.

Provider configuration must be permission-restricted and audited.

---

# 23. Provider Interface

The implementation should expose a provider-neutral internal contract sufficient for:

- create checkout session;
- create/update subscription where supported;
- cancel subscription;
- retrieve subscription;
- retrieve payment status;
- process webhook/event;
- invoice/receipt lookup where supported;
- refund/credit operations where authorized;
- customer/payment-method operations where supported.

Provider-specific capabilities must be represented explicitly rather than assumed to exist universally.

---

# 24. Webhooks and Subscription State

Provider events must not directly become unrestricted application state.

Conceptually:

```text
Provider Event
      │
      ▼
Webhook Authentication
      │
      ▼
Event Validation
      │
      ▼
Idempotency Check
      │
      ▼
Map Provider Event
      │
      ▼
Update CarbonTally Subscription State
      │
      ▼
Entitlement Re-resolution
      │
      ▼
Audit Event
```

Webhook processing must be idempotent.

---

# 25. Subscription Lifecycle

The module should support lifecycle states already compatible with CarbonTally's architecture.

Potential states include:

- trialing;
- active;
- past_due;
- cancelled;
- expired/suspended where applicable.

Exact state semantics must reuse the existing billing model unless discovery identifies a justified gap.

---

# 26. Trial Configuration

Trials should be configurable rather than hard-coded.

Admin may eventually configure:

```text
Trial
────────────────────────
Enabled:       [ ✓ ]
Duration:      [ 14 ] days
Eligible:      [ New customers ]
Features:      [ Selected plan ]
Payment method required:
               [ No ▼ ]
```

The system must support disabling trials.

Trial values must not be silently invented during implementation.

---

# 27. Upgrade / Downgrade

The product must support configurable commercial rules for:

### Upgrade

Potentially:

- immediate;
- prorated;
- next-cycle.

### Downgrade

Potentially:

- end of current period;
- immediate with credit;
- restricted where limits conflict.

The exact rule must be configured/approved before implementation.

The system must preserve entitlement consistency throughout the transition.

---

# 28. Cancellation / Reactivation

Customer UX:

```text
Subscription
──────────────────────────────
Status: ACTIVE

[ Cancel Subscription ]

Cancellation
──────────────────────────────
Your access remains available until:
DD MMM YYYY

Reason (optional)
[________________________]

[ Confirm Cancellation ]
[ Keep Subscription ]
```

Reactivation should be available where the provider/subscription lifecycle supports it.

Data-retention rules must be separately defined and must not be invented from this specification.

---

# 29. Customer Subscription Portal

```text
Customer
 └── Settings
      └── Subscription

┌──────────────────────────────────────────────┐
│ Subscription                                 │
├──────────────────────────────────────────────┤
│ Plan: Professional                           │
│ Status: ACTIVE                               │
│ Billing: Monthly                             │
│ Price: £XX / month                           │
│ Next billing date: DD MMM YYYY               │
│                                              │
│ [ Change Plan ]                              │
│ [ Manage Payment ]                           │
│ [ View Invoices ]                            │
│ [ Cancel ]                                   │
├──────────────────────────────────────────────┤
│ Included Usage                               │
│ Documents      ███████░░░  70%               │
│ Users          ██░░░░░░░░  20%               │
│ Entities       █████░░░░░  50%               │
└──────────────────────────────────────────────┘
```

The exact usage dimensions depend on the configured plan.

---

# 30. Customer Billing History

```text
Billing
─────────────────────────────────────────────
Date          Description          Amount

01 Oct 2026   Professional         £XX.XX
01 Sep 2026   Professional         £XX.XX
01 Aug 2026   Professional         £XX.XX

[ View Invoice ] [ Download ]
```

Historical invoice information must come from authoritative CarbonTally/provider records.

---

# 31. Platform Admin Subscription Management

```text
Platform Admin
 └── Subscriptions

Search [________________]

Customer          Plan          Status
────────────────────────────────────────────
Acme Ltd          Professional  ACTIVE
Beta Ltd          Starter       TRIAL
Gamma Ltd         Business      PAST_DUE

[ View ]
```

Detail:

```text
Customer: Acme Ltd
────────────────────────────────────────────
Subscription ID: ...
Plan: Professional
Version: 3
Price: £XX/month
Status: ACTIVE
Provider: Stripe
Provider ID: ...

Entitlements
✓ Scope 1
✓ Scope 2
✓ Scope 3
✓ Evidence Chain
✓ Manual Processing

[ View Audit ]
[ View Billing ]
```

---

# 32. Admin Commercial Control Plane

The Admin module should have a coherent structure:

```text
Platform Admin
────────────────────────────────────────
Commercial
 ├── Plans
 ├── Prices
 ├── Features
 ├── Limits
 ├── Add-ons
 ├── Promotions
 └── Payment Providers

Subscriptions
 ├── Customers
 ├── Active
 ├── Trial
 ├── Past Due
 └── Cancelled

Billing
 ├── Invoices
 ├── Payments
 ├── Refunds/Credits
 └── Events

Manual Processing
 ├── Coverage
 ├── Capacity
 └── Processing Entities
```

The actual navigation should reuse the existing Admin/Operations architecture where possible.

---

# 33. Plan Versioning UX

```text
Professional
──────────────────────────────────────────
Versions

v1    £79/mo    Retired
v2    £89/mo    Existing customers
v3    £99/mo    CURRENT

[ Create New Version ]

New Version
──────────────────────────────────────────
Copy from: [ v3 ▼ ]

Price:
Monthly [ £____ ]
Annual  [ £____ ]

Effective:
[ Immediately / Scheduled ]

[ Save Draft ]
[ Publish ]
```

Publishing a new version must be auditable.

---

# 34. Commercial Configuration Safety

Admin configuration must validate:

- price >= 0;
- supported currency;
- supported billing interval;
- valid plan state transitions;
- valid feature keys;
- valid limits;
- compatible provider capability;
- duplicate prevention;
- effective dates;
- required fields.

Invalid commercial configurations must not become purchasable.

---

# 35. Entitlement Resolution

There must be one authoritative entitlement-resolution path.

Conceptually:

```text
Request
   │
   ▼
Organization
   │
   ▼
Active Subscription(s)
   │
   ├── Direct entitlement
   │
   └── Sponsored entitlement where applicable
   │
   ▼
Plan / Version / Add-ons
   │
   ▼
Effective Entitlements
   │
   ▼
Feature / Limit Decision
```

No individual frontend component should independently infer entitlement from plan names.

---

# 36. Manual Processing Effective Entitlement

For Manual Processing:

```text
effective_manual_processing
=
direct_subscription_entitlement
OR
consultant_sponsored_entitlement
```

Then:

```text
effective_manual_processing
AND
FIN-06 governance enabled
```

determines operational availability.

Existing F-5/F-6 decisions remain:

- preserve an existing open human/internal-staff assignment rather than silently superseding it;
- resolve the requested organization/scope correctly rather than relying on `organizations[0]`.

---

# 37. Security

The module must preserve:

- organization-scoped authorization;
- existing RLS;
- service-role boundaries;
- role/permission checks;
- server-side commercial validation;
- server-side price resolution;
- provider webhook authentication;
- webhook idempotency;
- audit logging;
- secure provider secrets;
- no client-controlled entitlement;
- no client-controlled price;
- no client-controlled subscription status.

---

# 38. Auditability

Audit events should capture, where applicable:

- actor;
- timestamp;
- organization;
- object;
- previous value;
- new value;
- reason;
- provider;
- provider event ID;
- correlation/reference ID.

Commercial configuration changes must be distinguishable from subscription lifecycle events.

---

# 39. Admin Overrides

Temporary commercial/entitlement overrides may be supported only if explicitly authorized and audited.

Conceptually:

```text
Temporary Override
────────────────────────────────
Organization: Acme Ltd
Feature: Manual Processing
Enabled: YES
Expires: DD MMM YYYY HH:MM
Reason: [_____________________]

[ Apply Override ]
```

Overrides must never silently rewrite the underlying plan.

The exact override model requires PO/security approval before implementation.

---

# 40. Discounts / Promotions

The module should be capable of configurable promotional rules.

Potential configuration:

```text
Promotion
──────────────────────────────
Code: SAVE20
Discount: [ % / fixed ]
Value: [ ____ ]
Start: [ date ]
End: [ date ]
Usage limit: [ ____ ]
Eligible plans: [ ... ]
```

Provider support and accounting implications must be verified before implementation.

---

# 41. Tax / VAT

Tax handling must be designed as a commercial capability, not hard-coded into UI.

The final tax implementation must account for:

- customer billing jurisdiction;
- B2B/B2C classification where applicable;
- provider capabilities;
- tax identification;
- invoice requirements.

No specific tax rate is mandated by this document.

---

# 42. Public vs Authenticated Pricing

Public pricing may show:

- published plan names;
- published prices;
- public feature summaries.

Authenticated customers may see:

- their current plan;
- personalized upgrade/downgrade options;
- applicable discounts;
- effective entitlements;
- usage.

Consultants may additionally see their firm's commercial coverage.

Customers must not see consultant firm's commercial arrangements.

---

# 42. Navigation Specification

## Public

```text
Home
Product
How It Works
Pricing
Resources
Contact
Login
Get Started
```

## Customer

```text
Dashboard
Documents
Emissions
Reports
Settings
 ├── Organization
 ├── Users
 ├── Subscription
 └── Billing
```

## Consultant

```text
Dashboard
Clients
Documents / Work
Reports
Subscription
 ├── Firm Plan
 ├── Manual Processing Coverage
 └── Billing
```

## Platform Admin

```text
Dashboard
Organizations
Users
Commercial
 ├── Plans
 ├── Prices
 ├── Features
 ├── Limits
 ├── Add-ons
 └── Payment Providers
Subscriptions
Billing
Manual Processing
Audit
```

---

# 43. Empty / Error States

The UI must explicitly handle:

### No subscription

```text
No active subscription

Choose a plan to unlock additional CarbonTally capabilities.

[ View Plans ]
```

### Payment failure

```text
Payment requires attention

Your subscription could not be renewed.

[ Update Payment Method ]
```

### Provider unavailable

```text
Checkout temporarily unavailable

Please try again later or contact support.
```

### Plan unavailable

```text
This plan is no longer available.

Choose from the currently available plans.
```

### Sponsored Manual Processing unavailable

```text
Manual Processing
Not currently included through your consultant coverage.
```

No UI should imply entitlement merely because a feature exists in the application.

---

# 44. Accessibility and UX

All surfaces should:

- use existing CarbonTally design system/components;
- support keyboard navigation;
- expose meaningful labels;
- provide clear validation errors;
- distinguish current vs proposed changes;
- avoid relying solely on colour;
- make pricing and renewal terms explicit;
- show confirmation before destructive actions.

---

# 45. API Principles

The API must support, as required by the actual architecture:

- public published plan retrieval;
- authenticated plan retrieval;
- current subscription retrieval;
- checkout-session creation;
- subscription lifecycle operations;
- invoice/payment history;
- Admin plan management;
- Admin price/version management;
- Admin provider management;
- entitlement resolution;
- usage retrieval;
- consultant coverage.

Existing endpoints must be reused where adequate.

Do not create duplicate endpoints merely to match this conceptual list.

---

# 46. Database Principles

The database must remain the source of truth for:

- published plan configuration;
- prices;
- plan versions;
- feature entitlements;
- limits;
- subscription state;
- commercial configuration;
- audit records.

Provider IDs may be stored as external references but must not replace CarbonTally's own commercial state.

---

# 47. Payment Provider Data

Store only what is required for integration and reconciliation.

Provider secrets must not be stored in ordinary customer-facing tables or exposed through APIs.

Provider identifiers should be treated as references, not authorization grants.

---

# 48. Idempotency

The following operations must be designed for idempotency where applicable:

- checkout creation;
- subscription activation;
- webhook handling;
- payment event processing;
- invoice event processing;
- cancellation/reactivation events.

Duplicate provider events must not create duplicate CarbonTally subscriptions or entitlements.

---

# 49. Customer Data Preservation

Changing plans must not delete customer carbon data merely because an entitlement changes.

Feature restriction and data retention are separate concerns.

If a customer downgrades below an existing usage/feature limit, the system must have an explicit product rule for existing data. It must not silently delete data.

---

# 50. Reporting and Analytics

The module should eventually provide:

- active subscriptions;
- new subscriptions;
- upgrades;
- downgrades;
- cancellations;
- trial conversion;
- recurring revenue;
- plan distribution;
- usage;
- entitlement utilization;
- payment failures.

Analytics must not be allowed to become a dependency for core entitlement enforcement.

---

# 51. Market-Informed Product Principles

External competitive research suggests that CarbonTally can differentiate through:

- transparent configurable pricing;
- evidence-grade traceability;
- accessible entry points;
- deeper processing/review capability;
- audit-ready evidence;
- consultant ecosystem;
- configurable services.

The market research does **not** determine CarbonTally's final pricing or plan structure.

---

# 52. Proposed Commercial Configuration Example

This is illustrative only:

```text
Plan Catalogue
──────────────────────────────────────────
Starter
  Monthly: £X
  Annual:  £Y

Professional
  Monthly: £X
  Annual:  £Y

Business
  Monthly: £X
  Annual:  £Y

Enterprise
  Pricing: Custom
```

The actual names, values, limits, and features are configurable.

---

# 53. Configuration vs Code Boundary

### Should normally require Admin configuration

- price;
- currency where supported;
- billing interval;
- plan visibility;
- plan active/inactive;
- feature enabled/disabled;
- quota/limit;
- add-on price;
- trial duration;
- promotion;
- active payment provider;
- commercial display order.

### Should require engineering/product authorization

- introducing a new entitlement type;
- changing authorization semantics;
- changing RLS;
- changing subscription ownership model;
- changing payment-provider interface;
- changing accounting semantics;
- changing Manual Processing governance;
- introducing a new billing architecture.

This prevents ordinary pricing operations from requiring deployments while preserving architecture governance.

---

# 54. Acceptance Scenarios

The eventual implementation must be independently verifiable against at least these scenarios:

1. Existing Customer Billing page is preserved and extended rather than replaced without justification.
2. Existing Billing sections are mapped to the new commercial/usage/service model.
3. Admin creates a plan.
4. Admin publishes a plan.
3. Admin configures monthly price.
4. Admin configures annual price.
5. Public pricing retrieves current published prices.
6. Customer sees correct configured price.
7. Customer submits a manipulated client price.
8. Backend ignores manipulated price.
9. Backend resolves authoritative database price.
10. Checkout uses authoritative price.
11. Successful provider event activates subscription.
12. Duplicate webhook does not duplicate subscription.
13. Failed payment updates subscription appropriately.
14. Cancellation follows configured lifecycle.
15. Customer can view current subscription.
16. Customer can view billing history.
17. Admin can inspect subscription.
18. Admin can create a new plan version.
19. Existing subscription remains historically consistent.
20. New customers receive current commercial version.
21. Admin can configure feature entitlement.
22. Entitlement resolver reflects configured feature.
23. Admin can configure limits.
24. Server enforces configured limits.
25. Public site never exposes unpublished plans.
26. Unauthorized user cannot change commercial configuration.
27. Provider secrets are not exposed.
28. Admin can select an available payment provider.
29. Unsupported provider configuration fails safely.
30. Manual Processing direct entitlement works.
31. Consultant-sponsored Manual Processing works.
32. Selected-client capacity is enforced.
33. All-eligible coverage works.
34. Direct + sponsored entitlement resolves as OR.
35. Commercial entitlement remains separate from FIN-06 operational activation.
36. Existing open human/internal assignment is not silently superseded.
37. Requested organization scope is correctly resolved.
38. No duplicate subscription architecture is introduced.
39. Existing RLS remains effective.
40. Audit events identify commercial changes.

---

# 55. Required Verification Layers

Implementation verification should cover:

### Unit

- price resolution;
- plan version resolution;
- entitlement resolution;
- limit resolution;
- lifecycle transitions;
- provider mapping;
- idempotency.

### API

- authorization;
- price authority;
- checkout;
- subscription retrieval;
- Admin configuration;
- provider management.

### Database/RLS

- organization isolation;
- Admin-only commercial changes;
- customer isolation;
- consultant/client isolation.

### Integration

- payment-provider sandbox;
- webhook handling;
- subscription lifecycle;
- invoice/payment reconciliation.

### Browser/UI

- public pricing;
- signup;
- checkout;
- customer subscription;
- consultant coverage;
- Admin commercial configuration.

### Independent verification

CoStrict/OHD must verify against the approved specification independently of the implementer's report.

---

# 56. Implementation Phases

## S1 — Discovery and reconciliation

- complete CT-DISC-SUB-001;
- inventory the existing Customer Billing UI and its backend/API/database dependencies;
- explicitly classify existing Billing mode, Credits, Storage, Credit history, Assisted Processing, Managed Processing, and Orders;
- identify which existing Customer Billing capabilities are preserved, extended, deprecated, or replaced and why;
- inventory existing subscription architecture;
- identify gaps;
- map current APIs/UI/database.

## S2 — Commercial configuration foundation

- configurable plans;
- prices;
- versions;
- features;
- limits;
- Admin UI.

## S3 — Customer subscription experience

- public pricing;
- signup;
- checkout;
- customer Subscription/Billing UI.

## S4 — Provider and lifecycle

- provider abstraction;
- selected provider;
- checkout;
- webhooks;
- lifecycle;
- invoices.

## S5 — Consultant / Manual Processing integration

- firm subscription;
- sponsorship;
- selected/all coverage;
- capacity;
- entitlement integration.

## S6 — Hardening and analytics

- audit;
- usage;
- analytics;
- operational dashboards;
- failure handling.

Actual sequencing may change after discovery.

---

# 57. Open PO Decisions

The following are intentionally **NOT YET DECIDED** unless separately approved:

- final plan names;
- final plan count;
- final prices;
- final currencies;
- final limits;
- final trial policy;
- final discount policy;
- tax implementation/provider;
- payment provider(s) to launch with;
- payment-provider priority;
- upgrade proration;
- downgrade semantics;
- refund policy;
- failed-payment grace period;
- data-retention policy;
- enterprise custom pricing model;
- add-on catalogue;
- usage-overage policy;
- whether customers may self-serve all plan changes;
- whether annual plans receive discounts;
- exact analytics KPIs.

The **capability to configure these values** is the product requirement. Their final commercial values remain PO decisions.

---

# 58. Existing Manual Processing Decisions That Remain Authoritative

This specification does not reopen:

- direct customer subscription entitlement;
- consultant-sponsored entitlement;
- consultant firm organization as sponsorship subscription owner;
- SELECTED_CLIENTS;
- ALL_ELIGIBLE_CLIENTS;
- direct OR sponsored entitlement;
- separation of commercial entitlement from FIN-06;
- no automatic PE assignment;
- preservation of open human/internal assignment;
- correct requested-scope resolution;
- canonical `features.manual_processing.enabled`;
- backward-compatible `assisted_processing_available`.

---

# 59. UI/UX Ownership

This specification is the authoritative product/UX starting point.

Implementation responsibilities:

**Product specification / ASCII UX:** PO + CarbonTally product design process.

**Implementation:** Cline/development.

**Independent verification:** CoStrict/OHD.

The implementer must not reinterpret unresolved commercial decisions.

---

# 60. Definition of Done for CT-SUB-001

The product specification is ready for implementation authorization only when:

- current architecture discovery is reconciled;
- all material architecture conflicts are resolved;
- commercial decisions are explicitly marked;
- PO approves the final document;
- ASCII UI/UX is accepted;
- acceptance scenarios are accepted;
- implementation boundaries are clear;
- security/RLS boundaries are clear;
- provider abstraction is clear;
- database-authoritative pricing is explicit;
- Manual Processing integration is preserved.

---

# 61. Final Product Principle

CarbonTally should not require a developer deployment merely because the business wants to:

- change a plan price;
- enable/disable a plan;
- change a configurable limit;
- change a feature entitlement;
- introduce a billing interval already supported by the implementation;
- change the active supported payment provider;
- configure a supported trial;
- modify supported commercial configuration.

Instead:

```text
                 PLATFORM ADMIN
                       │
                       ▼
             COMMERCIAL CONFIGURATION
                       │
                       ▼
              VALIDATED DATABASE
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   PUBLIC/CUSTOMER UI       SERVER ENTITLEMENTS
          │                         │
          ▼                         ▼
      CHECKOUT              PRODUCT ENFORCEMENT
          │
          ▼
   PAYMENT PROVIDER
          │
          ▼
      WEBHOOKS
          │
          ▼
CARBONTALLY SUBSCRIPTION STATE
```

**The database/configuration is authoritative for commercial values.  
The backend is authoritative for price and entitlement decisions.  
The payment provider is authoritative for payment execution.  
CarbonTally remains authoritative for application access and product entitlement.**

---

## 62. Governance Conclusion

**CT-SUB-001 — PROPOSED**

This document is **not implementation authorization**.

Next action:

> Complete `CT-DISC-SUB-001`, reconcile the discovered implementation against CT-SUB-001, resolve any gaps/PO decisions, then submit the reconciled document for PO approval.

**Target implementation boundary after approval:**

> `CT-SUB-001 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION`

No production migration, production payment configuration, deployment, commit, or push is authorized by this document.
