# CarbonTally — CT-UX-MP-SUB-003
## Manual Processing Commercial & Entitlement — Authoritative ASCII UI/UX Specification

**Document ID:** CT-UX-MP-SUB-003  
**Revision:** 2026-10-04  
**Status:** PROPOSED FOR PO APPROVAL  
**Governing specification:** `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md`  
**Scope:** Platform Admin/Operations, Customer, Consultant

> This document translates the already-approved CT-PO-MP-SUB-003 commercial model into UI/UX. It does not create pricing, capacity tiers, payment, proration, refund, tax, persona, authorization, or operational-processing rules.

---

## 1. Core product model

The UI must preserve this separation:

```text
                    SUBSCRIPTION / COMMERCIAL COVERAGE
                                  |
                  +---------------+---------------+
                  |                               |
           DIRECT CUSTOMER                  CONSULTANT-SPONSORED
             SUBSCRIPTION                       COVERAGE
                  |                               |
                  |                         +-----+------+
                  |                         |            |
                  |                   SELECTED      ALL ELIGIBLE
                  |                   CLIENTS         CLIENTS
                  |                         |            |
                  |                    allocation    relationship
                  |                    capacity       eligibility
                  +-------------------------+------------+
                                            |
                                            v
                                  COMMERCIAL ENTITLEMENT
                                            |
                                            v
                                    FIN-06 GOVERNANCE
                                            |
                                            v
                                  PROCESSING / ROUTING
                                            |
                                            v
                                    PROCESSING ENTITY
```

**Mandatory UX rule:** commercial entitlement, FIN-06 governance, and Processing Entity/routing are separate concepts.

Purchasing coverage does not automatically make a consultant a Processing Entity. PE assignment does not create commercial entitlement.

---

# 2. Platform Admin / Operations

The existing Manual Processing screen remains the operational/routing view:

```text
+------------------------------------------------------------------+
| Internal Operations                                              |
|                                                                  |
| Review | Assignments | QC | Staff | Roles | Entities | ...      |
|                                                                  |
| [ Manual Processing ]                                            |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
| Manual Processing — subscription to routing                     |
|                                                                  |
| Scope:             [ Organisation v ]                            |
| Organisation ID:   [ UUID / organisation id              ]       |
|                                                                  |
|                     [ Load state ]                               |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
| Operational state                                                 |
|                                                                  |
| Commercial entitlement:    ...                                  |
| FIN-06 activation:         ...                                  |
| Processing Entity:         ...                                  |
| Routing state:              ...                                  |
+------------------------------------------------------------------+
```

Add a distinct commercial coverage control area rather than conflating it with routing:

```text
+------------------------------------------------------------------+
| Manual Processing                                                |
+------------------------------------------------------------------+
| [ Commercial Coverage ] [ Operational Routing ] [ Assignments ] |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
| Commercial Coverage                                              |
|                                                                  |
| Consultant Firm:   ABC Consulting Ltd                            |
| Subscription:      [ active plan / configured plan ]            |
| Status:             ACTIVE                                       |
|                                                                  |
| Manual Processing:  ENABLED                                     |
|                                                                  |
| Consultant Coverage:                                             |
|   ( ) No sponsored coverage                                     |
|   (*) Selected Clients                                          |
|   ( ) All Eligible Clients                                      |
+------------------------------------------------------------------+
```

## Admin — SELECTED_CLIENTS

```text
+------------------------------------------------------------------+
| Selected Clients                                                 |
+------------------------------------------------------------------+
| Purchased capacity:        [ configured quantity ]              |
| Allocated:                  7                                    |
| Available:                  3                                    |
|                                                                  |
| Capacity                                                        |
| [██████████████░░░░░░]  7 / 10                                |
|                                                                  |
| [ View Covered Clients ]   [ Allocate Client ]                  |
+------------------------------------------------------------------+
```

Exhausted:

```text
+------------------------------------------------------------------+
| Selected Client Capacity                                        |
+------------------------------------------------------------------+
| Capacity:                 10 / 10                               |
| Available allocations:    0                                    |
|                                                                  |
| No allocation capacity remains.                                |
| A new client cannot receive sponsored coverage until capacity   |
| is increased or an existing allocation is released.             |
|                                                                  |
| [ Upgrade / Change Coverage ]                                   |
+------------------------------------------------------------------+
```

The actual capacity must come from subscription configuration; the UI must not invent final tier quantities.

## Admin — ALL_ELIGIBLE_CLIENTS

