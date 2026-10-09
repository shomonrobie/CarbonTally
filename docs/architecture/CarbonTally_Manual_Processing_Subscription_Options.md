# CarbonTally Manual Processing Subscription & Entitlement Options

**Document ID:** `CT-PO-MP-SUB-003`\
**Status:** **PO APPROVED --- AUTHORITATIVE COMMERCIAL/ENTITLEMENT
DESIGN**\
**Revision:** 2026-10-04\
**Implementation:** NOT YET IMPLEMENTED --- this document authorizes the
implementation task defined by `CT-MP-SUB-003` only\
**Production:** NOT AUTHORIZED\
**Supersedes:** Earlier Manual Processing subscription drafts, including
the prior `ALL_CLIENTS` / `SELECTED_CLIENTS`-only concept

------------------------------------------------------------------------

## 1. Purpose

This document is the Product Owner's authoritative product and
entitlement decision for CarbonTally Manual Processing.

It defines:

-   who may commercially receive Manual Processing;
-   how Manual Processing is purchased;
-   how consultant firms sponsor Manual Processing for clients;
-   finite selected-client capacity;
-   all-eligible-client coverage;
-   client allocation;
-   upgrades and downgrades;
-   consultant/client lifecycle;
-   direct and sponsored entitlement interaction;
-   subscription lifecycle;
-   operational governance;
-   Processing Entity assignment boundaries;
-   Admin configuration requirements;
-   auditability and security requirements.

The objective is a complete, deterministic product model so
implementation does not require the PO to repeatedly resolve predictable
edge cases.

------------------------------------------------------------------------

# 2. Core Product Decision

Manual Processing is a **subscription-plan capability**.

Commercial entitlement and operational activation are separate concepts.

The authoritative model is:

``` text
Commercial entitlement
        +
FIN-06 governance
        +
valid operational configuration
        =
Manual Processing operationally available
```

A customer can receive commercial entitlement through either:

1.  **Direct customer subscription**, or
2.  **Consultant-sponsored subscription coverage**.

A consultant-client relationship alone never grants Manual Processing.

------------------------------------------------------------------------

# 3. Two Commercial Entitlement Paths

## 3.1 Direct Customer Subscription

A customer organization purchases a CarbonTally subscription/plan that
includes Manual Processing.

``` text
Customer Organization
        ↓
Active qualifying subscription
        ↓
Manual Processing entitlement
```

Direct entitlement belongs to the customer organization.

It is independent of consultant relationships.

## 3.2 Consultant-Sponsored Subscription

A consultant firm purchases Manual Processing coverage as part of the
consultant firm's own subscription.

``` text
Consultant Firm
      ↓
Active qualifying subscription
      ↓
Manual Processing coverage
      ↓
Eligible consultant clients
```

The consultant firm is commercially responsible for the purchased
coverage.

The consultant does not become the Processing Entity merely by
purchasing the subscription.

------------------------------------------------------------------------

# 4. Consultant Coverage Modes

Consultant-sponsored Manual Processing has two approved commercial
coverage modes.

## 4.1 SELECTED_CLIENTS

The consultant purchases a finite capacity and explicitly allocates that
capacity to eligible consultant clients.

Example:

``` text
Manual Processing — 10 Client Capacity

Allocated:
Client A
Client B
...
Client J

Capacity: 10
Allocated: 10
Available: 0
```

One active sponsored allocation consumes one client-capacity unit.

Capacity is **not permanently tied to a specific customer**. When a
valid allocation is released, that capacity may be assigned to another
eligible consultant client.

## 4.2 ALL_ELIGIBLE_CLIENTS

The consultant explicitly purchases a product/coverage mode that covers
**all currently eligible and future eligible consultant-client
organizations**.

This is a separate commercial entitlement from finite selected-client
capacity.

Example:

``` text
Consultant subscription:
Coverage = ALL_ELIGIBLE_CLIENTS

Current eligible clients:
Client A
Client B
...
Client Z

All are commercially covered.
```

When the consultant later acquires another eligible client, that client
becomes covered automatically while the all-client subscription remains
active.

### Important

`ALL_ELIGIBLE_CLIENTS` is **not** an unrestricted administrative toggle.

It must be a commercially purchased entitlement/product configuration.

A consultant who purchased a 10-client selected-capacity product cannot
simply change a field to `ALL_ELIGIBLE_CLIENTS` without purchasing the
applicable commercial coverage.

------------------------------------------------------------------------

# 5. Eligibility Under ALL_ELIGIBLE_CLIENTS

"All clients" means:

