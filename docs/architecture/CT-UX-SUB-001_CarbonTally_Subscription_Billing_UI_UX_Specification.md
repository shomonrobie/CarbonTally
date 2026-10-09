# CT-UX-SUB-001 — CarbonTally Subscription & Billing UI/UX Specification

**Document ID:** CT-UX-SUB-001  
**Version:** 0.1  
**Date:** 2026-10-04  
**Status:** **PROPOSED — PO REVIEW REQUIRED — NOT YET AUTHORIZED FOR IMPLEMENTATION**  
**Parent Product Specification:** `CT-SUB-001 — CarbonTally Configurable Subscription & Billing Product Specification`

---

## 1. Purpose

This document defines the intended **user experience and information architecture** for CarbonTally's configurable Subscription & Billing module.

It covers the complete commercial journey across:

1. Public website / pricing
2. Sign-up
3. Plan selection
4. Checkout
5. Customer Subscription & Billing
6. Consultant subscription and Manual Processing coverage
7. Platform Admin commercial configuration
8. Platform Admin subscription/billing operations
9. Payment-provider configuration
10. Billing/invoice history
11. Upgrade/downgrade/cancellation
12. Trial/payment-failure states
13. Empty/error states
14. Mobile/responsive behavior
15. Accessibility
16. Trust, transparency, and confirmation UX

The objective is not merely to expose billing controls. The objective is to make CarbonTally's commercial experience **clear, trustworthy, predictable, low-friction, and easy to self-serve**.

---

# 2. Design Principles

## 2.1 Clarity before conversion

The customer must understand:

- what they are buying;
- what is included;
- what it costs;
- how often they will be charged;
- what happens at renewal;
- what limits apply;
- what happens if they upgrade/downgrade/cancel.

Do not optimize for conversion by hiding commercial information.

## 2.2 One commercial truth

All visible plan/pricing information must originate from the same published commercial configuration used by the backend.

```text
ADMIN CONFIGURATION
       ↓
PUBLISHED COMMERCIAL CATALOGUE
       ↓
PUBLIC PRICING
       ↓
CUSTOMER PLAN SELECTION
       ↓
SERVER PRICE RE-RESOLUTION
       ↓
CHECKOUT
```

## 2.3 Progressive disclosure

Do not present every technical billing detail on the first screen.

Show:

1. essential decision information first;
2. important details next;
3. advanced/legal/provider details on demand.

## 2.4 No surprise charges

The user should always be able to answer:

> "What will I pay now, and what will I pay later?"

before confirming purchase.

## 2.5 Self-service first

Customers should be able to perform normal subscription tasks without contacting CarbonTally:

- view plan;
- view price;
- view renewal;
- update payment method;
- view invoices;
- change plan where allowed;
- cancel where allowed;
- reactivate where allowed.

This aligns with current SaaS billing practice and reduces support dependency.

## 2.6 Existing-first

The existing Demo Lab customer Billing page is a real product surface and must be **extended rather than blindly replaced**.

Current visible sections include:

- Plan
- Billing mode
- Credits
- Storage
- Credit history
- Assisted Processing estimate
- Managed Processing
- Orders

These existing concepts must be mapped to the target commercial architecture before redesign.

---

# 3. Industry UX Basis

The UX direction is informed by established SaaS subscription research and billing guidance.

Baymard's SaaS research identifies the pricing/plan matrix as a central decision surface and emphasizes clear feature explanations, scannability, and a holistic understanding of the service. citeturn0search0turn0search2

Baymard also identifies the sign-up and checkout flow, plan matrix, and account management as major SaaS UX areas requiring careful design. citeturn0search4

Current Stripe billing guidance emphasizes simple billing pages, transparent costs/currency, mobile usability, trust cues, simple checkout, clear CTAs, graceful errors, and clear order review. citeturn0search7turn0search15

Stripe's current self-service guidance also treats plan changes, cancellation, payment-method updates, billing history, and subscription details as normal self-service capabilities. citeturn0search1

CarbonTally should apply these principles while adapting them to:

- evidence-grade carbon accounting;
- organization-scoped subscriptions;
- consultant-sponsored Manual Processing;
- configurable commercial plans;
- CarbonTally's existing Billing page;
- the existing Admin/Operations architecture.

---

# 4. User Roles and Commercial Surfaces

