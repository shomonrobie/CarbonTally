# CarbonTally — Post-P17-ARCH-01 Product Owner Decision Record
## Unified Carbon Accounting Management System (CAMS)

**Document ID:** CT-PO-P17-POST-ARCH-DECISIONS-20260925  
**Date:** 2026-09-25  
**Status:** APPROVED PRODUCT-OWNER DECISIONS  
**Baseline prompt:** `P17-ARCH-01-20250925-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT`  
**Production authorization:** NOT AUTHORIZED

---

# 1. Purpose

This document captures the Product Owner decisions made **after the P17 architecture/contract prompt was given to Cline**.

It is intended to be a future implementation reference and an amendment/extension to the P17 architecture contract.

The decisions in this document concern the product structure and operating model for a **Unified Carbon Accounting Management System (CAMS)** covering:

- Scope 1
- Scope 2
- Scope 3
- CarbonTally Admin/Staff
- Direct CarbonTally customer organizations
- Consultant organizations
- Consultant-managed client organizations
- Customer-owned emissions data
- Delegated consultant access
- Organization-level capabilities
- Accounting governance
- UI/UX

This document does not replace the original P17 architecture contract. It records decisions made subsequently that must be reconciled into that contract before implementation of the affected areas.

---

# 2. Foundational Product Decision

## APPROVED

CarbonTally will have **one Unified Carbon Accounting Management System**.

It will not have:

- a separate Staff accounting system
- a separate direct-customer accounting system
- a separate consultant accounting system
- a separate consultant-client accounting system
- separate Scope 1, Scope 2 and Scope 3 accounting products

Instead:

```text
                         CARBONTALLY PLATFORM
                                  |
                    UNIFIED CARBON ACCOUNTING
                       MANAGEMENT SYSTEM
                                  |
          +-----------------------+-----------------------+
          |                       |                       |
     CarbonTally             Direct Customer          Consultant
     Admin/Staff             Organization             Organization
                                                          |
                                                    Client Portfolio
                                                          |
                                               +----------+----------+
                                               |          |          |
                                            Client A   Client B   Client C
```

All actors use the same underlying accounting architecture.

---

# 3. Shared Accounting Core

Scope 1, Scope 2 and Scope 3 are domain modules over a shared accounting core.

Shared capabilities include:

- activity data
- emission-factor governance
- calculations
- evidence
- provenance
- validation
- review
- reportability
- audit trail
- organization/tenant security
- reporting
- idempotency where applicable

Scope-specific accounting rules remain domain-specific.

There must not be duplicate accounting engines merely because different actors access the system.

---

# 4. Two Primary Interaction Planes

The product must provide two major interaction planes.

## 4.1 CarbonTally Admin/Staff Management Plane

Authorized CarbonTally staff can operate across customer organizations according to their role and permissions.

Expected capabilities include:

- customer submission review
- exception resolution
- factor governance
- methodology governance
- customer-specific factor governance
- controlled accounting overrides
- Scope 1 management
- Scope 2 management
- Scope 3 management
- contractual-instrument management
- supplier management
- evidence management
- reportability controls
- organization accounting capability management
- audit/history review
- reporting controls

Staff access must still be authorization-controlled. "Staff" does not automatically mean unrestricted access to every customer organization.

## 4.2 Customer Carbon Accounting Workspace

An organization may be allowed to:

- enter activity data
- upload files
- provide evidence
- correct permitted submissions
- manage permitted Scope 1 data
- manage permitted Scope 2 data
- manage permitted Scope 3 data
- provide supplier information
- participate in review
- view calculations
- view data quality
- prepare reporting information

Customer access is controlled by organization capability and user permissions.

---

# 5. Customer-Owned Emissions Data

## APPROVED

Customers are **not required to rely exclusively on CarbonTally Staff for emissions-data entry**.

Customer organizations may own and contribute their own emissions data.

This existing/provisioned customer-emissions-data capability should be treated as a **first-class product capability**, not removed or treated as an exception.

The product principle is:

> Customer owns/provides operational data; CarbonTally governs the accounting system in which that data is processed.

---

# 6. Data Ownership vs Accounting Governance