> **All currently active and future eligible consultant-client
> organizations covered by the consultant's active subscription.**

It does not mean:

-   every organization the consultant has ever contacted;
-   unrelated CarbonTally organizations;
-   organizations without an active consultant-client relationship;
-   organizations the consultant is not authorized to access.

The existing consultant-client relationship remains authoritative for
eligibility.

Therefore:

``` text
Consultant subscription
        +
active consultant-client relationship
        ↓
eligible client
```

For `ALL_ELIGIBLE_CLIENTS`, every eligible client receives sponsored
commercial entitlement without manual per-client allocation.

For `SELECTED_CLIENTS`, explicit allocation is required.

------------------------------------------------------------------------

# 6. Capacity-Based Selected-Client Model

A consultant may purchase capacity such as:

-   10 clients;
-   25 clients;
-   50 clients;
-   100 clients;
-   custom/enterprise capacity.

Exact public tiers and prices remain configurable commercial data.

The consultant's purchased capacity is the maximum number of
simultaneously active sponsored client allocations.

Example:

``` text
Capacity = 25
Allocated = 18
Available = 7
```

If the consultant acquires another eligible client, one available
capacity unit may be allocated.

If:

``` text
Capacity = 25
Allocated = 25
Available = 0
```

a newly acquired client does not automatically receive sponsored
entitlement.

The consultant must either:

1.  release an existing allocation; or
2.  increase purchased capacity.

------------------------------------------------------------------------

# 7. Switching from Selected Clients to All Eligible Clients

This is an approved commercial scenario.

Example:

``` text
Consultant starts:
Selected Clients
Capacity = 10
Allocated = 10
```

Later the consultant wants all clients covered.

They purchase/upgrade to:

``` text
All Eligible Clients
```

The existing 10 allocations must not be treated as deleted history.

After the effective transition:

``` text
Coverage mode = ALL_ELIGIBLE_CLIENTS
```

all eligible consultant clients receive sponsored commercial
entitlement.

The old allocation records remain auditable.

### No commercial loophole

A finite selected-capacity plan cannot be converted to
unlimited/all-client coverage merely by changing an operational setting.

The transition must correspond to a valid commercial plan/subscription
state.

------------------------------------------------------------------------

# 8. Switching from All Eligible Clients to Selected Capacity

This is also supported, but it must be controlled.

Example:

``` text
Current:
ALL_ELIGIBLE_CLIENTS
Eligible clients = 37

Requested:
SELECTED_CLIENTS
Capacity = 10
```

CarbonTally must **not silently choose ten clients and disable the other
27**.

The transition must enter a controlled reconciliation state unless the
billing/commercial rules provide a future-effective downgrade.

The consultant/admin must be able to identify which clients will remain
covered.

The final active selected allocations must not exceed purchased
capacity.

------------------------------------------------------------------------

# 9. Consultant Acquires New Clients

## Selected capacity

If capacity remains:

``` text
Capacity = 25
Allocated = 18
Available = 7
```

the new client may be allocated one unit.

If capacity is exhausted:

``` text
Capacity = 25
Allocated = 25
Available = 0
```

the new client remains uncovered until:

-   capacity is increased; or
-   another allocation is released.

The system must not silently grant entitlement.

## All eligible

If the consultant has valid `ALL_ELIGIBLE_CLIENTS` coverage, the newly
acquired client becomes covered automatically once the existing
consultant-client relationship is active and the client is eligible.

No per-client allocation is required.

------------------------------------------------------------------------

# 10. Consultant Client Relationship Ends

When a consultant-client relationship ends:

-   consultant access follows the existing consultant-client lifecycle;
-   the former client no longer qualifies for consultant-sponsored
    entitlement through that relationship;
-   for selected coverage, the allocation is released/deactivated;
-   released capacity becomes available for another eligible client;
-   for all-eligible coverage, the client is no longer within the
    eligible population;
-   the client organization, data, accounting history, evidence,
    processing history and provenance remain intact.

Historical records must not be rewritten.

------------------------------------------------------------------------

# 11. Direct + Consultant-Sponsored Entitlement

A client may have:

``` text
Direct entitlement
```

or:

``` text
Consultant-sponsored entitlement
```

or both.

The effective commercial entitlement is:

``` text
DIRECT OR SPONSORED
```

If a client already has direct Manual Processing and later becomes
consultant-sponsored:

-   do not create duplicate operational services;
-   do not double-count the same entitlement merely because two
    commercial paths exist;
-   preserve both commercial facts where required for billing/audit;
-   resolve operational capability deterministically.