| Persona | Primary commercial surface |
|---|---|
| Public visitor | Pricing / plan comparison |
| New customer | Signup → plan selection → checkout |
| Existing customer | Subscription & Billing |
| Consultant | Firm Subscription & Coverage |
| Platform Admin | Commercial configuration |
| Platform Owner | Full commercial oversight |
| Support/authorized staff | Subscription operations within permissions |

A customer must never see another organization's subscription or consultant firm's commercial arrangement.

---

# 5. Global Information Architecture

## 5.1 Public

```text
CarbonTally
├── Product
├── How It Works
├── Evidence & Auditability
├── Integrations
├── Pricing
├── Resources
├── Contact
├── Login
└── Get Started
```

## 5.2 Customer

```text
Dashboard
Documents
Processing
Review & Approve
Emissions
Reports
Issues
Organisation
Messaging
Insight

Settings
├── Organization
├── Users
├── Subscription
└── Billing
```

Where the existing product currently has a single Billing navigation item, the UI may retain that entry and evolve it into the broader Subscription & Billing surface.

## 5.3 Consultant

```text
Dashboard
Clients
Client Work
Reports
Messaging

Settings
├── Firm
├── Members
├── Subscription
│   ├── Plan
│   ├── Manual Processing Coverage
│   └── Usage
└── Billing
```

## 5.4 Platform Admin

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
├── Promotions
└── Payment Providers

Subscriptions
Billing
Manual Processing
Audit
```

---

# 6. Public Pricing Experience

## 6.1 Pricing page objectives

The pricing page must let a prospective customer quickly answer:

- Which plan is appropriate?
- What does it include?
- What does it cost?
- What limits apply?
- What happens if I choose annual vs monthly?
- Can I change plans later?
- What support/processing services are included?

## 6.2 Recommended layout

```text
┌──────────────────────────────────────────────────────────────┐
│ CarbonTally logo                         Login   Get Started │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Evidence-grade carbon accounting, without enterprise        │
│ complexity.                                                  │
│                                                              │
│              [ MONTHLY ]   [ ANNUAL — SAVE X% ]             │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ STARTER             PROFESSIONAL          BUSINESS           │
│ £XX / month         £XX / month           £XX / month        │
│                                                              │
│ For...               For...                For...             │
│                                                              │
│ ✓ Feature            ✓ Feature             ✓ Feature         │
│ ✓ Feature            ✓ Feature             ✓ Feature         │
│ ○ Limited            ✓ Feature             ✓ Feature         │
│                                                              │
│ [Get Started]       [Get Started]         [Get Started]      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ ENTERPRISE                                                   │
│ Custom commercial configuration                              │
│ [Talk to CarbonTally]                                       │
└──────────────────────────────────────────────────────────────┘
```

## 6.3 Recommended UX details

- Use a monthly/annual switch.
- Clearly label the billing interval.
- If annual savings are configured, show the saving transparently.
- Highlight one recommended plan only when there is a genuine product basis.
- Avoid hiding important differences behind hover-only interactions.
- Provide concise explanations for technical features.
- Link complex features to deeper product pages.
- Make limits scannable.
- Include a full comparison below the summary cards.

---

# 7. Plan Comparison Matrix

```text
Feature                    Starter    Professional    Business
───────────────────────────────────────────────────────────────
Scope 1                    ✓          ✓               ✓
Scope 2                    ✓          ✓               ✓
Scope 3                    —          ✓               ✓
Evidence chain             ✓          ✓               ✓
Calculation snapshots      —          ✓               ✓
Manual Processing           —          ✓               ✓
API access                  —          —               ✓
Documents/month             X          X               X
Users                       X          X               X
Entities                    X          X               X
Support                    Standard   Priority        Priority+
```

## UX rules

Every ambiguous feature should have:

- short explanation;
- tooltip/popover;
- or link to detailed documentation.

Avoid vague labels such as:

`Advanced analytics`

Prefer:

`Multi-year emissions reporting`

---

# 8. Plan Recommendation

Where appropriate:

```text
Most popular
────────────────
PROFESSIONAL
Best for organizations
that need evidence-grade
accounting and assisted
processing.

[Choose Professional]
```

The recommendation must be driven by product/commercial configuration, not hard-coded marketing text.

---

# 9. Plan Details Drawer

Clicking a feature or `View details` should open:

```text
Professional
────────────────────────────────────
Evidence Chain

