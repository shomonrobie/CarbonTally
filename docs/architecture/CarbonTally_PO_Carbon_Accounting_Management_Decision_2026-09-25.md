# CarbonTally Product Owner Decision Record
## Carbon Accounting Management + Customer-Owned Emissions Data

**Document ID:** CT-PO-CARBON-ACCOUNTING-MANAGEMENT-001  
**Status:** APPROVED — PRODUCT BASELINE  
**Date:** 2026-09-25  
**Applies to:** CarbonTally P17 and subsequent implementation phases  
**Production authorization:** NOT AUTHORIZED

---

## 1. Purpose

This document records the Product Owner decisions for CarbonTally's Scope 1, Scope 2, and Scope 3 carbon-accounting management architecture.

> CarbonTally is a multi-tenant carbon-accounting platform. Customers may provide and manage their organization's carbon-accounting data, while CarbonTally governs the accounting system, methodology, validation, review, reportability, and reporting controls.

CarbonTally Staff/Admin are **not** the only users permitted to enter or maintain emissions data.

---

## 2. Core Product Decision

CarbonTally will provide one unified:

**Carbon Accounting Management System**

containing:

- Scope 1
- Scope 2
- Scope 3

These are domain modules, not three independent systems.

They share the accounting core:

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

Scope-specific accounting rules remain domain-specific.

---

## 3. Two Primary Interaction Planes

### A. CarbonTally Admin/Staff Management Plane

Authorized CarbonTally staff can manage accounting operations across organizations according to their permissions.

Capabilities include:

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
- organization accounting capabilities
- audit/history review
- reporting controls

### B. Customer Carbon Accounting Workspace

Customers can, when enabled:

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

Customer access is capability-controlled by CarbonTally.

---

## 4. Customer Accounting Capability Policy

Customer carbon accounting is a **per-organization capability**.

It must NOT be a global hard-coded behavior.

Conceptually:

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

The exact database representation must be determined during P17 architecture work after inspection of the existing repository/schema.

Do not create duplicate policy systems if equivalent capabilities already exist.

---

## 5. Mandatory Existing-First Discovery

Before implementing ANY feature in this document, Cline MUST inspect the repository and determine:

1. What already exists.
2. What partially exists.
3. What is implemented but disconnected.
4. What exists only in the backend.
5. What exists only in the UI.
6. What exists in database/schema/migrations.
7. What exists in API routes/services.
8. What exists in customer workflows.
9. What exists in Admin/Staff workflows.
10. What is missing completely.
11. What is obsolete or duplicated.
12. What can be extended safely instead of rebuilt.

Cline MUST NOT assume a feature is missing because it is not visible in one UI.

For every material feature, trace:

    UI
      -> API
      -> service/domain logic
      -> database
      -> RLS/authorization
      -> audit/provenance
      -> tests

If an equivalent feature already exists, extend/refactor it rather than creating a parallel implementation.

---

## 6. Mandatory UI/UX Requirement

All features described in this document require actual UI/UX implementation where applicable.

Do NOT implement backend-only feature flags and call the feature complete.

For every customer/staff capability that is implemented, provide the corresponding user experience, including where applicable:

- navigation
- dashboards
- forms
- tables
- status indicators
- review queues
- empty states
- validation/error states
- permission-aware controls
- evidence views
- calculation views
- activity history
- audit/history views
- confirmation dialogs
- loading states
- disabled/locked states
- responsive behavior

Use the existing CarbonTally design system where one exists. Do not create an unrelated visual system.

---

## 7. Customer Data Does Not Automatically Become Reportable

Customer-entered data must use the controlled accounting lifecycle.

    DRAFT
      ↓
    SUBMITTED
      ↓
    VALIDATED
      ↓
    CALCULATED
      ↓
    REVIEW
      ↓
    APPROVED
      ↓
    REPORTABLE

Where applicable, rejection, correction, invalidation, and supersession paths must exist.