If consultant sponsorship later ends while the client's direct
subscription remains active:

``` text
Sponsored = inactive
Direct = active

Effective entitlement = active
```

If direct subscription ends while consultant sponsorship remains active:

``` text
Direct = inactive
Sponsored = active

Effective entitlement = active
```

If both end:

``` text
Effective entitlement = inactive
```

------------------------------------------------------------------------

# 12. Subscription Lifecycle

The implementation must use the existing CarbonTally subscription
lifecycle rather than inventing a parallel lifecycle.

The entitlement resolver must distinguish at least the existing
commercially meaningful states such as:

-   active;
-   inactive/expired;
-   cancelled;
-   suspended/past-due where applicable under the existing billing
    model.

The exact billing-state semantics must be reconciled with the existing
`customer_subscriptions` implementation.

### Payment failure

Payment failure must not produce an arbitrary entitlement state.

The implementation must reuse the existing CarbonTally subscription
lifecycle and any established grace-period semantics.

If the existing architecture does not define a required commercial rule,
Cline must report the gap rather than invent a materially different
billing policy.

------------------------------------------------------------------------

# 13. Capacity Upgrade

A selected-capacity consultant may upgrade:

``` text
10 → 25
25 → 50
50 → 100
```

Existing allocations remain valid.

The additional capacity becomes available after the effective commercial
change.

Example:

``` text
Before:
Capacity = 10
Allocated = 10
Available = 0

After upgrade:
Capacity = 25
Allocated = 10
Available = 15
```

An upgrade must not require recreating client allocations.

------------------------------------------------------------------------

# 14. Capacity Downgrade

A downgrade must not silently remove Manual Processing from clients.

Example:

``` text
Current:
Capacity = 25
Allocated = 22

Requested:
Capacity = 10
```

This creates:

``` text
Over-allocated = 12
```

The system must use a controlled reconciliation mechanism.

Approved principles:

-   no silent selection of survivors;
-   no silent removal of clients;
-   no deletion of historical allocation records;
-   active allocation count must not exceed effective capacity after the
    downgrade takes effect.

Exact proration and billing-period timing are commercial configuration
and must use existing billing architecture or be reported as a remaining
PO decision if unsupported.

------------------------------------------------------------------------

# 15. Allocation Lifecycle

For selected-client coverage:

``` text
Available capacity
       ↓
Allocate
       ↓
Active allocation
       ↓
Release / deactivate
       ↓
Available capacity
```

Allocation changes must be auditable.

An allocation is not a replacement for the underlying consultant-client
relationship.

A forged allocation record must not grant cross-tenant access.

------------------------------------------------------------------------

# 16. Manual Processing Operational Activation

Commercial entitlement does not automatically mean operational routing.

The existing FIN-06 governance remains authoritative.

The effective operational rule is:

``` text
Commercial entitlement
        AND
FIN-06 governance enabled
        ↓
Manual Processing operationally available
```

Therefore:

### Entitled + governance enabled

Manual Processing may be operationally available, subject to PE
configuration.

### Entitled + governance disabled

Manual Processing is commercially entitled but operationally disabled.

### Not entitled + governance enabled

Manual Processing must remain operationally unavailable.

Governance must never create commercial entitlement.

------------------------------------------------------------------------

# 17. Processing Entity Assignment

PE assignment remains separate from subscription entitlement.

Commercial coverage does not:

-   create a PE;
-   select an arbitrary PE;
-   authorize a PE;
-   bypass PE assignment governance.

For automatic fallback:

``` text
Commercial entitlement
        ↓
FIN-06 enabled
        ↓
valid PE configuration
        ↓
automatic routing
```

If no valid PE is configured:

> explicit `no_processor_configured` operational outcome.

The system must not randomly choose a PE or silently route to an
unrelated PE.

Existing human/internal-staff assignments must not be silently
superseded merely because automatic fallback becomes eligible.

------------------------------------------------------------------------

# 18. Existing Legacy Entitlement Compatibility

The canonical feature is:

``` json
{
  "manual_processing": {
    "enabled": true
  }
}
```

Existing `assisted_processing_available` must be treated as a
backward-compatible legacy alias for the same Manual Processing
capability unless a future PO decision explicitly changes its meaning.

Resolution principle:

``` text
Explicit features.manual_processing.enabled
        ↓
authoritative when present

Otherwise
        ↓
legacy assisted_processing_available
```

The implementation must not silently remove existing
Professional/Business/Enterprise entitlement that currently depends on
the legacy flag.