What it means
Trace every reported value to
its source document and calculation
provenance.

Included
✓ Source linkage
✓ Calculation provenance
✓ Evidence history

[Close]
```

This reduces ambiguity without overcrowding the pricing matrix.

---

# 10. Public FAQ

Recommended topics:

- What is included?
- Can I change plans?
- Can I pay annually?
- What happens if I exceed a limit?
- Can I cancel?
- What happens to my data after cancellation?
- Can a consultant purchase Manual Processing for my organization?
- What payment methods are supported?
- Are taxes/VAT included?
- Can Enterprise plans be customized?

Answers must be generated from approved commercial policy/configuration.

---

# 11. Signup Experience

## 11.1 Principle

Avoid unnecessary fields before the user has committed.

Recommended flow:

```text
Pricing
  ↓
Choose plan
  ↓
Create account
  ↓
Create organization
  ↓
Confirm plan
  ↓
Checkout
  ↓
Welcome / onboarding
```

## 11.2 Signup UI

```text
Create your CarbonTally account
────────────────────────────────────

Work email
[____________________________]

Password
[____________________________]

Organization name
[____________________________]

Country
[ Select ▼ ]

[ Continue ]

Already have an account? Sign in
```

Only collect additional information when necessary.

---

# 12. Plan Confirmation Before Checkout

```text
Confirm your plan
────────────────────────────────────
Professional

Billing
○ Monthly
● Annual

Price
£XX / year

Equivalent
£XX / month

Next renewal
DD MMM YYYY

Included
✓ Evidence-grade traceability
✓ Scope 1–3
✓ X documents/month
✓ X users

[ Back ]             [ Continue to Checkout ]
```

The user must not be surprised by the plan selected on the next screen.

---

# 13. Checkout

## 13.1 Preferred structure

```text
Checkout
─────────────────────────────────────────────────

YOUR PLAN                    PAYMENT
────────────────────         ────────────────────
Professional                 Provider checkout
Annual                       fields
£XX / year
                             Billing details
Includes:
✓ Feature A                 [ ... ]
✓ Feature B
✓ Feature C                 [ ... ]

─────────────────────────────────────────────────
Subtotal                       £XX
Tax/VAT                        £XX
─────────────────────────────────────────────────
Total today                   £XX

Renews on DD MMM YYYY at £XX

☐ I agree to Terms and Billing Terms

[ Pay & Subscribe ]
```

## 13.2 Critical price behavior

The browser must never submit an authoritative price.

```text
Client
  │
  │ plan_id + interval
  ▼
Backend
  │
  ├── resolve published plan
  ├── resolve current price
  ├── validate availability
  ├── calculate commercial/tax data
  └── create provider checkout
  ▼
Provider
```

---

# 14. Checkout Trust UX

Before payment, clearly show:

- plan;
- billing interval;
- amount due today;
- tax/VAT where applicable;
- renewal date;
- renewal amount;
- discounts;
- trial terms;
- cancellation terms;
- payment provider/security indication;
- support route.

Do not bury renewal information in small text.

---

# 15. Payment Failure UX

```text
Payment could not be completed
────────────────────────────────────

We couldn't complete your payment.

Your subscription has not been activated.

Reason:
Your payment method was declined.

[ Try Again ]
[ Use Another Payment Method ]

Need help?
Contact CarbonTally Support
```

Do not expose provider-specific technical error details unnecessarily.

---

# 16. Successful Purchase

```text
You're subscribed
────────────────────────────────────

Professional
£XX / month

Next renewal
DD MMM YYYY

Your account is ready.

[ Go to CarbonTally ]

You'll receive your billing confirmation
and invoice by email.
```

If provider confirmation is asynchronous, show:

```text
Payment received
Subscription activation pending confirmation.

[ View Subscription ]
```

---

# 17. Customer Subscription Overview

The existing customer Billing page should evolve into:

```text
Subscription & Billing
─────────────────────────────────────────────

CURRENT PLAN
┌─────────────────────────────────────────────┐
│ Professional                               │
│ ACTIVE                                      │
│ £XX / month                                 │
│ Renews DD MMM YYYY                          │
│                                             │
│ [ Change Plan ] [ Manage Payment ]          │
└─────────────────────────────────────────────┘