These are explicitly separate concepts.

### Customer

Provides/owns the organization's operational information.

### CarbonTally

Provides and governs the accounting system.

### CarbonTally processing engine

Transforms submitted information into controlled accounting results.

The conceptual pipeline is:

```text
CUSTOMER DATA
      |
INGESTION
      |
NORMALIZATION
      |
VALIDATION
      |
FACTOR / METHODOLOGY
      |
CALCULATION
      |
REVIEW
      |
REPORTABILITY
      |
REPORTING
```

No customer permission may create an uncontrolled shortcut around this pipeline.

---

# 7. Customer Capability Must Be CarbonTally-Controlled

## APPROVED

Customer carbon accounting is configurable **per organization**.

It must not be a single global hard-coded behavior.

The architecture must support organization-level accounting capabilities/policies.

Conceptually:

```text
Organization Accounting Policy

customer_accounting_enabled

scope1_customer_entry
scope2_customer_entry
scope3_customer_entry

customer_edit_submission
customer_upload_evidence
customer_supplier_data

customer_review
customer_approval

staff_review_required
staff_approval_required
```

The final database representation must be reconciled with the existing schema and P17 architecture.

Do not create a duplicate policy system if equivalent capability infrastructure already exists.

---

# 8. Customer Permission Does Not Equal Accounting Authority

A customer being permitted to enter data does not automatically authorize the customer to:

- change governed methodology
- modify CarbonTally-controlled emission factors
- bypass validation
- bypass mandatory review
- make invalid calculations reportable
- silently mutate historical accounting results
- access another organization
- manipulate accounting snapshots
- alter platform accounting governance

Customer permissions must therefore be granular.

---

# 9. Customer Data Is Not Automatically Reportable

Customer-entered data must pass the controlled accounting lifecycle.

Conceptually:

```text
DRAFT
  |
SUBMITTED
  |
VALIDATED
  |
CALCULATED
  |
REVIEW
  |
APPROVED
  |
REPORTABLE
```

Where applicable, the system must support:

- rejection
- correction
- invalidation
- supersession

Customer submission must never silently bypass required accounting controls.

---

# 10. Auditable Customer Changes

Customer edits must preserve the accounting history required for auditability.

Example:

```text
Original: 10,000 kWh
New:      12,000 kWh
```

Where applicable, preserve:

- actor
- timestamp
- original value
- new value
- reason
- source/evidence
- resulting calculation impact
- reportability impact

Historical accounting results must not silently mutate.

Existing CarbonTally audit/provenance mechanisms should be reused.

---

# 11. Supported Operating Models

The same CAMS architecture must support three operating models.

## 11.1 Managed

Customer accounting entry may be disabled.

```text
Customer
   |
provides documents/data
   |
CarbonTally Staff
   |
process/review/report
```

## 11.2 Collaborative

```text
Customer <-> CarbonTally Staff
          |
    Shared accounting workflow
```

## 11.3 Self-Service / Advanced

```text
Customer
   |
accounting workflow
   |
CarbonTally governance
```

These are configurations of one product, not separate products.

---

# 12. Consultant Organizations Are First-Class CarbonTally Customers

## APPROVED

A CarbonTally customer may be a consulting organization.

Example:

```text
Green Advisory Ltd.
       |
       +-- Client A
       +-- Client B
       +-- Client C
```

The consultant is itself a CarbonTally organization and may have its **own** Scope 1/2/3 accounting.

The consultant also may manage client organizations when an explicit consultant-client relationship and appropriate delegated permissions exist.

---

# 13. Consultant Clients Remain Independent Organizations

## HARD PRODUCT DECISION

A consultant's client must remain an independent organization.

Do not model a consultant's client merely as a sub-user-space inside the consultant organization.

Conceptually:

```text
Green Advisory
organization_id = A

ABC Manufacturing
organization_id = B
```

With a separate relationship:

```text
consultant_client_relationship

consultant_org_id = A
client_org_id     = B
status            = active
```

This preserves:

- tenant isolation
- data ownership
- auditability
- reporting boundaries
- client independence
- future billing
- future client migration
- future direct CarbonTally relationship