Customer submission must never silently bypass required accounting controls.

---

## 8. Data Ownership vs Accounting Governance

These are separate concepts.

**Customer:** provides/owns the organization's operational information.

**CarbonTally:** provides and governs the accounting system.

**Processing engine:** transforms submitted information into controlled accounting results.

Therefore:

    CUSTOMER DATA
          ↓
    INGESTION
          ↓
    NORMALIZATION
          ↓
    VALIDATION
          ↓
    FACTOR / METHODOLOGY
          ↓
    CALCULATION
          ↓
    REVIEW
          ↓
    REPORTABILITY
          ↓
    REPORTING

No customer permission may create an uncontrolled shortcut around this pipeline.

---

## 9. Customer Permissions Do Not Equal Accounting Authority

A customer may be allowed to enter data without being allowed to:

- change governed methodology
- modify CarbonTally-controlled emission factors
- bypass validation
- bypass mandatory review
- make invalid calculations reportable
- silently mutate historical accounting results
- access another organization
- manipulate accounting snapshots
- alter governance configuration

Customer permissions must be granular.

---

## 10. Auditable Customer Changes

Customer edits must preserve accounting history.

For example:

    Original: 10,000 kWh
    New:      12,000 kWh

The system must preserve, where applicable:

- actor
- timestamp
- original value
- new value
- reason
- source/evidence
- resulting calculation impact
- reportability impact

Historical accounting results must not silently mutate.

Use existing CarbonTally audit/provenance mechanisms where possible.

---

## 11. Supported Operating Models

The same architecture must support:

### Managed

Customer accounting entry may be disabled.

    Customer
       ↓
    provides documents/data
       ↓
    CarbonTally Staff
       ↓
    process/review/report

### Collaborative

    Customer ↔ CarbonTally Staff
              ↓
        Shared accounting workflow

### Self-Service / Advanced

    Customer
       ↓
    accounting workflow
       ↓
    CarbonTally governance

These are configurations of one product, not separate systems.

---

## 12. Role/Capability Model

Do not hard-code the architecture around only Admin, Staff, and Customer.

The architecture must accommodate capability-based authorization.

Potential CarbonTally roles:

- CarbonTally Admin
- CarbonTally Accounting Manager
- CarbonTally Reviewer
- CarbonTally Processor

Potential customer roles:

- Customer Sustainability Manager
- Customer Contributor
- Customer Reviewer

The final role taxonomy must be reconciled with the existing authorization model. Do not create a duplicate authorization system.

---

## 13. Scope 1 Product Requirements

Scope 1 customer/staff workflows must support applicable direct-emission activity data.

Potential domains include:

- stationary combustion
- mobile combustion
- refrigerants/fugitives
- company vehicles
- other applicable Scope 1 activities

The implementation must inspect the existing Scope 1 model first.

Required management UX, where applicable:

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

Do not invent unsupported Scope 1 categories if the existing accounting contract defines a different taxonomy.

---

## 14. Scope 2 Product Requirements

Scope 2 requires dedicated treatment for:

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

Customer-provided contractual-instrument information must pass applicable CarbonTally validation/governance.

Required UX includes, where applicable:

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

Do not implement contractual instruments as a superficial text field if the P17 contract requires governed instrument records.

---

## 15. Scope 3 Product Requirements

Scope 3 must support the full 15-category accounting architecture defined by P17.

Customers must be able to contribute relevant data where enabled.

The UX must support category-specific workflows rather than forcing every category into one generic form.

Potential contributors include:

- procurement
- finance
- facilities
- HR
- travel
- logistics
- waste
- suppliers

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

The implementation must reconcile the exact Scope 3 category model with the P17 accounting contract before coding.

---

## 16. Supplier Data

Supplier information must be able to enter the same controlled accounting pipeline.

    Customer
       │
       ├── Own activity data
       │
       └── Supplier data
              ↓
        CarbonTally
              ↓
          Validation
              ↓
          Attribution
              ↓
         Calculation
              ↓
          Reporting