USAGE
Documents       ███████░░░ 70%
Users           ███░░░░░░░ 30%
Entities        █████░░░░░ 50%

BILLING
Next invoice    DD MMM YYYY
Payment method  •••• 4242

[ View invoices ]
```

---

# 18. Existing Billing Page Integration

The current page contains:

```text
Plan
Billing mode
Credits
Storage
Credit history
Assisted Processing estimate
Managed Processing
Orders
```

Target mapping:

```text
Subscription
 └── Plan

Billing
 ├── Billing mode
 ├── Payment method
 ├── Renewal
 └── Invoices

Usage
 ├── Credits
 ├── Storage
 └── Configured limits

Processing Services
 ├── Assisted Processing
 ├── Managed Processing
 └── Orders
```

The exact semantics must be verified by CT-DISC-SUB-001.

---

# 19. Customer Usage Experience

Usage should not be merely a percentage bar.

```text
Documents
────────────────────────────────
Used: 700
Included: 1,000

██████████████░░░░░░ 70%

700 / 1,000

You have 300 documents remaining
this billing period.

[ View usage ]
```

If the limit is near:

```text
Approaching your document limit

You've used 90% of this month's
included documents.

[ View Plans ]
```

Avoid alarmist language.

---

# 20. Customer Plan Change

```text
Change your plan
────────────────────────────────────

CURRENT
Professional
£XX/month

AVAILABLE

Starter
£XX/month
[Choose]

Business
£XX/month
[Choose]

────────────────────────────────────

Change effective:
[ Immediately / Next renewal ]

What changes?
+ Feature X
+ Limit increases
- Feature Y

Estimated charge today: £XX

[ Confirm Change ]
```

The UI must explicitly show the effective date and financial impact.

---

# 21. Upgrade Confirmation

```text
Confirm upgrade
────────────────────────────────────

Professional → Business

Effective:
Immediately

Charge today:
£XX

Next renewal:
£XX on DD MMM YYYY

You will gain:
✓ Feature A
✓ Feature B
✓ Higher document limit

[ Confirm Upgrade ]
[ Cancel ]
```

---

# 22. Downgrade Confirmation

Downgrades require extra clarity:

```text
Confirm downgrade
────────────────────────────────────

Business → Professional

Effective:
At end of current billing period

Current plan remains active until:
DD MMM YYYY

At renewal:
• Limit changes from X → Y
• Feature A will no longer be available

Your existing data will not be deleted.

[ Confirm Downgrade ]
[ Keep Business ]
```

The exact commercial behavior must follow approved policy.

---

# 23. Cancellation UX

Cancellation must not be dark-patterned.

```text
Cancel subscription
────────────────────────────────────

Your subscription will remain active
until DD MMM YYYY.

After cancellation:
• Your plan will not renew.
• Your existing data remains subject
  to CarbonTally's data-retention policy.
• Some features may become unavailable.

Why are you cancelling? (optional)
○ Too expensive
○ Not using enough
○ Missing a feature
○ Moving to another service
○ Other

[ Keep Subscription ]    [ Cancel Subscription ]
```

---

# 24. Reactivation

```text
Subscription cancelled
────────────────────────────────────

Your plan remains active until:
DD MMM YYYY

You can reactivate before cancellation
takes effect.

[ Reactivate Subscription ]
```

---

# 25. Invoice History

```text
Billing History
──────────────────────────────────────────────

Date          Description       Amount   Status
──────────────────────────────────────────────
01 Oct 2026   Professional      £XX      Paid
01 Sep 2026   Professional      £XX      Paid
01 Aug 2026   Professional      £XX      Paid

[ View ] [ Download ]
```

Filters:

- date;
- status;
- type.

---

# 26. Payment Method

```text
Payment Method
────────────────────────────────

Primary
Visa •••• 4242
Expires 08/28

[ Update Payment Method ]

Billing address
Company Name
Address
Country

[ Edit Billing Details ]
```

Never display sensitive payment credentials.

---

# 27. Billing Alerts

Customers should receive contextual in-product notices for:

- upcoming renewal;
- payment failure;
- expiring payment method;
- approaching usage limit;
- subscription cancellation scheduled;
- trial ending;
- plan change pending.

Alerts should link directly to the required action.

---

# 28. Consultant Subscription Overview

The consultant workspace requires a dedicated commercial surface.

```text
Consultant Workspace
─────────────────────────────────────────────
Subscription