---

# 14. Consultant Access Is Delegated Access

A consultant does not become the owner of the client's accounting data.

The consultant receives explicit, auditable delegated access to the client organization.

Conceptually:

```text
Client Organization
        |
        | grants/accepts
        v
Consultant Organization
        |
        v
Delegated client access
```

The exact invitation/consent workflow is an architecture/implementation detail, but the product principle is fixed:

> Consultant access to a client organization must be explicitly authorized and auditable.

---

# 15. Consultant Gets the Same Accounting Capabilities

## APPROVED

If a direct organization can use:

- Scope 1
- Scope 2
- Scope 3
- evidence
- suppliers
- calculations
- review
- reporting

then an authorized consultant should be able to operate the **same accounting functionality for an authorized client**, subject to delegated permissions.

There is no "consultant version" of the accounting engine.

The difference is:

- actor
- organization context
- role
- capability
- delegated relationship

—not accounting logic.

---

# 16. Consultant Client Context Switching

The consultant UX should support selecting a client organization.

Conceptually:

```text
Green Advisory

Client:
[ ABC Manufacturing v ]

--------------------------------

Carbon Accounting
  Overview
  Scope 1
  Scope 2
  Scope 3
  Evidence
  Suppliers
  Review
  Reporting
```

Changing the selected client changes the organization context.

It must not be implemented as a superficial UI filter.

Backend/API/database authorization must enforce the selected organization context.

---

# 17. Consultant Portfolio Management

Consultants require an additional management layer that ordinary organizations do not.

Conceptually:

```text
Consultant Workspace
|
+-- Portfolio
|   +-- Client A
|   +-- Client B
|   +-- Client C
|
+-- Client Onboarding
+-- Client Tasks
+-- Review Queue
+-- Data Collection
+-- Carbon Accounting
+-- Reporting
```

This is a consultant-management layer **on top of CAMS**.

It is not a second accounting engine.

---

# 18. Consultant Permissions Must Be Client-Specific

Consultant access must be configurable per client.

Example:

### Client A

Consultant can:

- enter data
- upload evidence
- perform mapping
- calculate
- review

but cannot:

- approve reporting

### Client B

Consultant can:

- enter data
- upload evidence
- calculate
- prepare reports

Client retains final approval.

### Client C

Consultant has read-only access.

Therefore:

```text
Consultant <-> Client
             |
             +-- delegated capabilities
```

Do not model:

```text
Consultant = Client Admin
```

as the general rule.

---

# 19. Consultant Can Have Its Own Carbon Accounting

## APPROVED

A consultant is also an organization.

Therefore it can have its own:

- Scope 1
- Scope 2
- Scope 3
- evidence
- suppliers
- calculations
- reviews
- reports

Example:

```text
Green Advisory
|
+-- Own Carbon Accounting
|   +-- Scope 1
|   +-- Scope 2
|   +-- Scope 3
|
+-- Client Portfolio
    +-- ABC
    +-- XYZ
    +-- DEF
```

Its own emissions must remain completely separate from client emissions.

---

# 20. A Direct Customer Can Become a Consultant

## APPROVED

An organization should not need a new CarbonTally product/account merely because it begins providing consulting services to other organizations.

Conceptually:

```text
ABC Sustainability Ltd.
|
+-- Own Carbon Accounting
|
+-- Client 1
+-- Client 2
+-- Client 3
```

A capability such as:

```text
consultant_features_enabled = true
```

may enable the additional portfolio/client-management layer.

The exact representation must be reconciled with the existing organization/capability architecture.

---

# 21. Organization Types and Relationships

The architecture should distinguish organization identity from relationships.

Do not permanently encode every possible business relationship as a mutually exclusive organization type.

A likely model is:

```text
organization
    organization_type

organization_relationship
    relationship_type
```

For example:

```text
Green Advisory
type = CONSULTANT

ABC Manufacturing
type = ORGANIZATION

relationship:
Green Advisory -> ABC Manufacturing
type = CONSULTANT_CLIENT
```

This allows ABC Manufacturing to later become a direct CarbonTally customer without restructuring its accounting data.