Supplier attribution and ownership must respect tenant boundaries.

---

## 17. CarbonTally Staff Management UX

The Staff/Admin management plane should provide an operational accounting workspace.

Expected navigation, reconciled with the existing application:

    Carbon Accounting
      ├── Overview
      ├── Scope 1
      ├── Scope 2
      ├── Scope 3
      ├── Customer Data
      ├── Review Queue
      ├── Exceptions
      ├── Factors
      ├── Methodologies
      ├── Suppliers
      ├── Evidence
      ├── Accounting Controls
      └── Reporting

Do not duplicate existing navigation. Cline must inspect the current application and integrate into the existing information architecture.

---

## 18. Customer Workspace UX

The customer workspace should provide, where enabled:

    Carbon Accounting
      ├── Overview
      ├── Scope 1
      ├── Scope 2
      ├── Scope 3
      ├── Upload Data
      ├── Evidence
      ├── Review Required
      ├── Calculations
      ├── Data Quality
      └── Reports

Sections must be capability-aware.

If Scope 3 customer entry is disabled, the customer should not receive a misleading empty Scope 3 management interface.

---

## 19. Organization Capability Management UX

Authorized CarbonTally staff need an organization-level settings interface for accounting capabilities.

Examples:

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

The final control list must be reconciled with the actual P17 architecture and existing authorization system.

---

## 20. Security Requirements

Every customer-facing accounting operation must be tenant-scoped.

Verify:

- organization access
- role/capability access
- object-level access
- RLS where applicable
- API authorization
- UI authorization
- cross-tenant denial
- staff-vs-customer authority
- audit actor correctness

Frontend hiding is NOT authorization.

Backend/API/database enforcement remains mandatory.

---

## 21. No Parallel Accounting Engines

Cline must not create:

- a customer calculation engine separate from staff calculation
- a customer factor system separate from governed factors
- a customer reportability system separate from accounting reportability
- a customer audit system separate from CarbonTally audit
- separate Scope 1/2/3 accounting engines if shared infrastructure already exists

Extend the existing architecture.

---

## 22. No Duplicate Data Models

Before creating any table/model/service, inspect:

- current schema
- migrations
- API models
- services
- existing UI data models
- existing customer accounting features
- existing Admin/Staff accounting features
- authorization/RLS

If an equivalent model exists, extend it.

Document why any new model is required.

---

## 23. UI/UX Acceptance Standard

A feature is NOT complete merely because:

- a table exists
- an API returns 200
- a database row can be inserted
- a feature flag exists
- a backend service exists

Completion requires the appropriate end-to-end path:

    UI
      ↓
    API
      ↓
    authorization
      ↓
    domain/service
      ↓
    database
      ↓
    audit/provenance
      ↓
    calculation/reportability where applicable
      ↓
    UI reflects resulting state

At least one realistic workflow must be exercised for each implemented major capability.

---

## 24. P16 Regression Protection

P17 implementation must not regress P16 controls, including:

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

Cline must inspect the P16 final verification and current code before changing accounting foundations.

---

## 25. Implementation Method

### Phase A — Discovery

Inspect:

- repository
- current branch
- migrations
- schema
- APIs
- services
- accounting engines
- customer UI
- staff UI
- authorization
- RLS
- tests
- documentation
- P16 implementation
- P17 architecture contract

Produce:

| Feature | Existing | Partial | Backend only | UI only | Missing | Reusable | Notes |
|---|---|---|---|---|---|---|---|

Do not implement during discovery.

### Phase B — Gap Reconciliation

For every required capability:

- identify existing implementation
- identify missing pieces
- identify conflicts
- identify duplicate implementations
- identify migration/schema changes
- identify API changes
- identify UI changes
- identify tests

### Phase C — Architecture Reconciliation

