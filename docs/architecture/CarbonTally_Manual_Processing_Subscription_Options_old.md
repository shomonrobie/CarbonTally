# CarbonTally — Manual Processing Subscription & Entitlement Options

**Status:** PO Decision / Design Specification  
**Date:** 2026-10-04  
**Scope:** Manual Processing subscription entitlement, consultant-sponsored coverage, and configurable subscription plans  
**Related capability:** FIN-06 Manual Processing, Processing Entity (PE) routing, CarbonTally Admin `/ops`

## 1. Purpose

This document defines how CarbonTally Manual Processing is commercially entitled and administratively configured.

The key business decision is that **Manual Processing is a subscription-plan capability**. A customer may receive the capability either through its own CarbonTally subscription or through a consultant-sponsored Manual Processing entitlement.

The existing CarbonTally subscription/billing system must be extended as necessary so that **subscription plans and their feature entitlements are configurable through the CarbonTally Admin panel**.

This is a product/business rule specification. It does not authorize production changes, deployment, migration, commit, or push.

## 2. Core Business Rule

Manual Processing is available only when the customer is entitled to it through an active subscription arrangement.

```text
Manual Processing Effective
=
Subscription Entitlement
AND
FIN-06 Governance Enabled
```

Subscription entitlement answers whether the customer has commercially purchased/received Manual Processing.

FIN-06 governance answers whether an authorized CarbonTally Admin has enabled it.

Processing Entity configuration answers where failed automatic processing should be routed.

These are separate concepts.

## 3. Subscription Options

### 3.1 Direct Customer Subscription

A customer organization subscribes directly to a CarbonTally plan that includes Manual Processing.

```text
Customer A
    |
    └── CarbonTally Plan
          └── Manual Processing = Enabled
```

Result:
- Customer A is commercially entitled.
- Admin may enable Manual Processing through FIN-06.
- Admin may configure the applicable PE.
- Automatic extraction failures may route to that PE once all operational conditions are satisfied.

### 3.2 Consultant-Sponsored Manual Processing

A consultant can purchase a Manual Processing capability that allows the consultant to cover:
- **All** of its consultant-client organizations, or
- **Selected** consultant-client organizations.

```text
Consultant ABC
    |
    └── Consultant Manual Processing entitlement
          |
          ├── ALL CLIENTS
          |
          OR
          |
          ├── Client A
          ├── Client B
          └── Client C
```

Consultant sponsorship provides **commercial entitlement**. It does not automatically:
- enable Manual Processing
- assign a PE
- give the consultant authority to assign CarbonTally PEs
- bypass FIN-06 governance
- bypass PE authorization or tenant isolation

## 4. Consultant Coverage Modes

### ALL_CLIENTS

Every eligible consultant-client organization under that consultant is commercially entitled.

### SELECTED_CLIENTS

Only explicitly selected consultant-client organizations are commercially entitled.

The selected-client relationship must be explicit and auditable.

## 5. Direct + Consultant-Sponsored Entitlement

A consultant-client may become entitled through either:

```text
Direct Customer Entitlement
OR
Consultant-Sponsored Entitlement
```

Recommended resolution:
1. Check the client organization's direct subscription.
2. If not entitled directly, check whether the consultant has an active Manual Processing entitlement covering that client.
3. Coverage must be `ALL_CLIENTS` or explicit `SELECTED_CLIENTS` membership.
4. Otherwise the client is not entitled.

Do not use a simple rule that a consultant subscription automatically entitles every organization associated with that consultant.

## 6. Subscription Plans Must Be Configurable from CarbonTally Admin

The existing subscription/billing system must be updated so CarbonTally Admin can configure subscription plans and their feature entitlements.

At minimum, Admin should be able to configure, subject to the existing billing architecture:
- plan name
- plan status
- plan description where applicable
- existing billing configuration
- feature entitlements
- Manual Processing entitlement
- other existing plan features

Normal plan/feature changes must not require a developer/database migration.

Do not create a parallel subscription system.

## 7. Manual Processing as a Configurable Plan Feature

Manual Processing should be represented as a configurable feature, not hard-coded to plan names.

Conceptually:

```json
{
  "features": {
    "manual_processing": {
      "enabled": true
    }
  }
}
```

The implementation must reuse the existing CarbonTally plan/feature mechanism where possible.

Plan names such as Starter, Professional, Business, and Enterprise must not themselves determine Manual Processing eligibility.

## 8. Consultant Manual Processing Subscription

The consultant offering should support a commercial entitlement that can cover clients according to the purchased coverage mode.