FIRM PLAN
┌─────────────────────────────────────────────┐
│ Business                                    │
│ ACTIVE                                      │
│ £XX / month                                 │
│                                             │
│ [ Manage Plan ] [ Billing ]                 │
└─────────────────────────────────────────────┘

MANUAL PROCESSING COVERAGE
┌─────────────────────────────────────────────┐
│ SELECTED CLIENTS                            │
│ Purchased capacity: 25                      │
│ Allocated: 18                               │
│ Available: 7                                │
│                                             │
│ [ Manage Client Coverage ]                  │
└─────────────────────────────────────────────┘
```

---

# 29. Consultant Coverage — Selected Clients

```text
Manual Processing Coverage
─────────────────────────────────────────────

Mode
● Selected clients
○ All eligible clients

Capacity
Purchased     25
Allocated     18
Available      7

Client                     Status
────────────────────────────────
Acme Ltd                   Covered
Beta Ltd                   Covered
Gamma Ltd                  Not covered
Delta Ltd                  Covered

[ Allocate Client ]
[ Release Allocation ]
```

Capacity availability must always be visible.

---

# 30. Consultant Coverage — All Eligible Clients

```text
Manual Processing Coverage
─────────────────────────────────────────────

Mode
○ Selected clients
● All eligible clients

Coverage
All eligible consultant-client
organizations are commercially covered.

Current eligible clients: 18

Former/terminated relationships
are not automatically covered.

[ Manage Coverage ]
```

The UI must clearly state that coverage does not automatically assign a Processing Entity.

---

# 31. Consultant Direct vs Sponsored View

A consultant should see firm commercial coverage.

A customer should see only the resulting effective entitlement.

Consultant:

```text
Client Coverage
Acme Ltd
────────────────────────────
Commercial source:
Sponsored by your firm

Manual Processing:
✓ Covered
```

Customer:

```text
Manual Processing
────────────────────────────
✓ Included for your organization

Coverage source:
Available through your consultant
arrangement.
```

Do not expose the consultant firm's pricing or capacity to the customer.

---

# 32. Platform Admin — Commercial Dashboard

```text
Platform Admin
─────────────────────────────────────────────

Commercial Overview

Active subscriptions     128
Trial subscriptions       14
Past due                   6
Cancelled this month      11

Plans
Starter                  42
Professional             61
Business                 20
Enterprise                5

[ Manage Plans ]
[ Manage Subscriptions ]
[ Billing ]
```

The exact metrics are configurable/product decisions.

---

# 33. Platform Admin — Plan Catalogue

```text
Commercial
 └── Plans

Plans
─────────────────────────────────────────────
Name             Status      Current Version
Starter          ACTIVE      v3
Professional     ACTIVE      v4
Business         ACTIVE      v2
Enterprise       ACTIVE      v5

[ Create Plan ]
```

---

# 34. Platform Admin — Plan Editor

```text
Edit Plan
─────────────────────────────────────────────

Identity
Name              [ Professional ]
Description       [ ... ]

Availability
Public            [ ✓ ]
Purchasable       [ ✓ ]
Status            [ ACTIVE ▼ ]

Pricing
Monthly           [ £______ ]
Annual            [ £______ ]

Features
☑ Scope 1
☑ Scope 2
☑ Scope 3
☑ Evidence Chain
☑ Manual Processing
☐ API

Limits
Documents/month  [ ______ ]
Users             [ ______ ]
Entities          [ ______ ]

[ Save Draft ]
[ Publish Version ]
```

---

# 35. Platform Admin — Feature Configuration

Features should be grouped by business meaning.

```text
Features
─────────────────────────────────────────────

Carbon Accounting
☑ Scope 1
☑ Scope 2
☑ Scope 3

Evidence
☑ Evidence Chain
☑ Calculation Snapshots
☐ Audit Export

Processing
☑ Assisted Processing
☑ Managed Processing
☑ Manual Processing

Integrations
☐ Xero
☐ QuickBooks
☐ API

[ Save ]
```

---

# 36. Platform Admin — Limits

```text
Limits
─────────────────────────────────────────────

Documents
Monthly limit      [ 1000 ]

Users
Included users     [ 20 ]

Entities
Included entities  [ 5 ]

API
Requests/month     [ 10000 ]