The final implementation must inspect and reuse any existing organization/relationship architecture.

---

# 22. Source Actor Must Be Recorded

For an accounting record, the system must distinguish the organization that owns the data from the person/organization that entered it.

Example: consultant enters ABC's electricity data.

```text
data_owner:
    ABC Manufacturing

entered_by:
    Green Advisory / User X

acting_for:
    ABC Manufacturing

source:
    Consultant submission
```

If ABC entered it:

```text
data_owner:
    ABC Manufacturing

entered_by:
    ABC / User Z

acting_for:
    ABC Manufacturing

source:
    Customer submission
```

This principle applies throughout the accounting lifecycle.

---

# 23. Audit Trail Must Capture Acting Context

Where applicable, the audit model should distinguish:

- who performed the action
- which organization they were acting for
- which organization owns the data
- what changed
- when
- why
- what accounting result was affected

This is especially important for consultant-client operations.

---

# 24. Reporting Belongs to the Client Organization

If a consultant prepares a report for ABC:

```text
Report organization:
    ABC Manufacturing

Prepared by:
    Green Advisory / Jane

Accounting period:
    FY2026
```

The report belongs to ABC's accounting context, not the consultant's organization.

The same principle applies to:

- calculations
- evidence
- activity data
- reporting versions
- reportability
- audit history

---

# 25. Evidence Belongs to the Organization Whose Accounting It Supports

If Green Advisory uploads an electricity invoice for ABC:

```text
Evidence owner:
    ABC Manufacturing

Uploaded by:
    Green Advisory / Jane

Acting for:
    ABC Manufacturing
```

The evidence must remain within ABC's accounting/tenant context.

---

# 26. Scope 1 Management

Scope 1 must use the unified accounting system.

Potential applicable domains include:

- stationary combustion
- mobile combustion
- refrigerants/fugitives
- company vehicles
- other applicable Scope 1 activities

The exact taxonomy must be reconciled with the existing/P17 Scope 1 accounting contract.

Required UX, where applicable:

- Scope 1 overview
- activity records
- data entry
- uploads
- evidence
- factor selection/governance
- calculations
- review
- exceptions
- reportability
- history

Do not invent duplicate Scope 1 taxonomy where an approved existing taxonomy exists.

---

# 27. Scope 2 Management

Scope 2 must support:

- purchased electricity
- purchased heat
- purchased steam
- purchased cooling where applicable
- location-based accounting
- market-based accounting
- contractual instruments
- supplier-specific information
- instrument evidence
- factor selection
- accounting-rule validation

Required UX, where applicable:

- Scope 2 overview
- energy activity management
- location-based calculation view
- market-based calculation view
- contractual instrument management
- instrument evidence
- factor/factor-set context
- review/exception queue
- calculation comparison
- reportability state

Contractual instruments must be modeled as governed accounting entities if required by the P17 contract, not reduced to an uncontrolled text field.

---

# 28. Scope 3 Management

Scope 3 must support the full 15-category architecture defined by P17.

Customers and authorized consultants must be able to contribute relevant data where enabled.

Required UX includes, as applicable:

- Scope 3 overview
- category navigation
- Category 1–15 management
- category-specific data entry
- uploads
- supplier data
- estimation/methodology context
- evidence
- validation
- review
- exceptions
- reportability
- history

Scope 3 must support distributed organizational data collection rather than assuming CarbonTally Staff manually enters every category.

Potential contributors include:

- procurement
- finance
- facilities
- HR
- travel
- logistics
- waste
- suppliers

The exact category model must be reconciled with the P17 contract before implementation.

---

# 29. Supplier Data

Supplier information must be able to enter the same controlled accounting pipeline.

```text
Customer
   |
   +-- Own activity data
   |
   +-- Supplier data
          |
          v
      CarbonTally
          |
      Validation
          |
      Attribution
          |
      Calculation
          |
      Reporting
```

Supplier attribution and ownership must respect tenant boundaries.

---

# 30. Staff Management UX

CarbonTally Staff/Admin should have an operational accounting workspace.

Conceptually:

```text
Carbon Accounting
|
+-- Overview
+-- Scope 1
+-- Scope 2
+-- Scope 3
+-- Customer Data
+-- Review Queue
+-- Exceptions
+-- Factors
+-- Methodologies
+-- Suppliers
+-- Evidence
+-- Accounting Controls
+-- Reporting
```

This must be reconciled with existing CarbonTally navigation.

Do not create duplicate navigation or parallel management modules.

---

# 31. Direct Customer UX

A direct organization should have a customer accounting workspace such as:

```text
Carbon Accounting
|
+-- Overview
+-- Scope 1
+-- Scope 2
+-- Scope 3
+-- Upload Data
+-- Evidence
+-- Review Required
+-- Calculations
+-- Data Quality
+-- Reports
```

Available sections depend on organization capabilities and user permissions.

---

# 32. Consultant UX

A consultant needs both:

1. its own Carbon Accounting workspace
2. a client portfolio/delegated-access workspace

Conceptually:

```text
My Organization
|
+-- My Carbon Accounting
|   +-- Scope 1
|   +-- Scope 2
|   +-- Scope 3
|
+-- Client Portfolio
    |
    +-- Client A
    |   +-- Carbon Accounting
    |   +-- Review
    |   +-- Reporting
    |
    +-- Client B
    |   +-- Carbon Accounting
    |
    +-- Client C
```

Client accounting must use the same CAMS.

---

# 33. Consultant Client UX

A consultant-managed client should receive the same applicable accounting capabilities as a direct CarbonTally organization.

The client may also have its own users.

Example:

```text
ABC Manufacturing
|
+-- Client Users
|   +-- Sustainability Manager
|   +-- Contributor
|   +-- Reviewer
|
+-- Consultant Delegation
    +-- Green Advisory
```

Both can operate in the same accounting context according to permissions.

---

# 34. Capability Matrix

The following is the approved conceptual model.

| Capability | Direct Customer | Consultant's Client | Consultant | CarbonTally Staff |
|---|---|---|---|---|
| Own Scope 1 | Yes, configurable | Yes, configurable | Yes | Yes, authorized |
| Own Scope 2 | Yes, configurable | Yes, configurable | Yes | Yes, authorized |
| Own Scope 3 | Yes, configurable | Yes, configurable | Yes | Yes, authorized |
| Upload evidence | Yes | Yes | Yes | Yes |
| Manage accounting data | Configurable | Configurable | Configurable per client | Yes, authorized |
| Supplier data | Yes | Yes | Yes | Yes |
| Review | Configurable | Configurable | Delegated | Yes |
| Reporting | Yes | Yes | On behalf of client | Yes |
| Client portfolio | No | No | Yes | Yes |
| Organization capability management | No | No | Limited/delegated | Yes |
| Global factor governance | No | No | No | Yes |
| Platform-wide governance | No | No | No | Yes |

This is a product-level capability model, not a final database schema.

---

# 35. Authorization Principle

Authorization is determined by:

```text
ACTOR
  +
ORGANIZATION CONTEXT
  +
ROLE
  +
CAPABILITY
  +
DELEGATED RELATIONSHIP
  =
PERMITTED ACTION
```

The UI must reflect this, but the backend/API/database must enforce it.

Frontend hiding is not authorization.

---

# 36. Tenant Isolation

All customer and consultant-client accounting operations must be tenant-safe.

A consultant's ability to operate Client A must not imply access to Client B.

Client A data must not leak into:

- Client B
- consultant's own accounting
- another consultant
- another CarbonTally customer

Cross-tenant authorization must be tested.

---

# 37. No Parallel Accounting Engines

Cline must not create:

- customer calculation engine
- consultant calculation engine
- client calculation engine
- staff calculation engine

There is one accounting engine.

Likewise, do not create separate:

- factor systems
- reportability systems
- audit systems
- evidence systems

where shared infrastructure is appropriate.

---

# 38. No Duplicate Data Models

Before creating any table/model/service, inspect:

- current schema
- migrations
- API models
- services
- existing accounting engines
- existing customer accounting features
- existing staff accounting features
- organization model
- consultant/client relationship model
- authorization/RLS
- existing UI data models