```text
Consultant Subscription
    |
    └── Manual Processing
          |
          ├── coverage_mode = ALL_CLIENTS
          |
          OR
          |
          └── coverage_mode = SELECTED_CLIENTS
```

Reuse the existing subscription architecture. If consultant coverage cannot be represented safely, introduce only the smallest explicit extension required.

## 9. Admin Responsibilities

CarbonTally Admin should be able to:

### Subscription configuration
- create/configure plans
- enable/disable Manual Processing as a plan feature
- change feature availability by plan
- manage plan status according to existing billing rules

### Consultant coverage
- select ALL_CLIENTS or individual consultant-client organizations where permitted
- remove client coverage
- view current coverage
- audit coverage changes

### Manual Processing operations
For an entitled customer:
- enable/disable FIN-06 Manual Processing
- assign/change the PE
- remove PE assignment
- view entitlement status
- view governance status
- view processor configuration status

Subscription entitlement and operational configuration must be visibly distinct.

## 10. Consultant Permissions

A consultant may eventually be allowed to manage which of its clients are covered by its purchased entitlement, subject to the final authorization model.

A consultant must not automatically receive authority to:
- assign arbitrary CarbonTally PEs
- bypass Admin governance
- bypass subscription entitlement
- access another consultant's clients
- bypass tenant/RLS boundaries

PE assignment remains an Admin operational decision unless separately authorized.

## 11. Processing Entity Assignment

Subscription entitlement does not determine the PE.

```text
Subscription entitlement
        |
        v
FIN-06 enabled
        |
        v
Admin configures PE
        |
        v
Automatic extraction failure
        |
        v
Manual Processing routing
        |
        v
Configured PE work item
```

If entitled and enabled but no PE is configured, the result is:

```text
no_processor_configured
```

The system must not randomly select a PE, select an arbitrary PE, revive legacy `queue_settings.auto_assign_enabled`, silently assign another organization, or create an unauthorized cross-tenant assignment.

## 12. Customer Without Entitlement

If the customer has neither a direct Manual Processing entitlement nor a valid consultant-sponsored entitlement:
- Manual Processing is unavailable.
- Admin cannot configure a PE for it.
- Manual Processing cannot be enabled.
- Automatic extraction failures must not be routed to a PE.
- The customer remains on the normal non-manual/self-service failure path.

This is a server-side rule.

## 13. Customer With Entitlement but Disabled

If commercially entitled but FIN-06 is disabled:

```text
entitlement = true
governance = false
effective Manual Processing = false
```

No automatic PE routing occurs.

## 14. Customer With Full Eligibility

Operational routing requires:

```text
Subscription entitlement
        AND
FIN-06 governance enabled
        AND
Processing Entity configured
        |
        v
Automatic failure
        |
        v
PE task/work item
```

Routing must remain server-authoritative and idempotent.

## 15. Audit Requirements

Audit at least:
- plan feature changes
- Manual Processing feature enabled/disabled on a plan
- consultant coverage mode changes
- selected-client additions/removals
- Manual Processing enable/disable
- rejected enablement due to missing entitlement
- PE assigned/changed/removed
- rejected PE assignment due to missing entitlement
- automatic routing success
- routing denied because not entitled
- routing denied because governance disabled
- routing blocked because no PE is configured
- duplicate/idempotent routing attempts where appropriate

## 16. Security Requirements

All entitlement checks must be server-side.

The implementation must prevent:
- forged entitlement fields
- customer self-enablement
- unauthorized PE assignment
- cross-organization PE assignment
- consultant access outside its authorized clients
- stale grants bypassing subscription entitlement
- consultant sponsorship bypassing subscription coverage rules

Reuse existing RLS and authorization patterns.

## 17. Recommended Admin UX

Example direct customer:

```text
Customer: Client A

Subscription
    Plan: Business
    Entitlement: Manual Processing ✓
    Source: Direct customer subscription

Manual Processing
    Governance: Enabled
    Processing Entity: PE Team 2
    Routing: Active
```

Example consultant-sponsored customer:

```text
Customer: Client B

Subscription
    Entitlement: Manual Processing ✓
    Source: Consultant-sponsored
    Consultant: Consultant ABC
    Coverage: Selected Client

Manual Processing
    Governance: Enabled
    Processing Entity: PE Team 1
    Routing: Active
```

Example uncovered client:

```text
Direct Manual Processing: No
Consultant-sponsored: No
Effective entitlement: No

Manual Processing
    Unavailable
```

## 18. Existing Subscription System Must Be Reviewed