```text
+------------------------------------------------------------------+
| All Eligible Clients                                            |
+------------------------------------------------------------------+
| Coverage mode:       ALL ELIGIBLE CLIENTS                       |
|                                                                  |
| Current eligible clients:          24                           |
| Currently covered:                 24                           |
| Future eligible clients:           Automatically covered        |
|                                                                  |
| Eligibility source:               Active consultant-client       |
|                                    relationship                  |
|                                                                  |
| [ View Eligible Clients ]                                        |
+------------------------------------------------------------------+
```

"All" means all currently/future eligible active consultant-client organizations, not every organization in CarbonTally.

## Admin — effective entitlement

```text
+------------------------------------------------------------------+
| Effective Manual Processing Entitlement                         |
+------------------------------------------------------------------+
| Direct customer subscription:       YES                          |
| Consultant-sponsored coverage:      YES                          |
| Effective entitlement:              YES                          |
| FIN-06 governance:                  ENABLED / DISABLED           |
| Processing Entity:                  CONFIGURED / NONE            |
+------------------------------------------------------------------+
```

Direct + sponsored must not imply two separate operational services.

---

# 3. Customer surface

Customers see their effective service state, not internal consultant capacity mechanics.

## Direct coverage

```text
+--------------------------------------------------------------+
| Manual Processing                                            |
+--------------------------------------------------------------+
| Status:                 AVAILABLE                            |
| Coverage:               Included in your subscription        |
| Processing mode:        Manual Processing                    |
| Processing Entity:      [ configured / not configured ]     |
| Governance status:      [ active / inactive ]                |
|                                                              |
| [ View details ]                                             |
+--------------------------------------------------------------+
```

## Consultant-sponsored coverage

```text
+--------------------------------------------------------------+
| Manual Processing                                            |
+--------------------------------------------------------------+
| Status:                 AVAILABLE                            |
| Coverage:               Provided through your consultant     |
| Consultant:             ABC Consulting Ltd                   |
| Processing Entity:      [ configured separately ]            |
|                                                              |
| [ View details ]                                             |
+--------------------------------------------------------------+
```

Do not expose purchased consultant capacity, other clients, internal allocation IDs, or internal routing identifiers unless separately authorized.

## Direct + sponsored

```text
+--------------------------------------------------------------+
| Manual Processing                                            |
+--------------------------------------------------------------+
| Status:                 AVAILABLE                            |
|                                                              |
| Your coverage includes:                                      |
|   ✓ Direct subscription                                     |
|   ✓ Consultant-sponsored coverage                            |
|                                                              |
| Effective entitlement:  AVAILABLE                            |
+--------------------------------------------------------------+
```

## Not entitled

```text
+--------------------------------------------------------------+
| Manual Processing                                            |
+--------------------------------------------------------------+
| Status:                 NOT INCLUDED                         |
|                                                              |
| Manual Processing is not included in your current commercial  |
| coverage.                                                    |
|                                                              |
| [ View available plans ]                                     |
+--------------------------------------------------------------+
```

## Commercially entitled but not operationally configured

```text
+--------------------------------------------------------------+
| Manual Processing                                            |
+--------------------------------------------------------------+
| Commercial entitlement: AVAILABLE                            |
| Operational status:      NOT YET CONFIGURED                  |
| Processing Entity:       Not configured                      |
|                                                              |
| Your Manual Processing coverage is active, but operational    |
| processing configuration is not yet complete.                |
+--------------------------------------------------------------+
```

This must not be presented as "not subscribed."

---

# 4. Consultant surface

The consultant needs to understand what coverage the firm purchased, how much selected capacity remains, and which eligible clients are covered.

## Consultant dashboard

```text
+----------------------------------------------------------------+
| Manual Processing Coverage                                    |
+----------------------------------------------------------------+
| Coverage:              [ SELECTED CLIENTS / ALL ELIGIBLE ]     |
| Subscription status:   ACTIVE                                  |
| Clients covered:       [ count ]                              |
+----------------------------------------------------------------+
| [ Covered Clients ]     [ Coverage Details ]                   |
+----------------------------------------------------------------+
```

## SELECTED_CLIENTS

```text
+----------------------------------------------------------------+
| Manual Processing Coverage                                    |
+----------------------------------------------------------------+
| Mode:                  SELECTED CLIENTS                       |
| Purchased capacity:   10 clients                              |
| Allocated:             7 / 10                                 |
| Available:             3                                       |
|                                                                |
| [██████████████░░░░░░]  70%                                   |
|                                                                |
| [ Add Client ]                                                |
+----------------------------------------------------------------+
```