Unlimited:
[ Use blank / explicit unlimited control ]

[ Save ]
```

Unlimited must be represented explicitly in the data model.

---

# 37. Platform Admin — Price Versioning

```text
Professional
─────────────────────────────────────────────

Versions

v1   £79/month   Historical
v2   £89/month   Existing customers
v3   £99/month   CURRENT

[ Create New Version ]
```

Publishing a new version must require confirmation:

```text
Publish version v4?

This will make v4 the current commercial
configuration for new purchases.

Existing subscriptions:
[ Keep existing version ]

[ Cancel ] [ Publish ]
```

---

# 38. Platform Admin — Payment Providers

```text
Commercial
 └── Payment Providers

Active:
● Stripe

Configured:
● Stripe
○ Provider B

Stripe
Status: Connected

[ Test Connection ]
[ Configure ]
[ Set Active ]
```

Secrets are never shown after storage.

---

# 39. Platform Admin — Subscription Search

```text
Subscriptions
─────────────────────────────────────────────

Search [________________________]

Filters:
Plan [All ▼]
Status [All ▼]
Provider [All ▼]

Organization      Plan           Status
─────────────────────────────────────────────
Acme Ltd           Professional  ACTIVE
Beta Ltd           Starter       TRIAL
Gamma Ltd          Business      PAST_DUE

[ View ]
```

---

# 40. Platform Admin — Subscription Detail

```text
Acme Ltd
─────────────────────────────────────────────

Subscription
Plan: Professional
Version: 4
Status: ACTIVE
Billing: Monthly
Price: £XX
Provider: Stripe

Renewal
DD MMM YYYY

Entitlements
✓ Scope 1
✓ Scope 2
✓ Scope 3
✓ Evidence Chain
✓ Manual Processing

Usage
Documents  700 / 1000
Users      12 / 20

[ View Billing ]
[ View Events ]
[ View Audit ]
```

---

# 41. Platform Admin — Billing Events

```text
Billing Events
─────────────────────────────────────────────

Time          Type                Status
─────────────────────────────────────────────
10:32         checkout.created   ✓
10:34         payment.succeeded  ✓
10:34         subscription.active ✓
```

Provider event IDs should be available to authorized staff without exposing secrets.

---

# 42. Platform Admin — Audit

```text
Commercial Audit
─────────────────────────────────────────────

Who        What                    When
Admin A    Changed price           10:32
Admin B    Published plan v4       09:14
Admin A    Changed provider        08:45
```

Selecting an event:

```text
Changed price
─────────────────────────────────────────────
Actor: Admin A
Object: Professional v4
Previous: £89
New: £99
Reason: Annual pricing update
Time: 10:32
```

---

# 43. Admin Safety Confirmations

High-impact actions require confirmation.

Examples:

- publish new price;
- disable plan;
- change active payment provider;
- cancel customer subscription;
- issue refund;
- change entitlement;
- change Manual Processing coverage.

Example:

```text
Change active payment provider?

Current: Stripe
New: Provider B

This affects new checkout sessions.

Existing subscriptions will not be
automatically migrated.

[ Cancel ] [ Confirm Change ]
```

---

# 44. Error and Recovery UX

Every commercial action should provide:

1. what happened;
2. what remains unchanged;
3. what the user can do next.

Bad:

`Error 500`

Better:

```text
We couldn't update the subscription.

No changes were made.

[ Try Again ]
[ Contact Support ]
```

---

# 45. Trial UX

If trials are enabled:

```text
Trial
─────────────────────────────────────────────
Professional trial

12 days remaining

Your trial ends:
DD MMM YYYY

After the trial:
£XX / month

[ Choose Plan ]
```

Do not hide trial-to-paid conversion terms.

---

# 46. Payment Failure / Past Due UX

```text
Payment issue
─────────────────────────────────────────────

We couldn't collect your latest payment.

Your subscription is currently:
PAST DUE

Update your payment method to avoid
interruption.

[ Update Payment Method ]

Next retry:
DD MMM YYYY
```

The exact grace period/status semantics must follow approved billing policy.

---

# 47. No Subscription State

```text
Subscription & Billing
─────────────────────────────────────────────

No active subscription

Your organization is not currently
subscribed to a paid CarbonTally plan.

[ View Plans ]
```

If the organization has free/default access, show that explicitly rather than implying the account is broken.

---

# 48. No Payment Method

```text
Payment method required
─────────────────────────────────────────────