Before implementation, inspect:
- current plans
- feature representation
- subscription states
- Admin configuration capabilities
- whether plan features are already configurable
- whether Manual Processing is already represented
- meaning of `features.manual_processing.enabled`
- meaning of `assisted_processing_available`
- whether consultant subscriptions already exist
- consultant-client relationship representation
- audit mechanisms

Do not assume the current model matches this specification.

## 19. PO Decision Required — `assisted_processing_available`

The current implementation reportedly treats:

```text
features.manual_processing.enabled
OR
assisted_processing_available
```

as entitlement sources.

This document does **not** ratify that behavior automatically.

Confirm whether `assisted_processing_available` is:
1. the legacy name for the same Manual Processing capability, or
2. a different commercial feature.

If it is the same feature, normalize it into the configurable Manual Processing entitlement.

If different, Manual Processing must use an explicit dedicated entitlement.

Do not silently broaden or narrow entitlement.

## 20. Recommended Product Model

```text
                         CARBONTALLY BILLING
                                |
                 ┌──────────────┴──────────────┐
                 |                             |
          Direct Customer                Consultant
          Subscription                  Subscription
                 |                             |
        Manual Processing              Manual Processing
           feature                         feature
                 |                             |
                 |                    ┌────────┴────────┐
                 |                    |                 |
                 |                ALL CLIENTS     SELECTED CLIENTS
                 |                    |                 |
                 └──────────────┬─────┴─────────────────┘
                                |
                      COMMERCIAL ENTITLEMENT
                                |
                                v
                     FIN-06 GOVERNANCE
                                |
                         Admin enabled?
                                |
                               YES
                                |
                                v
                     PE CONFIGURATION
                                |
                         PE configured?
                                |
                               YES
                                |
                                v
                    AUTOMATIC PROCESSING
                                |
                            FAILURE
                                |
                                v
                      MANUAL PE WORK ITEM
```

## 21. Implementation Principles

1. Reuse the existing subscription/billing system.
2. Make subscription plans configurable from CarbonTally Admin.
3. Represent Manual Processing as a configurable plan feature.
4. Support direct customer entitlement.
5. Support consultant-sponsored entitlement.
6. Support consultant coverage for all clients.
7. Support consultant coverage for selected clients.
8. Keep commercial entitlement separate from FIN-06 activation.
9. Keep PE assignment separate from entitlement.
10. Enforce all rules server-side.
11. Preserve existing FIN-06 scope precedence.
12. Preserve existing PE and D38 work-item models.
13. Do not revive legacy automatic-assignment behavior.
14. Maintain auditability and idempotency.
15. Do not make production changes until implementation and independent verification are complete.

## 22. Acceptance Criteria

### Subscription
- [ ] Admin can configure subscription plans.
- [ ] Admin can configure Manual Processing as a plan feature.
- [ ] Direct customer subscription can grant Manual Processing.
- [ ] Consultant subscription can grant Manual Processing.
- [ ] Consultant can cover all clients where the plan permits.
- [ ] Consultant can cover selected clients where the plan permits.
- [ ] Coverage is explicit and auditable.

### Governance
- [ ] FIN-06 remains separate from subscription entitlement.
- [ ] Effective state requires entitlement AND governance enabled.
- [ ] Existing FIN-06 scope precedence remains correct.

### Operations
- [ ] Admin can configure PE only for entitled customers.
- [ ] Unentitled customers cannot receive PE configuration.
- [ ] Automatic extraction failure routes only when all conditions are satisfied.
- [ ] No arbitrary PE selection.
- [ ] No duplicate work items.

### Security
- [ ] Customer cannot forge entitlement.
- [ ] Customer cannot self-enable Manual Processing.
- [ ] Consultant cannot access another consultant's clients.
- [ ] Consultant sponsorship cannot bypass tenant boundaries.
- [ ] PE assignment remains authorized.

### Verification
- [ ] Direct subscription E2E passes.
- [ ] Consultant ALL_CLIENTS E2E passes.
- [ ] Consultant SELECTED_CLIENTS E2E passes.
- [ ] Uncovered consultant-client E2E passes.
- [ ] Disabled governance E2E passes.
- [ ] Missing PE behavior passes.
- [ ] Unauthorized access tests pass.
- [ ] RLS/tenant isolation is independently verified.

## 23. Current Status

This document records a **PO-level product decision/design direction**.

It does not itself authorize implementation, migration, production database changes, deployment, commit, or push.

Implementation should begin only after the current subscription/billing architecture is inspected and the meaning of `assisted_processing_available` is established.

The Manual Processing implementation currently under verification must be updated to conform to this entitlement model before final PO acceptance if its current behavior differs.