The migration should normalize or preserve compatibility safely.

------------------------------------------------------------------------

# 19. Subscription/Plan Configuration

Manual Processing must be configurable through CarbonTally Admin.

The implementation must reuse the existing plan/subscription
architecture.

Conceptually, plans need to express:

``` text
Manual Processing
    enabled: true/false

Consultant coverage:
    selected capacity: quantity
    OR
    all eligible clients: entitlement
```

The exact storage representation must be determined by inspection of the
existing billing architecture.

Do not create a parallel subscription system.

Public plan names, pricing and capacity tiers must remain configurable
rather than hard-coded into application logic.

------------------------------------------------------------------------

# 20. Admin UX

CarbonTally Admin must be able to understand and manage the commercial
state.

At minimum, the relevant Admin experience must distinguish:

### Plan

-   Manual Processing enabled/disabled;
-   consultant coverage mode;
-   selected-client capacity where applicable;
-   commercial configuration.

### Consultant

-   active subscription;
-   coverage mode;
-   purchased capacity where applicable;
-   allocated count;
-   available count;
-   over-allocation;
-   eligible client population.

### Client

-   direct entitlement;
-   consultant-sponsored entitlement;
-   consultant relationship;
-   allocation status;
-   FIN-06 governance;
-   PE configuration;
-   effective operational state.

Do not collapse all of these into one ambiguous Manual Processing
switch.

------------------------------------------------------------------------

# 21. Customer/Consultant UX

The consultant-facing experience should make commercial coverage
understandable.

For selected capacity:

``` text
Manual Processing
25 client capacity

18 clients covered
7 client slots available
```

For all eligible:

``` text
Manual Processing
All eligible consultant clients covered
```

When capacity is exhausted:

``` text
Manual Processing capacity full
25 / 25 client slots used

Upgrade capacity or release an existing client allocation.
```

When a new client is not covered:

``` text
Manual Processing not included for this client
Reason: consultant capacity exhausted.
```

The UI must not imply that a consultant relationship automatically
includes Manual Processing.

------------------------------------------------------------------------

# 22. Security and Tenant Isolation

Consultant-sponsored entitlement must never become a cross-tenant
authorization shortcut.

Required:

-   consultant-client relationship remains authoritative for consultant
    access;
-   client organization boundaries remain enforced;
-   allocation records are not authorization grants;
-   Admin operations use existing Admin authorization;
-   backend authorization is authoritative;
-   RLS/security controls are preserved or extended appropriately;
-   frontend hiding is not security;
-   a consultant cannot allocate capacity to an unrelated organization.

------------------------------------------------------------------------

# 23. Auditability

The system must preserve an auditable commercial history.

Relevant events should establish, where applicable:

-   consultant firm;
-   client organization;
-   subscription/plan;
-   coverage mode;
-   capacity;
-   allocation creation;
-   allocation release;
-   allocation transition;
-   upgrade;
-   downgrade;
-   entitlement activation/deactivation;
-   actor;
-   timestamp.

Changing entitlement must not rewrite historical processing records.

------------------------------------------------------------------------

# 24. Commercial Scenarios That Must Work

The implementation and verification must eventually exercise at least:

1.  Direct customer with Manual Processing.
2.  Consultant with 10 selected-client capacity.
3.  7/10 selected allocations.
4.  10/10 selected allocations.
5.  New client when capacity remains.
6.  New client when capacity is exhausted.
7.  Upgrade 10 → 25.
8.  Release a client allocation.
9.  Reuse released capacity for another client.
10. Consultant acquires client under all-eligible coverage.
11. Switch selected → all eligible.
12. Switch all eligible → selected.
13. All eligible with client relationship termination.
14. Direct + sponsored entitlement simultaneously.
15. Sponsored entitlement ends while direct remains.
16. Direct entitlement ends while sponsored remains.
17. Both entitlements end.
18. Consultant subscription becomes inactive.
19. FIN-06 disabled despite commercial entitlement.
20. Entitled client with no PE.
21. Consultant attempts to allocate unrelated organization.
22. Downgrade while selected allocations exceed new capacity.
23. Existing human/internal-staff assignment is preserved during
    fallback.
24. Legacy `assisted_processing_available` compatibility.

------------------------------------------------------------------------

# 25. Remaining Commercial Decisions

The following are deliberately not invented by this document:

1.  final public pricing;
2.  final capacity tier names;
3.  final exact capacity quantities;
4.  final payment provider;
5.  final proration percentages/formulas;
6.  final refund policy;
7.  exact grace-period duration if not already defined by the billing
    architecture;