If an equivalent model exists:

> extend it rather than creating a parallel model.

If a new model is genuinely required, document why.

---

# 39. Mandatory Existing-vs-Missing Discovery

Before implementing these decisions, Cline MUST determine:

1. What already exists.
2. What partially exists.
3. What is backend-only.
4. What is UI-only.
5. What is implemented but disconnected.
6. What exists in migrations/schema.
7. What exists in API/services.
8. What exists in customer workflows.
9. What exists in Staff/Admin workflows.
10. What exists for consultants.
11. What exists for consultant clients.
12. What exists for organization relationships.
13. What exists for authorization/RLS.
14. What is missing.
15. What is duplicated.
16. What should be reused.

Cline must not assume a feature is missing because it is not visible in one interface.

For each major feature, trace:

```text
UI
 ↓
API
 ↓
Service/domain logic
 ↓
Database
 ↓
RLS/authorization
 ↓
Audit/provenance
 ↓
Tests
```

---

# 40. Mandatory Feature Classification

Every major requirement must be classified as one of:

- EXISTS — VERIFIED
- PARTIAL — EXTENDED
- EXISTS BUT DISCONNECTED — WIRED
- DUPLICATE — CONSOLIDATED
- MISSING — IMPLEMENTED
- DEFERRED — JUSTIFIED
- BLOCKED — EVIDENCE REQUIRED

Cline must not claim "Implemented" without first establishing the previous state.

---

# 41. Mandatory UI/UX Implementation

All applicable features in this specification require real UI/UX.

Backend-only feature flags, routes, tables, or services are not sufficient.

Required UI/UX includes, where applicable:

- navigation
- organization context
- client context for consultants
- dashboards
- data-entry forms
- tables
- filters
- status indicators
- review queues
- exceptions
- evidence views
- calculation views
- data-quality views
- activity history
- audit/history views
- permissions-aware controls
- loading states
- empty states
- error states
- disabled/locked states
- confirmation dialogs
- responsive behavior

Use the existing CarbonTally design system.

Do not create an unrelated UI system.

---

# 42. Organization Capability Management UX

Authorized CarbonTally staff should be able to manage organization accounting capabilities.

Conceptually:

```text
Customer Carbon Accounting        ON/OFF
Scope 1 Customer Entry            ON/OFF
Scope 2 Customer Entry            ON/OFF
Scope 3 Customer Entry            ON/OFF
Customer Evidence Upload          ON/OFF
Customer Supplier Data            ON/OFF
Customer Editing                  ON/OFF
Customer Review                   ON/OFF
Staff Review Required             ON/OFF
Staff Approval Required           ON/OFF
Consultant Features               ON/OFF
```

The exact controls must be reconciled with existing architecture.

Do not implement unnecessary duplicated switches.

---

# 43. Consultant Relationship Management UX

Where applicable, CarbonTally should provide controlled workflows for:

- consultant onboarding
- client invitation
- client acceptance/authorization
- delegated capability configuration
- client suspension
- relationship termination
- access review
- audit/history

The UI must make the acting organization/client context clear.

A consultant must never be allowed to unknowingly perform an action against the wrong client.

---

# 44. Organization Context Must Be Visible

Whenever a user can operate across organizations, the UI should clearly show:

- current organization
- current client, if applicable
- acting role/context
- relevant permission state

For consultants this is particularly important.

Example:

```text
Acting for:
ABC Manufacturing

Operator:
Green Advisory / Jane Smith
```

Exact UI treatment should follow the existing CarbonTally design system.

---

# 45. P16 Controls Must Remain Intact

P17/CAMS implementation must not regress the established P16 controls, including:

- calculation correctness
- factor precedence
- scope/year guards
- supplier attribution
- reportability lifecycle
- invalidation/supersession
- idempotency
- tenant isolation
- cross-organization authorization
- auditability

Cline must inspect the P16 final verification and current implementation before changing accounting foundations.

---

# 46. Production Safety

Nothing in this document authorizes production deployment.

Cline must not:

- deploy production
- modify production data
- run production migrations
- change production configuration
- claim production readiness

Use development, test, and disposable environments as appropriate.

---