Covered clients:

```text
+----------------------------------------------------------------+
| Covered Clients                                                |
+----------------------------------------------------------------+
| Client                     Coverage             Action         |
| ----------------------------------------------------------------|
| Client A                   Active               [ View ]        |
| Client B                   Active               [ View ]        |
| Client C                   Active               [ View ]        |
+----------------------------------------------------------------+
```

Eligible client allocation:

```text
+----------------------------------------------------------------+
| Add Client                                                     |
+----------------------------------------------------------------+
| Eligible consultant clients                                   |
|                                                                |
| Client A                         [ Covered ]                    |
| Client B                         [ Available ]                  |
| Client C                         [ Available ]                  |
|                                                                |
| [ Allocate ]                                                   |
+----------------------------------------------------------------+
```

Only eligible consultant-client organizations may be selected.

Capacity exhausted:

```text
+----------------------------------------------------------------+
| Manual Processing Coverage                                    |
+----------------------------------------------------------------+
| Mode:                  SELECTED CLIENTS                       |
| Allocated:             10 / 10                                |
| Available:              0                                     |
|                                                                |
| No allocation capacity remains.                                |
| A newly eligible client cannot receive sponsored coverage      |
| until capacity is increased or an allocation is released.      |
|                                                                |
| [ View subscription options ]                                  |
+----------------------------------------------------------------+
```

## ALL_ELIGIBLE_CLIENTS

```text
+----------------------------------------------------------------+
| Manual Processing Coverage                                    |
+----------------------------------------------------------------+
| Mode:                  ALL ELIGIBLE CLIENTS                   |
| Eligible clients:      24                                     |
| Covered automatically: 24                                     |
| Future eligible clients: Automatically covered                 |
|                                                                |
| Eligibility is based on active consultant-client              |
| relationships.                                                 |
|                                                                |
| [ View Eligible Clients ]                                      |
+----------------------------------------------------------------+
```

There is no per-client allocation action in this mode.

## New eligible client

Selected mode:

```text
+----------------------------------------------------------------+
| New Eligible Client                                            |
+----------------------------------------------------------------+
| Client:                 New Client Ltd                         |
| Consultant relationship: ACTIVE                               |
| Sponsored coverage:       NOT YET ALLOCATED                   |
| Available capacity:       3                                   |
|                                                                |
| [ Allocate Coverage ]                                          |
+----------------------------------------------------------------+
```

All-eligible mode:

```text
+----------------------------------------------------------------+
| New Eligible Client                                            |
+----------------------------------------------------------------+
| Client:                 New Client Ltd                         |
| Consultant relationship: ACTIVE                               |
| Sponsored coverage:       AUTOMATICALLY COVERED               |
+----------------------------------------------------------------+
```

Relationship termination:

```text
+----------------------------------------------------------------+
| Client Coverage                                               |
+----------------------------------------------------------------+
| Client:                 Client A                              |
| Relationship:           ENDED                                 |
| Sponsored entitlement:  NOT ACTIVE                            |
|                                                                |
| Historical coverage information is retained.                  |
+----------------------------------------------------------------+
```

For selected mode, the UI must reflect the actual implemented allocation-release behaviour and must not promise automatic release unless implemented.

---

# 5. Coverage transitions

## Selected → All

```text
+------------------------------------------------------------------+
| Coverage transition                                             |
+------------------------------------------------------------------+
| Current mode:        SELECTED CLIENTS                           |
| New mode:            ALL ELIGIBLE CLIENTS                      |
| Existing allocations:     Preserved as historical state         |
| Current eligible clients: Covered automatically                  |
| Future eligible clients:  Covered automatically                  |
|                                                                  |
| [ Review ]                                                       |
+------------------------------------------------------------------+
```

Existing allocation/history must not be silently destroyed.

## All → Selected

```text
+------------------------------------------------------------------+
| Coverage transition                                             |
+------------------------------------------------------------------+
| Current mode:        ALL ELIGIBLE CLIENTS                      |
| New mode:            SELECTED CLIENTS                           |
| Existing eligible clients:     [ count ]                        |
| New selected capacity:         [ configured quantity ]          |
|                                                                  |
| This change may require controlled reconciliation.              |
| No client is silently selected or removed.                      |
|                                                                  |
| [ Review reconciliation ]                                       |
+------------------------------------------------------------------+
```

If the implemented system does not support an operation, the UI must not pretend that it does.

---

# 6. State and authorization rules