Add a payment method to continue
your subscription.

[ Add Payment Method ]
```

---

# 49. Provider Unavailable

```text
Checkout temporarily unavailable
─────────────────────────────────────────────

We can't start checkout right now.

Your account and selected plan have
not been changed.

[ Try Again ]
```

---

# 50. Mobile UX

The pricing matrix must not simply shrink horizontally.

Recommended mobile structure:

```text
Professional
────────────────
£XX / month

Best for:
...

Included:
✓ Scope 1
✓ Scope 2
✓ Evidence
✓ Manual Processing

Limits:
Documents X
Users X

[ Choose ]
```

Feature comparison can use:

- accordion sections;
- plan selector;
- sticky plan CTA.

Checkout must remain short and vertically ordered.

---

# 51. Accessibility

All commercial UI must support:

- keyboard navigation;
- visible focus;
- screen-reader labels;
- sufficient contrast;
- semantic headings;
- accessible tables;
- non-colour status indicators;
- clear error association;
- accessible dialogs;
- accessible confirmation actions.

Pricing information must remain understandable without colour alone.

---

# 52. Trust UX

Use appropriate trust signals:

- clear company identity;
- secure payment indicator where applicable;
- transparent billing terms;
- visible renewal information;
- clear support route;
- invoice availability;
- no deceptive countdowns;
- no forced dark-pattern cancellation.

---

# 53. Notification UX

Notifications should be:

- actionable;
- contextual;
- non-duplicative;
- dismissible where appropriate;
- linked to the relevant billing page.

Examples:

```text
Your payment method expires soon.
[ Update Payment Method ]
```

```text
You're using 90% of your document allowance.
[ View Usage ]
```

---

# 54. Copy Guidelines

Prefer:

> "Your plan renews on 4 November at £99/month."

Over:

> "Recurring billing applies."

Prefer:

> "Your downgrade takes effect on 4 November."

Over:

> "Plan change pending."

Prefer:

> "No changes were made."

Over:

> "Operation failed."

---

# 55. Avoiding Dark Patterns

CarbonTally must not:

- hide the cancellation action;
- obscure renewal prices;
- preselect expensive upgrades deceptively;
- use false scarcity;
- make downgrade harder than upgrade without legitimate operational reason;
- hide important plan limitations;
- make the customer navigate through unrelated pages to cancel.

---

# 56. Customer vs Consultant Commercial Privacy

### Customer can see

- own plan;
- own price;
- own usage;
- own invoices;
- effective entitlement;
- applicable consultant-sponsored availability where relevant.

### Customer cannot see

- consultant firm's subscription price;
- consultant firm's purchased capacity;
- other clients;
- consultant allocation details.

### Consultant can see

- own firm subscription;
- own billing;
- own Manual Processing coverage;
- own client coverage allocations.

### Consultant cannot see

- another consultant firm's commercial information;
- client payment credentials;
- unrelated organizations.

---

# 57. Platform Admin Permissions

Not every Admin user should automatically receive every commercial action.

Permissions should distinguish:

- view commercial configuration;
- edit plans;
- publish prices;
- manage payment providers;
- view subscriptions;
- modify customer subscriptions;
- issue refunds/credits;
- manage Manual Processing coverage;
- view commercial audit.

The existing CarbonTally permission model must be reused.

---

# 58. UX State Model

Every subscription screen should have explicit states:

```text
LOADING
   ↓
READY
   ├── ACTIVE
   ├── TRIAL
   ├── PAST_DUE
   ├── CANCELLING
   ├── CANCELLED
   └── NO_SUBSCRIPTION