# 47. Cline Operating Requirements

Every implementation task derived from this specification must:

1. Have a unique task identifier.
2. Inspect before implementing.
3. Reuse existing functionality where appropriate.
4. Never invent missing data.
5. Never silently change accounting semantics.
6. Never create duplicate systems without documented justification.
7. Implement required UI/UX.
8. Enforce authorization at backend/database boundaries.
9. Verify organization and delegated-client isolation.
10. Run appropriate regression tests.
11. Produce a Markdown completion report.
12. Clearly distinguish PASS, PARTIAL, FAIL, BLOCKED, and DEFERRED.
13. Never authorize production.

---

# 48. Required Cline Final Report

Every material implementation task must produce a Markdown report containing:

- unique task ID
- starting commit
- ending commit
- discovery results
- existing features reused
- features extended
- features implemented
- features deliberately not implemented
- backend changes
- schema changes
- API changes
- authorization/RLS changes
- organization/relationship changes
- UI/UX changes
- tests run
- test results
- known failures
- regressions
- remaining gaps
- exact files changed
- acceptance status
- final verdict

---

# 49. PO Acceptance Principle

The objective is not to create the maximum number of screens.

The objective is to create a coherent accounting platform where:

1. Customers can contribute their own emissions data when enabled.
2. CarbonTally Staff retains appropriate accounting governance.
3. Scope 1, Scope 2 and Scope 3 share a controlled accounting core.
4. Scope-specific rules remain correctly separated.
5. Consultants can manage their own accounting and authorized client accounting.
6. Consultant clients remain independent organizations.
7. Delegated access is explicit and auditable.
8. Customer/consultant data cannot bypass accounting controls.
9. Important accounting actions are auditable.
10. Tenant isolation is enforced.
11. The UI accurately reflects organization context and permissions.
12. Existing functionality is reused rather than duplicated.
13. The implementation is verified rather than assumed.

---

# 50. Final Product Owner Decision

The following is the authoritative product direction from the post-P17 discussion:

> **CarbonTally will operate one Unified Carbon Accounting Management System for Scope 1, Scope 2 and Scope 3. The system will serve CarbonTally Admin/Staff, direct customer organizations, consultant organizations, and consultant-managed client organizations through the same accounting core.**

> **Customers may contribute and manage their organization's emissions data when enabled by CarbonTally. Consultants may manage their own organization's accounting and, where explicitly authorized, the accounting of client organizations. Consultant clients remain independent organizations with their own data, evidence, calculations, reporting and audit history.**

> **The difference between Staff, Customer, Consultant and Consultant Client is determined by actor identity, organization context, role, capability and delegated relationship—not by separate accounting systems.**

> **All applicable features must have complete UI/UX implementation in addition to backend/domain implementation.**

> **Before implementation, Cline must inspect what exists, what is partial, what is disconnected, what is duplicated, and what is missing. Cline must reuse existing functionality wherever appropriate and must not invent parallel systems.**

---

# 51. Relationship to P17-ARCH-01

This document is a **post-contract Product Owner decision/amendment record**.

The original P17 prompt:

`P17-ARCH-01-20250925-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT`

remains the foundational Scope 2/Scope 3/full-accounting architecture contract.

Before affected implementation begins, the architecture must be reconciled so that the P17 contract explicitly incorporates:

- Unified Carbon Accounting Management System
- CarbonTally Staff/Admin management plane
- direct customer organization workspace
- consultant organization workspace
- consultant client organizations
- delegated consultant-client access
- organization-level capabilities
- customer-owned emissions data
- acting-for context
- organization ownership
- consultant portfolio management
- complete UI/UX
- existing-vs-missing discovery
- reuse/consolidation requirements

No implementation agent should silently reinterpret or omit these decisions.

---

## Document Control

**Document:** `CT-PO-P17-POST-ARCH-DECISIONS-20260925`  
**Status:** APPROVED PRODUCT-OWNER DECISIONS  
**Baseline:** `P17-ARCH-01-20250925-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT`  
**Production:** NOT AUTHORIZED  
**Implementation:** Must follow discovery → reconciliation → implementation → verification → report