### Commercial state

```text
ENTITLED
NOT ENTITLED
DIRECT
SPONSORED
DIRECT + SPONSORED
NOT COVERED
```

### Consultant coverage modes

```text
SELECTED CLIENTS
ALL ELIGIBLE CLIENTS
```

### Operational state

```text
GOVERNANCE ENABLED
GOVERNANCE DISABLED
PROCESSING ENTITY CONFIGURED
PROCESSING ENTITY NOT CONFIGURED
```

Do not create new backend semantic statuses merely for presentation.

### Visibility

**Platform Admin:** full commercial + operational state according to the existing Admin authorization model.

**Consultant:** only their firm's coverage, their authorized consultant-client relationships, and their own allocation/capacity state.

**Customer:** only their organization's effective entitlement and authorized operational state.

Cross-tenant data must never be exposed.

---

# 7. Empty and error states

Admin:

```text
No consultant coverage configured for this organization.

Configure the firm's commercial coverage first.
```

Consultant:

```text
No Manual Processing consultant coverage is currently active.

Your firm's subscription coverage will appear here when configured.
```

Customer:

```text
Manual Processing is not currently available through your
commercial coverage.
```

Allocation error:

```text
Unable to allocate this client.

Possible reasons:
- the client is not eligible;
- allocation capacity is exhausted;
- coverage is no longer active.

Refresh the coverage state and try again.
```

Unauthorized/cross-tenant failures must not reveal whether another organization's records exist.

---

# 8. Navigation and implementation boundary

Use the existing CarbonTally Admin/Operations, customer, and consultant surfaces. Do not create a new persona or parallel application.

The Admin experience should make the distinction visible:

```text
[ Commercial Coverage ] [ Operational Routing ] [ Assignments ]
```

The exact placement can follow the existing CarbonTally navigation architecture.

The existing backend CT-MP-SUB-003 implementation is the starting point.

This document does **not** authorize:

- production deployment;
- production migration;
- production configuration;
- new billing architecture;
- new commercial rules;
- new authorization model;
- new persona;
- automatic PE assignment;
- deletion of historical data.

---

# 9. Deliberately unresolved commercial decisions

The governing PO specification leaves the following outside this UI design:

- final pricing;
- final plan names;
- final capacity tier quantities;
- payment provider;
- payment mechanics;
- proration;
- refund policy;
- grace period;
- tax/VAT;
- custom enterprise pricing;
- independent capacity purchase;
- unused capacity carryover.

The UI must display configured subscription values rather than inventing these decisions.

---

# 10. UI acceptance criteria

The eventual implementation must demonstrate:

1. Admin can distinguish commercial coverage from operational routing.
2. Admin can distinguish direct and sponsored entitlement.
3. Admin can understand selected capacity/allocation.
4. Admin can understand all-eligible coverage.
5. Consultant can understand purchased coverage.
6. Consultant can understand remaining selected capacity.
7. Consultant can see covered clients within authorization scope.
8. Consultant can distinguish selected from all-eligible coverage.
9. Customer can understand why Manual Processing is available.
10. Customer can distinguish direct versus sponsored coverage where appropriate.
11. Customer cannot see internal consultant commercial data.
12. FIN-06 remains distinct from commercial entitlement.
13. Processing Entity remains distinct from commercial coverage.
14. Empty/error states are explicit.
15. Cross-tenant information is not exposed.
16. No UI creates a commercial rule not contained in the governing PO specification.
17. Existing CarbonTally navigation and authorization architecture are preserved.

---

# 11. Governance status

| Item | Status |
|---|---|
| CT-PO-MP-SUB-003 commercial model | **PO APPROVED / AUTHORITATIVE** |
| CT-UX-MP-SUB-003 UI/UX design | **PROPOSED FOR PO APPROVAL** |
| CT-MP-SUB-003 backend | **IMPLEMENTED / READY FOR INDEPENDENT VERIFICATION** |
| UI implementation | **NOT YET AUTHORIZED** |
| CoStrict verification | **NOT YET STARTED** |
| Git push | **NOT AUTHORIZED** |
| Production migration | **NOT AUTHORIZED** |
| Production deployment | **NOT AUTHORIZED** |

## Recommended PO disposition

**APPROVE CT-UX-MP-SUB-003 as the UI/UX implementation authority.**

After explicit PO approval, create a separate uniquely identified Cline implementation prompt. CoStrict should later verify the implemented product against both the governing commercial specification and this approved UI/UX specification.

**No production or code change is authorized by this document.**