8.  tax/VAT treatment;
9.  custom enterprise pricing;
10. whether additional capacity may be purchased independently of plan
    upgrades;
11. whether unused selected-client capacity carries across billing
    periods.

These are commercial/billing decisions, not reasons to redesign the
entitlement architecture.

Where implementation depends materially on one of these decisions, Cline
must identify the dependency and STOP rather than invent a business
rule.

------------------------------------------------------------------------

# 26. Existing-First Implementation Requirement

Before modifying code, Cline must inspect:

-   `customer_subscriptions`;
-   `billing_plans`;
-   `billing_plans.features`;
-   `assisted_processing_available`;
-   `get_active_for_org`;
-   consultant profiles;
-   consultant-client relationships;
-   existing Manual Processing governance;
-   Processing Entity configuration;
-   existing Admin plan-management APIs/UI;
-   subscription lifecycle/status handling;
-   existing audit mechanisms;
-   RLS/security policies;
-   existing tests.

Every requirement must be classified:

-   EXISTS --- VERIFIED;
-   PARTIAL --- EXTENDED;
-   EXISTS BUT DISCONNECTED --- WIRED;
-   DUPLICATE --- CONSOLIDATED;
-   MISSING --- IMPLEMENTED;
-   DEFERRED --- JUSTIFIED;
-   BLOCKED --- EVIDENCE REQUIRED.

------------------------------------------------------------------------

# 27. Implementation Boundary

This document authorizes implementation of the approved Manual
Processing subscription/entitlement design through the separately
identified implementation task `CT-MP-SUB-003`.

It does **not** authorize:

-   production deployment;
-   production migration;
-   production data modification;
-   payment-provider integration unless already required by existing
    architecture and explicitly within task scope;
-   final public pricing;
-   unrelated refactoring;
-   changes to closed authorization foundations;
-   arbitrary new roles;
-   arbitrary new billing systems.

If implementation requires a material product decision not contained in
this document, Cline must STOP and report it.

------------------------------------------------------------------------

# 28. Product Owner Final Decision

**APPROVED**

CarbonTally Manual Processing supports:

### Direct customers

Direct subscription entitlement.

### Consultant-sponsored selected coverage

Finite purchased client capacity with explicit allocation.

### Consultant-sponsored all-eligible coverage

A separately purchased commercial mode covering all currently and
subsequently eligible consultant-client organizations while active.

### Entitlement rule

``` text
Effective commercial entitlement
=
Direct entitlement
OR
Consultant-sponsored entitlement
```

### Operational rule

``` text
Operational Manual Processing
=
Commercial entitlement
AND
FIN-06 governance enabled
AND
required operational configuration
```

### Core commercial principle

> A consultant relationship is not itself a Manual Processing
> entitlement. Manual Processing coverage is purchased commercially, and
> consultant-sponsored coverage is bounded by the purchased coverage
> model.

### Core flexibility principle

> A consultant may start with selected clients and finite capacity,
> later upgrade to all eligible clients, or move back to finite selected
> capacity through controlled commercial reconciliation.

### Core safety principle

> No commercial state change may silently remove client service, bypass
> tenant authorization, bypass FIN-06 governance, or invent a Processing
> Entity assignment.

------------------------------------------------------------------------

# 29. Status

  Item                                       Status
  ------------------------------------------ -----------------------------------
  Direct Manual Processing entitlement       **CLOSED**
  Consultant-sponsored entitlement           **CLOSED**
  Selected-client finite capacity            **CLOSED**
  All-eligible-client coverage               **CLOSED**
  Selected → All transition                  **CLOSED**
  All → Selected transition principle        **CLOSED**
  Capacity upgrade principle                 **CLOSED**
  Capacity downgrade safety principle        **CLOSED**
  Direct + sponsored entitlement             **CLOSED**
  Consultant/client lifecycle                **CLOSED**
  FIN-06 separation                          **CLOSED**
  PE separation                              **CLOSED**
  Legacy assisted-processing compatibility   **CLOSED**
  Admin configurability requirement          **CLOSED**
  Final public pricing                       **OPEN --- COMMERCIAL**
  Payment provider                           **OPEN --- COMMERCIAL/TECHNICAL**
  Production deployment                      **NOT AUTHORIZED**

------------------------------------------------------------------------

## Authority

This document is the **Product Owner authority** for `CT-MP-SUB-003`.

Cline must implement the approved architecture without silently
broadening, narrowing, or replacing these decisions.

If a material contradiction is discovered, Cline must stop and report it
before implementation.