```

Provider-dependent actions should additionally support:

```text
PROCESSING
SUCCESS
FAILED
UNAVAILABLE
```

---

# 59. Design System Integration

The implementation should reuse CarbonTally's existing:

- navigation;
- typography;
- buttons;
- cards;
- tables;
- dialogs;
- badges;
- form controls;
- notification system.

CT-UX-SUB-001 defines information architecture and interaction behavior, not a mandate to introduce a second design system.

---

# 60. UX Acceptance Scenarios

At minimum, independent verification should be able to exercise:

1. Public visitor finds Pricing.
2. Public visitor understands monthly vs annual.
3. Public visitor compares plans.
4. Public visitor can understand major feature differences.
5. Public visitor starts signup.
6. New customer sees selected plan before checkout.
7. Checkout clearly shows amount due.
8. Checkout clearly shows renewal terms.
9. Manipulated frontend price cannot change charged price.
10. Successful payment leads to clear confirmation.
11. Existing customer can see current plan.
12. Existing customer can see renewal date.
13. Existing customer can see usage.
14. Existing customer can see invoices.
15. Existing customer can update payment method.
16. Existing customer can change plan where permitted.
17. Existing customer can cancel where permitted.
18. Existing customer can reactivate where permitted.
19. Payment failure is understandable and actionable.
20. Existing Billing functionality remains available after migration.
21. Consultant can view firm subscription.
22. Consultant can manage selected-client coverage where entitled.
23. Consultant can view all-eligible coverage where entitled.
24. Customer does not see consultant commercial details.
25. Platform Admin can view subscriptions.
26. Platform Admin can configure plans.
27. Platform Admin can configure prices.
28. Platform Admin can publish a new plan version.
29. Platform Admin can configure features.
30. Platform Admin can configure limits.
31. Platform Admin can configure supported payment provider.
32. High-risk Admin changes require confirmation.
33. Audit information is visible to authorized staff.
34. Mobile pricing is usable.
35. Keyboard-only user can complete key flows.
36. Error states explain next action.

---

# 61. Relationship to CT-SUB-001

`CT-SUB-001` defines:

- product architecture;
- commercial capabilities;
- server-authoritative pricing;
- entitlement model;
- provider abstraction;
- acceptance principles.

`CT-UX-SUB-001` defines:

- user journeys;
- navigation;
- screen structure;
- interaction behavior;
- ASCII wireframes;
- UX states;
- persona boundaries;
- accessibility;
- public/customer/consultant/admin commercial experience.

The two documents are complementary.

---

# 62. Current-State Reconciliation Requirement

Before implementation, `CT-DISC-SUB-001` must identify the actual implementation behind the existing customer Billing UI.

Specifically verify:

- Billing page route;
- frontend components;
- backend endpoints;
- subscription data source;
- billing data source;
- credit model;
- storage model;
- Assisted Processing model;
- Managed Processing model;
- Orders model;
- existing permissions;
- existing Admin commercial UI;
- existing plan/version management;
- existing payment-provider integration, if any.

No existing functionality should be removed merely to make the new UI cleaner.

---

# 63. Implementation Boundary

Cline must implement the approved UX by extending the existing application architecture.

Cline must not:

- invent new billing semantics;
- invent commercial prices;
- hard-code provider choice;
- hard-code plan limits;
- create duplicate subscription infrastructure;
- bypass existing RLS;
- expose consultant commercial data to customers;
- replace working Billing functionality without authorization.

---

# 64. PO Decisions Still Required

The following remain product/commercial decisions:

- final plan names;
- final prices;
- final plan count;
- trial policy;
- billing intervals;
- discounts;
- payment providers to launch with;
- tax behavior;
- upgrade/downgrade semantics;
- cancellation semantics;
- usage-overage behavior;
- exact limits;
- exact add-ons.

The UX must support these decisions without hard-coding them.

---

# 65. Governance Status

**CT-UX-SUB-001 — PROPOSED**

This document is not implementation authorization.

Required sequence:

```text
CT-DISC-SUB-001
      ↓
Reconcile actual existing UI/backend
      ↓
PO review CT-SUB-001 + CT-UX-SUB-001
      ↓
PO APPROVAL
      ↓
Implementation prompt
      ↓
Cline implementation
      ↓
Independent verification
      ↓
PO acceptance
```

---

# 66. Final UX Principle

CarbonTally's Subscription & Billing experience should make commercial decisions feel as trustworthy as CarbonTally's evidence model:

```text
CLEAR
  ↓
UNDERSTAND
  ↓
COMPARE
  ↓
CHOOSE
  ↓
CONFIRM
  ↓
PAY
  ↓
VERIFY
  ↓
MANAGE
```

The customer should never have to guess:

> What am I buying?

> What am I paying now?

> What will I pay at renewal?

> What is included?

> What happens if I change plans?

> What happens if payment fails?

> Where is my invoice?

> How do I cancel?

And CarbonTally administrators should never need a code deployment merely to change an ordinary supported commercial parameter.