Update the P17 architecture/contract artifacts as necessary.

Do not silently change the product contract.

If a material contradiction is discovered, STOP and report it before implementation.

### Phase D — Implementation

Implement approved gaps.

Backend and UI/UX are both required.

### Phase E — Verification

Verify:

- customer access
- staff access
- disabled capability behavior
- enabled capability behavior
- cross-tenant denial
- auditability
- reportability
- calculations
- UI state
- error state
- empty state
- loading state
- permission state

### Phase F — Final Report

Cline MUST write a Markdown report containing:

- task ID
- starting commit
- ending commit
- discovery results
- existing features reused
- features implemented
- features deliberately not implemented
- backend changes
- schema changes
- API changes
- authorization/RLS changes
- UI/UX changes
- tests run
- test results
- known failures
- regressions
- remaining gaps
- exact files changed
- exact acceptance status
- final verdict

---

## 26. Mandatory Existing-vs-Missing Classification

Every major requirement must be classified as exactly one of:

- EXISTS — VERIFIED
- PARTIAL — EXTENDED
- EXISTS BUT DISCONNECTED — WIRED
- DUPLICATE — CONSOLIDATED
- MISSING — IMPLEMENTED
- DEFERRED — JUSTIFIED
- BLOCKED — EVIDENCE REQUIRED

Cline MUST NOT report "Implemented" without first establishing the previous state.

---

## 27. Production Safety

Production deployment is NOT authorized by this document.

Cline must not:

- deploy production
- modify production data
- run production migrations
- claim production readiness
- change production configuration

Use development/test/disposable environments as appropriate.

---

## 28. Product Owner Acceptance Principle

The objective is not to create the maximum number of screens.

The objective is to create a coherent CarbonTally accounting product where:

1. Customers can contribute their own emissions data when CarbonTally enables it.
2. CarbonTally Staff retains appropriate accounting governance.
3. Scope 1, Scope 2 and Scope 3 share a controlled accounting core.
4. Scope-specific rules remain correctly separated.
5. Customer data cannot bypass accounting controls.
6. Important accounting actions are auditable.
7. Tenant isolation is enforced.
8. The UI accurately reflects permissions and accounting state.
9. Existing CarbonTally functionality is reused rather than duplicated.
10. The implementation is verified rather than assumed.

---

## 29. Final PO Decision

**APPROVED:**

> CarbonTally will be a multi-tenant carbon accounting platform where customers can contribute and manage their organization's emissions data when enabled by CarbonTally, while CarbonTally retains control of accounting governance, methodology, validation, review, reportability, and platform administration.

CarbonTally will provide one unified **Carbon Accounting Management System** with Scope 1, Scope 2 and Scope 3, plus:

- CarbonTally Admin/Staff Management
- Customer Carbon Accounting Workspace

Customer capabilities are organization-level and configurable.

All implemented capabilities require appropriate UI/UX as well as backend/domain implementation.

Before implementation, Cline MUST determine what already exists and what does not exist.

---

## 30. Mandatory Cline Operating Rules

Every implementation task based on this document must:

1. Have a unique task identifier.
2. Inspect before implementing.
3. Reuse existing functionality where appropriate.
4. Never invent missing data.
5. Never silently change accounting semantics.
6. Never create duplicate systems without documented justification.
7. Implement required UI/UX, not backend-only stubs.
8. Verify authorization at backend/database boundaries.
9. Run appropriate regression tests.
10. Produce a Markdown completion report.
11. Clearly distinguish PASS, PARTIAL, FAIL, BLOCKED, and DEFERRED.
12. Never authorize production.

---

## Document Control

**Product Owner status:** APPROVED  
**Architecture status:** To be reconciled with P17 contract before implementation  
**Implementation status:** Not authorized by this document alone  
**Production status:** NOT AUTHORIZED  
**Next action:** Amend/reconcile P17 architecture, then perform existing-vs-missing discovery before implementation.
