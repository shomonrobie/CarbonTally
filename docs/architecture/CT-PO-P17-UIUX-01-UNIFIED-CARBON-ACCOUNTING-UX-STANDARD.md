# CT-PO-P17-UIUX-01
# Unified Carbon Accounting Management System — UI/UX Standard

**Document ID:** CT-PO-P17-UIUX-01  
**Version:** 1.0.0  
**Date:** 2026-09-25  
**Status:** APPROVED PRODUCT-OWNER UI/UX STANDARD  
**Baseline Architecture Contract:** `P17-ARCH-01-20250925-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT`  
**Related PO Decision Record:** `CT-PO-P17-POST-ARCH-DECISIONS-20260925`  
**Production Authorization:** NOT AUTHORIZED

---

# 1. Purpose

This document defines the Product Owner's UI/UX standard for CarbonTally's **Unified Carbon Accounting Management System (CAMS)**.

It is an implementation and acceptance reference for Cline and future developers.

The system covers:

- Scope 1
- Scope 2
- Scope 3
- CarbonTally Admin/Staff
- Direct CarbonTally customer organizations
- Consultant organizations
- Consultant-managed client organizations
- Customer/client users
- Evidence
- Activity data
- Suppliers
- Calculations
- Review
- Exceptions
- Reportability
- Reporting
- Audit/history
- Organization capabilities
- Delegated access

This is a **UI/UX information-architecture and acceptance standard**, not a pixel-perfect visual design specification.

---

# 2. Core Product Principle

CarbonTally has one:

> **Unified Carbon Accounting Management System**

It does not have separate accounting applications for:

- CarbonTally Staff
- direct customers
- consultants
- consultant clients

The same accounting domain and calculation architecture is used by all authorized actors.

What changes is:

- actor
- organization context
- role
- capability
- delegated relationship
- workflow authority

---

# 3. Primary User Contexts

The UI/UX must support at least these contexts.

## 3.1 CarbonTally Admin/Staff

CarbonTally staff operate the platform and may manage customer accounting according to their role.

## 3.2 Direct Customer Organization

A normal CarbonTally customer manages its own organization's accounting.

## 3.3 Consultant Organization

A consultant:

1. manages its own organization's accounting;
2. manages an authorized portfolio of client organizations.

## 3.4 Consultant Client Organization

A consultant's client remains an independent organization and can have its own users, accounting data, evidence, review and reporting.

## 3.5 Users Acting Through Delegated Access

A consultant user may operate on behalf of an authorized client.

The UI must make the acting organization/client context unmistakable.

---

# 4. Global UX Architecture

Conceptual platform structure:

```text
CARBONTALLY PLATFORM
│
├── Platform Administration
│
├── Organizations
│
├── Carbon Accounting
│   │
│   ├── Overview
│   ├── Scope 1
│   ├── Scope 2
│   ├── Scope 3
│   ├── Data Collection
│   ├── Evidence
│   ├── Suppliers
│   ├── Review Queue
│   ├── Exceptions
│   └── Reporting
│
└── Settings
```

The actual navigation must be reconciled with the existing CarbonTally application.

Cline MUST NOT create duplicate navigation if equivalent navigation already exists.

---

# 5. Global UX Rule — Organization Context

Every accounting screen must make the current organization context clear.

For CarbonTally Staff:

```text
Organization:
[ ABC Manufacturing ▼ ]
```

For a direct customer:

```text
Organization:
ABC Manufacturing
```

For a consultant:

```text
My Organization:
Green Advisory

Acting For:
[ ABC Manufacturing ▼ ]
```

For a client user:

```text
Organization:
ABC Manufacturing
```

The user must never have to infer which organization owns the displayed accounting data.

---

# 6. Global UX Rule — Acting For Context

When a consultant is operating on behalf of a client:

```text
┌──────────────────────────────────────────────────────────────┐
│ GREEN ADVISORY                               Jane ▼          │
├──────────────────────────────────────────────────────────────┤
│ ACTING FOR: ABC MANUFACTURING                         ▼      │
└──────────────────────────────────────────────────────────────┘
```

This context should remain visible throughout the client accounting workflow.

The UI must prevent accidental operation against the wrong client.

Backend authorization remains mandatory. The UI indicator is not an authorization mechanism.

---

# 7. CarbonTally Staff — Global Layout

Reference layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ CARBONTALLY                                  🔔  Staff ▼     │
├────────────────┬─────────────────────────────────────────────┤
│ PLATFORM       │                                             │
│                │  Carbon Accounting Management               │
│ Dashboard      │                                             │
│ Organizations  │  Organization: [ ABC Manufacturing ▼ ]    │
│                │                                             │
│ ACCOUNTING     │  ┌────────────┐ ┌────────────┐ ┌─────────┐│
│ Overview       │  │ Scope 1    │ │ Scope 2    │ │ Scope 3 ││
│ Scope 1        │  │            │ │            │ │         ││
│ Scope 2        │  │  Status    │ │  Status    │ │ Status  ││
│ Scope 3        │  │  ...       │ │  ...       │ │  ...    ││
│ Data           │  └────────────┘ └────────────┘ └─────────┘│
│ Review Queue   │                                             │
│ Exceptions     │  Review Required: 23                        │
│ Evidence       │  Exceptions: 7                              │
│ Suppliers      │  Pending Data: 41                           │
│ Reporting      │                                             │
│                │  Recent Accounting Activity                │
│ GOVERNANCE     │  ─────────────────────────────────────────  │
│ Factors        │  ...                                        │
│ Methodologies  │                                             │
│ Controls       │                                             │
│ Capabilities   │                                             │
│ Audit          │                                             │
└────────────────┴─────────────────────────────────────────────┘
```

---

# 8. Staff Organization Selector

Staff must be able to select an authorized organization.

```text
┌─────────────────────────────────────────┐
│ Organization                            │
│                                         │
│ [ ABC Manufacturing                 ▼ ] │
│                                         │
│ Search organizations...                 │
│                                         │
│ Recent                                  │
│ • ABC Manufacturing                     │
│ • XYZ Retail                             │
│ • Global Logistics                       │
└─────────────────────────────────────────┘
```

Only organizations the staff member is authorized to access should appear.

---

# 9. Direct Customer — Global Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ ABC MANUFACTURING                            User ▼          │
├────────────────┬─────────────────────────────────────────────┤
│ MY ORGANIZATION │                                             │
│                │ Carbon Accounting                           │
│ Dashboard      │                                             │
│                │ Reporting Period: [ FY2026 ▼ ]              │
│ ACCOUNTING     │                                             │
│ Overview       │ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│ Scope 1        │ │ Scope 1  │ │ Scope 2  │ │ Scope 3  │     │
│ Scope 2        │ │          │ │          │ │          │     │
│ Scope 3        │ │  ...     │ │  ...     │ │  ...     │     │
│                │ └──────────┘ └──────────┘ └──────────┘     │
│ Data Collection│                                             │
│ Evidence       │ Data Quality                                │
│ Suppliers      │ ████████████████░░░░ 82%                   │
│ Review         │                                             │
│ Calculations   │ Action Required                             │
│ Reports        │ • 12 records awaiting review                │
│                │ • 4 missing evidence                        │
│                │ • 2 clarification requests                  │
└────────────────┴─────────────────────────────────────────────┘
```

---

# 10. Consultant — Global Layout

A consultant needs its own accounting plus client portfolio management.

```text
┌──────────────────────────────────────────────────────────────┐
│ GREEN ADVISORY                               User ▼          │
├────────────────┬─────────────────────────────────────────────┤
│ MY ORGANIZATION │ Consultant Workspace                       │
│                │                                             │
│ Dashboard      │ MY CARBON ACCOUNTING                        │
│ My Accounting  │ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│                │ │ Scope 1  │ │ Scope 2  │ │ Scope 3  │     │
│ CLIENTS        │ └──────────┘ └──────────┘ └──────────┘     │
│ Portfolio      │                                             │
│ Client Tasks   │ CLIENT PORTFOLIO                            │
│ Data Requests  │                                             │
│ Review Queue   │ ┌─────────────────────────────────────────┐ │
│                │ │ ABC Manufacturing                       │ │
│                │ │ Scope 1 ● Scope 2 ● Scope 3 ●          │ │
│                │ │ Review: 12    Issues: 3                │ │
│                │ ├─────────────────────────────────────────┤ │
│                │ │ XYZ Retail                              │ │
│                │ │ Scope 1 ● Scope 2 ● Scope 3 ●          │ │
│                │ │ Review: 4     Issues: 1                │ │
│                │ └─────────────────────────────────────────┘ │
└────────────────┴─────────────────────────────────────────────┘
```

---

# 11. Consultant Client Portfolio

```text
┌──────────────────────────────────────────────────────────────┐
│ CLIENT PORTFOLIO                                             │
├──────────────────────┬─────────┬─────────┬─────────┬─────────┤
│ Organization         │ S1      │ S2      │ S3      │ Actions │
├──────────────────────┼─────────┼─────────┼─────────┼─────────┤
│ ABC Manufacturing    │ ●       │ ●       │ ●       │ Open    │
│ XYZ Retail            │ ●       │ ●       │ —       │ Open    │
│ Global Logistics      │ ●       │ ●       │ ●       │ Open    │
└──────────────────────┴─────────┴─────────┴─────────┴─────────┘
```

The UI should show the capability state rather than misleadingly displaying unavailable scopes as empty data.

---

# 12. Consultant — Client Context

```text
┌──────────────────────────────────────────────────────────────┐
│ GREEN ADVISORY                             Jane ▼            │
├──────────────────────────────────────────────────────────────┤
│ ACTING FOR: ABC MANUFACTURING                         ▼      │
├────────────────┬─────────────────────────────────────────────┤
│ CLIENT ACCOUNT │                                             │
│                │ Carbon Accounting                           │
│ Overview       │                                             │
│ Scope 1        │ Scope 1    Scope 2    Scope 3              │
│ Scope 2        │ ┌───────┐ ┌───────┐ ┌───────┐             │
│ Scope 3        │ │  ...  │ │  ...  │ │  ...  │             │
│ Evidence       │ └───────┘ └───────┘ └───────┘             │
│ Suppliers      │                                             │
│ Review         │ Review Required: 12                         │
│ Reporting      │                                             │
└────────────────┴─────────────────────────────────────────────┘
```

---

# 13. Client Switcher

```text
┌──────────────────────────────────────┐
│ ACTING FOR                           │
│                                      │
│ ● ABC Manufacturing                  │
│   Full accounting + review           │
│                                      │
│ ○ XYZ Retail                         │
│   Scope 1/2 + reporting              │
│                                      │
│ ○ Global Logistics                   │
│   Read-only                           │
│                                      │
│ [ Manage Access ]                    │
└──────────────────────────────────────┘
```

Client access must be explicit and client-specific.

---

# 14. Client Organization — Own Workspace

A consultant client remains a normal organization.

```text
┌──────────────────────────────────────────────────────────────┐
│ ABC MANUFACTURING                            User ▼          │
├──────────────────────────────────────────────────────────────┤
│ Consultant Access: GREEN ADVISORY                            │
│                                                              │
│ Carbon Accounting                                            │
│                                                              │
│ Scope 1 │ Scope 2 │ Scope 3 │ Evidence │ Review │ Reports   │
│                                                              │
│ Delegated Access                                             │
│ Green Advisory                                               │
│   ✓ Data entry                                               │
│   ✓ Evidence upload                                          │
│   ✓ Calculation                                              │
│   ✓ Review                                                   │
│   ✗ Final reporting approval                                 │
└──────────────────────────────────────────────────────────────┘
```

The client should be able to understand who has delegated access and what the delegation allows.

---

# 15. Organization Capability Settings — Staff

```text
┌──────────────────────────────────────────────────────────────┐
│ ORGANIZATION ACCOUNTING CAPABILITIES                          │
│ ABC Manufacturing                                            │
├──────────────────────────────────────────────────────────────┤
│ Customer Carbon Accounting                    [ ON ]          │
│                                                              │
│ Scope 1 Customer Entry                        [ ON ]          │
│ Scope 2 Customer Entry                        [ ON ]          │
│ Scope 3 Customer Entry                        [ ON ]          │
│                                                              │
│ Customer Evidence Upload                      [ ON ]          │
│ Customer Supplier Data                        [ ON ]          │
│ Customer Editing                              [ ON ]          │
│ Customer Review                               [ ON ]          │
│                                                              │
│ Staff Review Required                         [ ON ]          │
│ Staff Approval Required                       [ ON ]          │
│                                                              │
│ Consultant Features                            [ OFF ]        │
│                                                              │
│                         [ Cancel ] [ Save ]                   │
└──────────────────────────────────────────────────────────────┘
```

The actual capability list must be reconciled with the existing authorization/capability model.

---

# 16. Consultant Delegated Access Settings

```text
┌──────────────────────────────────────────────────────────────┐
│ DELEGATED ACCESS                                             │
│ Client: ABC Manufacturing                                    │
│ Consultant: Green Advisory                                   │
├──────────────────────────────────────────────────────────────┤
│ Consultant Access                                             │
│                                                              │
│ Scope 1 Data Entry                            [ ON ]          │
│ Scope 2 Data Entry                            [ ON ]          │
│ Scope 3 Data Entry                            [ ON ]          │
│ Evidence Upload                               [ ON ]          │
│ Supplier Data                                 [ ON ]          │
│ Calculations                                  [ ON ]          │
│ Review                                        [ ON ]          │
│ Reporting Preparation                         [ ON ]          │
│ Final Reporting Approval                      [ OFF ]         │
│                                                              │
│ Relationship Status: ACTIVE                                  │
│                                                              │
│ [ Cancel Access ]                           [ Save ]          │
└──────────────────────────────────────────────────────────────┘
```

Only authorized users should be able to change this.

---

# 17. Scope 1 — Information Architecture

```text
SCOPE 1
│
├── Overview
│
├── Activities
│   ├── Activity List
│   ├── Add Activity
│   ├── Import
│   └── History
│
├── Evidence
│
├── Calculations
│
├── Review
│
├── Exceptions
│
└── Reportability
```

---

# 18. Scope 1 — Overview

```text
┌──────────────────────────────────────────────────────────────┐
│ SCOPE 1                                                     │
│ FY2026                                                       │
├──────────────────────────────────────────────────────────────┤
│ Total Emissions                                              │
│                                                              │
│  4,175.903780 kgCO2e                                        │
│                                                              │
│ Data Quality        Review Required       Reportability     │
│ █████████ 91%       8 records             ● Controlled      │
│                                                              │
│ Activity Sources                                             │
│ • Stationary combustion                                     │
│ • Mobile combustion                                         │
│ • Fugitive emissions                                        │
│                                                              │
│ [ Add Activity ] [ Import ] [ Review Queue ]                │
└──────────────────────────────────────────────────────────────┘
```

Exact values must always come from actual data; this diagram is illustrative only.

---

# 19. Scope 1 — Activity List

```text
┌──────────────────────────────────────────────────────────────┐
│ SCOPE 1 ACTIVITIES                          [ + Add Activity ]│
├────────────┬──────────────┬─────────┬──────────┬─────────────┤
│ Period     │ Activity     │ Qty     │ Status   │ Action      │
├────────────┼──────────────┼─────────┼──────────┼─────────────┤
│ Jan 2026   │ Natural Gas  │ 12,181  │ ● Valid  │ View/Edit   │
│ Feb 2026   │ Diesel       │ 8,420   │ ⚠ Review │ Review      │
└────────────┴──────────────┴─────────┴──────────┴─────────────┘
```

---

# 20. Scope 1 — Data Entry

Every activity form should clearly expose:

- activity
- facility/site
- reporting period
- quantity
- unit
- source
- evidence
- factor/method
- validation status
- review state

Reference:

```text
┌──────────────────────────────────────────────────────────────┐
│ ADD SCOPE 1 ACTIVITY                                         │
├──────────────────────────────────────────────────────────────┤
│ Activity       [ Natural Gas                         ▼ ]     │
│ Facility       [ Dhaka Factory                       ▼ ]     │
│ Period         [ Jan 2026 ]                                  │
│ Quantity       [ 12,181.4 ]                                  │
│ Unit           [ kWh ▼ ]                                     │
│ Evidence       [ invoice.pdf ]                               │
│                                                              │
│ Factor         [ Auto-matched ]                              │
│                                                              │
│ Data Quality   ● Complete                                    │
│ Review         ● Required                                    │
│                                                              │
│ [ Save Draft ]                       [ Submit for Review ]   │
└──────────────────────────────────────────────────────────────┘
```

---

# 21. Scope 2 — Information Architecture

```text
SCOPE 2
│
├── Overview
│
├── Energy Activities
│
├── Location-Based
│   ├── Activity Data
│   ├── Grid Region
│   ├── Factor
│   └── Calculation
│
├── Market-Based
│   ├── Activity Data
│   ├── Supplier Factors
│   ├── Contractual Instruments
│   └── Calculation
│
├── Contractual Instruments
│   ├── Instruments
│   ├── Evidence
│   ├── Validation
│   └── Status
│
├── Comparison
│   ├── Location-Based
│   └── Market-Based
│
├── Review
│
├── Exceptions
│
└── Reportability
```

---

# 22. Scope 2 — Overview

```text
┌──────────────────────────────────────────────────────────────┐
│ SCOPE 2                                                     │
├──────────────────────────────────────────────────────────────┤
│ Location-Based Emissions          Market-Based Emissions     │
│ ┌─────────────────────────┐       ┌────────────────────────┐ │
│ │       4,821.42          │       │       3,992.18         │ │
│ │       kgCO2e            │       │       kgCO2e            │ │
│ └─────────────────────────┘       └────────────────────────┘ │
│                                                              │
│ Contractual Instruments                                     │
│ • 2 active                                                   │
│ • 1 awaiting validation                                      │
│                                                              │
│ Review Required: 5                                          │
│                                                              │
│ [ Energy Activities ] [ Instruments ] [ Review ]            │
└──────────────────────────────────────────────────────────────┘
```

Illustrative values only.

---

# 23. Scope 2 — Contractual Instrument

```text
┌──────────────────────────────────────────────────────────────┐
│ CONTRACTUAL INSTRUMENT                                      │
├──────────────────────────────────────────────────────────────┤
│ Instrument Type       [ EAC / PPA / Other ▼ ]               │
│ Issuer / Supplier     [ Supplier Name ▼ ]                   │
│ Coverage Period       [ Jan 2026 — Dec 2026 ]               │
│ Quantity              [ 10,000 ]                             │
│ Unit                  [ MWh ▼ ]                              │
│ Applicable Facility   [ Dhaka Factory ▼ ]                   │
│                                                              │
│ Evidence              [ certificate.pdf ]                    │
│                                                              │
│ Validation             ● Pending                             │
│                                                              │
│ [ Save Draft ] [ Submit for Validation ]                    │
└──────────────────────────────────────────────────────────────┘
```

The actual instrument fields must follow the P17 accounting contract.

---

# 24. Scope 2 — Location vs Market Comparison

```text
┌──────────────────────────────────────────────────────────────┐
│ SCOPE 2 METHOD COMPARISON                                    │
├──────────────────────┬──────────────────────┬───────────────┤
│                      │ Location-Based       │ Market-Based  │
├──────────────────────┼──────────────────────┼───────────────┤
│ Activity              │ 12,181.4 kWh        │ 12,181.4 kWh  │
│ Factor                │ Grid factor         │ Contractual   │
│ Evidence              │ Invoice             │ Certificate   │
│ Result                │ [calculated]        │ [calculated]  │
│ Status                │ Valid               │ Review        │
└──────────────────────┴──────────────────────┴───────────────┘
```

The UI must make the methodological distinction clear.

---

# 25. Scope 3 — Information Architecture

```text
SCOPE 3
│
├── Overview
│
├── Category 1 — Purchased Goods & Services
├── Category 2 — Capital Goods
├── Category 3 — Fuel & Energy Related Activities
├── Category 4 — Upstream Transportation & Distribution
├── Category 5 — Waste Generated in Operations
├── Category 6 — Business Travel
├── Category 7 — Employee Commuting
├── Category 8 — Upstream Leased Assets
├── Category 9 — Downstream Transportation & Distribution
├── Category 10 — Processing of Sold Products
├── Category 11 — Use of Sold Products
├── Category 12 — End-of-Life Treatment
├── Category 13 — Downstream Leased Assets
├── Category 14 — Franchises
├── Category 15 — Investments
│
├── Supplier Data
├── Evidence
├── Estimation / Methodology
├── Review
├── Exceptions
└── Reportability
```

Category labels must ultimately match the approved P17 taxonomy.

---

# 26. Scope 3 — Category Overview

```text
┌──────────────────────────────────────────────────────────────┐
│ SCOPE 3                                                     │
├───────────────┬────────────┬────────────┬───────────────────┤
│ Category      │ Data       │ Quality    │ Status            │
├───────────────┼────────────┼────────────┼───────────────────┤
│ Category 1    │ 1,248 rows │ 86%        │ ● Review          │
│ Category 2    │ 82 rows    │ 94%        │ ● Valid           │
│ Category 3    │ 19 rows    │ 71%        │ ⚠ Attention       │
│ Category 4    │ 42 rows    │ 90%        │ ● Valid           │
│ ...           │ ...        │ ...        │ ...               │
│ Category 15   │ 0 rows     │ —          │ ○ No data         │
└───────────────┴────────────┴────────────┴───────────────────┘
```

Do not represent "no data" as "zero emissions".

---

# 27. Scope 3 — Category Detail

```text
┌──────────────────────────────────────────────────────────────┐
│ CATEGORY 1 — PURCHASED GOODS & SERVICES                      │
├──────────────────────────────────────────────────────────────┤
│ Overview                                                     │
│                                                              │
│ Data Records: 1,248                                         │
│ Suppliers: 84                                               │
│ Evidence Coverage: 78%                                      │
│ Review Required: 31                                         │
│                                                              │
│ [ Add Data ] [ Import ] [ Suppliers ] [ Review ]            │
│                                                              │
│ Recent Records                                               │
│ ┌──────────────┬──────────┬───────────┬────────────────────┐│
│ │ Supplier     │ Quantity │ Method    │ Status             ││
│ ├──────────────┼──────────┼───────────┼────────────────────┤│
│ │ Supplier A   │ ...      │ Activity  │ ● Valid            ││
│ │ Supplier B   │ ...      │ Spend     │ ⚠ Review           ││
│ └──────────────┴──────────┴───────────┴────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

# 28. Data Collection Workspace

```text
┌──────────────────────────────────────────────────────────────┐
│ DATA COLLECTION                                              │
├──────────────────────────────────────────────────────────────┤
│ Collection Period: FY2026                                   │
│                                                              │
│ ┌──────────────────┐ ┌──────────────────┐ ┌────────────────┐│
│ │ Scope 1          │ │ Scope 2          │ │ Scope 3        ││
│ │ 12 tasks         │ │ 8 tasks          │ │ 43 tasks       ││
│ │ 75% complete     │ │ 91% complete     │ │ 62% complete   ││
│ └──────────────────┘ └──────────────────┘ └────────────────┘│
│                                                              │
│ Pending Requests                                             │
│ • Upload electricity invoices                                │
│ • Confirm supplier quantities                                 │
│ • Provide travel records                                      │
│                                                              │
│ [ Create Request ]                                           │
└──────────────────────────────────────────────────────────────┘
```

---

# 29. Evidence Workspace

```text
┌──────────────────────────────────────────────────────────────┐
│ EVIDENCE                                                     │
├──────────────────────────────────────────────────────────────┤
│ [ Upload ] [ Search ] [ Filter ]                             │
│                                                              │
│ ┌─────────────────────┬────────────┬────────────┬───────────┐│
│ │ Evidence             │ Scope      │ Linked To  │ Status    ││
│ ├─────────────────────┼────────────┼────────────┼───────────┤│
│ │ invoice.pdf          │ Scope 2    │ Activity   │ ✓ Valid   ││
│ │ supplier_data.xlsx   │ Scope 3    │ Category 1 │ ⚠ Review  ││
│ │ certificate.pdf      │ Scope 2    │ Instrument │ ✓ Valid   ││
│ └─────────────────────┴────────────┴────────────┴───────────┘│
└──────────────────────────────────────────────────────────────┘
```

Evidence should show ownership and uploader/acting context where relevant.

---

# 30. Evidence Detail

```text
┌──────────────────────────────────────────────────────────────┐
│ EVIDENCE: electricity_invoice.pdf                            │
├──────────────────────────────────────────────────────────────┤
│ Owner Organization: ABC Manufacturing                        │
│ Uploaded By: Green Advisory / Jane                           │
│ Acting For: ABC Manufacturing                                │
│                                                              │
│ Source Type: Invoice                                         │
│ Reporting Period: Jan 2026                                   │
│                                                              │
│ Linked Activity: Purchased Electricity                       │
│                                                              │
│ Extraction: Complete                                         │
│ Validation: Valid                                            │
│                                                              │
│ [ View Document ] [ View Extraction ] [ View Audit ]         │
└──────────────────────────────────────────────────────────────┘
```

---

# 31. Supplier Workspace

```text
┌──────────────────────────────────────────────────────────────┐
│ SUPPLIERS                                                    │
├──────────────────────────────────────────────────────────────┤
│ [ Add Supplier ] [ Import ]                                  │
│                                                              │
│ ┌─────────────────────┬──────────────┬──────────┬───────────┐│
│ │ Supplier             │ Categories   │ Data     │ Status    ││
│ ├─────────────────────┼──────────────┼──────────┼───────────┤│
│ │ Supplier A           │ 1,4          │ Primary  │ ✓ Valid   ││
│ │ Supplier B           │ 1            │ Partial  │ ⚠ Review  ││
│ │ Supplier C           │ 3,4          │ Estimate │ ○ Pending ││
│ └─────────────────────┴──────────────┴──────────┴───────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

# 32. Supplier Detail

```text
┌──────────────────────────────────────────────────────────────┐
│ SUPPLIER: Supplier A                                         │
├──────────────────────────────────────────────────────────────┤
│ Organization: ABC Manufacturing                              │
│                                                              │
│ Categories                                                  │
│ ✓ Category 1                                                │
│ ✓ Category 4                                                │
│                                                              │
│ Data                                                         │
│ • Supplier-specific emissions                                │
│ • Activity data                                              │
│ • Evidence                                                   │
│                                                              │
│ Attribution                                                  │
│ ✓ Linked to ABC Manufacturing                                │
│                                                              │
│ [ Add Data ] [ Evidence ] [ History ]                        │
└──────────────────────────────────────────────────────────────┘
```

---

# 33. Review Queue — Shared Pattern

```text
┌──────────────────────────────────────────────────────────────┐
│ REVIEW QUEUE                                                 │
├────────┬──────────────┬──────────┬────────────┬─────────────┤
│ Status │ Organization │ Scope    │ Issue      │ Action      │
├────────┼──────────────┼──────────┼────────────┼─────────────┤
│ ⚠ Open │ ABC          │ Scope 3 │ Factor     │ Review      │
│ ⚠ Open │ ABC          │ Scope 2 │ Evidence   │ Review      │
│ ⚠ Open │ XYZ          │ Scope 1 │ Unit       │ Resolve     │
│ ✓ Done │ DEF          │ Scope 3 │ Supplier   │ View        │
└────────┴──────────────┴──────────┴────────────┴─────────────┘
```

The actual visible scope of the queue depends on actor permissions.

---

# 34. Review Detail

```text
┌──────────────────────────────────────────────────────────────┐
│ REVIEW ITEM                                                  │
├──────────────────────────────────────────────────────────────┤
│ Organization: ABC Manufacturing                              │
│ Acting User: Green Advisory / Jane                           │
│ Scope: Scope 3                                               │
│ Category: Category 1                                         │
│                                                              │
│ Issue                                                        │
│ Factor selection requires review.                            │
│                                                              │
│ Source Data                                                  │
│ Quantity: ...                                                │
│ Unit: ...                                                    │
│ Evidence: supplier_invoice.pdf                               │
│                                                              │
│ Proposed Factor: ...                                         │
│                                                              │
│ [ Request Clarification ] [ Correct ] [ Approve ] [ Reject ] │
└──────────────────────────────────────────────────────────────┘
```

---

# 35. Exception / Clarification Workspace

```text
┌──────────────────────────────────────────────────────────────┐
│ EXCEPTIONS                                                   │
├───────────┬──────────────┬──────────────┬───────────────────┤
│ Priority  │ Organization │ Issue        │ Status            │
├───────────┼──────────────┼──────────────┼───────────────────┤
│ High      │ ABC          │ Supplier     │ Awaiting customer │
│ Medium    │ ABC          │ Unit         │ Open              │
│ Low       │ XYZ          │ Evidence     │ Open              │
└───────────┴──────────────┴──────────────┴───────────────────┘
```

An exception must clearly identify:

- what is wrong/uncertain
- affected accounting object
- owner
- required action
- status
- downstream impact

---

# 36. Calculation Detail

```text
┌──────────────────────────────────────────────────────────────┐
│ CALCULATION                                                  │
├──────────────────────────────────────────────────────────────┤
│ Organization: ABC Manufacturing                              │
│ Scope: Scope 2                                               │
│ Method: Location-Based                                       │
│                                                              │
│ Activity Data                                                │
│ Quantity: 12,181.4 kWh                                      │
│                                                              │
│ Factor                                                       │
│ Factor: [ governed factor ]                                  │
│ Unit: kgCO2e/kWh                                             │
│ Year: 2026                                                   │
│ Source: [ factor source ]                                    │
│                                                              │
│ Calculation                                                  │
│ 12,181.4 × 0.2027                                            │
│ = 2,469.169780 kgCO2e                                        │
│                                                              │
│ Status: Calculated                                           │
│ Reportability: Controlled                                    │
│                                                              │
│ [ View Evidence ] [ View Audit ]                             │
└──────────────────────────────────────────────────────────────┘
```

Illustrative example only. Actual calculations must come from real data.

---

# 37. Calculation Provenance

Every user-facing calculation detail should expose enough provenance for the actor's permissions.

Conceptually:

```text
CALCULATION PROVENANCE
│
├── Source Activity
├── Source Evidence
├── Normalized Value
├── Unit
├── Factor
├── Factor Source
├── Factor Year
├── Methodology
├── Calculation Formula
├── Result
├── Actor
├── Organization
├── Review Status
└── Reportability Status
```

---

# 38. Reportability UI

```text
┌──────────────────────────────────────────────────────────────┐
│ REPORTABILITY                                                │
├──────────────────────────────────────────────────────────────┤
│ Result: 2,469.169780 kgCO2e                                  │
│                                                              │
│ Accounting State: Calculated                                 │
│ Reportability: ● REPORTABLE                                  │
│                                                              │
│ Evidence: ✓                                                 │
│ Validation: ✓                                               │
│ Review: ✓                                                    │
│ Approval: ✓                                                 │
│                                                              │
│ History                                                      │
│ • Calculated                                                 │
│ • Reviewed                                                   │
│ • Approved                                                   │
│                                                              │
│ [ View History ]                                             │
└──────────────────────────────────────────────────────────────┘
```

If not reportable:

```text
Reportability: ● NOT FOR REPORTING

Reason:
Awaiting required evidence.

Action:
[ Resolve Issue ]
```

Never display "reportable" merely because a calculation exists.

---

# 39. Reporting Workspace

```text
┌──────────────────────────────────────────────────────────────┐
│ REPORTING                                                    │
├──────────────────────────────────────────────────────────────┤
│ Reporting Period: [ FY2026 ▼ ]                               │
│ Organization: [ ABC Manufacturing ▼ ]                       │
│                                                              │
│ Scope 1     4,175.90                                         │
│ Scope 2     4,821.42                                         │
│ Scope 3    18,420.11                                         │
│                                                              │
│ Data Quality: 87%                                            │
│ Reportability: 91%                                           │
│ Review Required: 7                                          │
│                                                              │
│ [ Create Report ] [ Review Data ] [ Export ]                 │
└──────────────────────────────────────────────────────────────┘
```

Actual reporting/disclosure capabilities must follow the P17 reporting architecture and later reporting contracts.

---

# 40. Audit / History UI

```text
┌──────────────────────────────────────────────────────────────┐
│ AUDIT HISTORY                                                │
├──────────────────────────────────────────────────────────────┤
│ Activity: Purchased Electricity                              │
│ Organization: ABC Manufacturing                              │
│                                                              │
│ 2026-09-25  Jane / Green Advisory                            │
│ Changed quantity                                             │
│ 10,000 → 12,181.4 kWh                                        │
│                                                              │
│ 2026-09-25  System                                            │
│ Calculation created                                          │
│                                                              │
│ 2026-09-25  CarbonTally Reviewer                             │
│ Review approved                                              │
│                                                              │
│ [ View Full Event ]                                          │
└──────────────────────────────────────────────────────────────┘
```

For delegated access, the UI must distinguish operator from organization owner.

---

# 41. Data Quality Dashboard

```text
┌──────────────────────────────────────────────────────────────┐
│ DATA QUALITY                                                 │
├──────────────────────────────────────────────────────────────┤
│ Overall                                      87%             │
│                                                              │
│ Completeness     ████████████████░░░  84%                   │
│ Evidence         █████████████████░░  91%                   │
│ Validation       ███████████████░░░░  78%                   │
│ Supplier Data    ██████████████░░░░░  72%                   │
│ Review           █████████████████░░  90%                   │
│                                                              │
│ Issues                                                       │
│ • 12 missing evidence                                        │
│ • 7 unresolved mappings                                      │
│ • 4 pending reviews                                          │
└──────────────────────────────────────────────────────────────┘
```

Do not convert missing data into zero emissions.

---

# 42. Data Submission State UX

Use explicit states.

```text
DRAFT
SUBMITTED
VALIDATING
VALIDATED
CALCULATING
CALCULATED
REVIEW
APPROVED
REPORTABLE
REJECTED
INVALIDATED
SUPERSEDED
```

The exact state machine must follow the accounting contract and existing P16 lifecycle.

The UI must not invent a conflicting lifecycle.

---

# 43. Disabled Capability UX

If an organization does not have Scope 3 customer entry enabled:

```text
┌───────────────────────────────────────────────┐
│ Scope 3                                       │
│                                               │
│ Customer-managed Scope 3 data entry is        │
│ currently disabled for this organization.    │
│                                               │
│ You may still have access to other Scope 3    │
│ information according to your permissions.   │
│                                               │
│ Contact your CarbonTally administrator.       │
└───────────────────────────────────────────────┘
```

Do not show a misleading empty data table.

---

# 44. Permission-Denied UX

```text
┌───────────────────────────────────────────────┐
│ Access Restricted                             │
│                                               │
│ You do not have permission to perform this    │
│ action for ABC Manufacturing.                 │
│                                               │
│ Required capability: Scope 3 Review           │
│                                               │
│ [ Back ]                                     │
└───────────────────────────────────────────────┘
```

The backend must independently enforce the same restriction.

---

# 45. Loading State Standard

All major accounting pages should have a deliberate loading state.

```text
┌───────────────────────────────────────────────┐
│ Scope 3                                       │
│                                               │
│ Loading accounting data...                    │
│                                               │
│ █████████████████████                        │
│ ███████████████                              │
│ ███████████████████                          │
└───────────────────────────────────────────────┘
```

Avoid blank screens.

---

# 46. Empty State Standard

An empty state must distinguish:

- no data
- not configured
- not enabled
- not yet submitted
- no access

Example:

```text
No Scope 3 Category 15 data has been submitted
for FY2026.

This does NOT mean emissions are zero.

[ Add Data ] [ Request Data ]
```

---

# 47. Error State Standard

```text
Unable to calculate this record.

Reason:
The selected factor is not valid for the activity scope/year.

Required action:
Review factor selection.

[ Review Factor ] [ View Details ]
```

Errors should explain the next useful action where possible.

---

# 48. Customer Data Entry — Standard Questions

Every applicable activity/data-entry workflow should expose enough context to answer:

```text
WHAT?
WHERE?
WHEN?
HOW MUCH?
UNIT?
SOURCE?
EVIDENCE?
METHOD?
FACTOR?
STATUS?
WHO ENTERED IT?
WHO IS ACTING FOR?
WHAT HAPPENS NEXT?
```

The exact fields differ by accounting domain.

---

# 49. UI Standard for Customer vs Consultant Entry

The accounting form itself should remain substantially consistent.

The context changes.

Direct customer:

```text
ABC Manufacturing
    ↓
Add Activity
```

Consultant:

```text
Green Advisory
    ↓
Acting For: ABC Manufacturing
    ↓
Add Activity
```

Do not create a separate consultant calculation/form engine.

---

# 50. UI Standard for Staff vs Customer

Staff may see additional controls.

Example:

```text
CUSTOMER VIEW

[ Save Draft ] [ Submit ]

STAFF VIEW

[ Edit ]
[ Resolve ]
[ Override ]
[ Approve ]
[ Invalidate ]
```

The additional controls must be capability-driven.

Do not create separate data models merely because the UI has more actions.

---

# 51. Navigation Rules

Navigation must be:

- role-aware
- organization-aware
- capability-aware
- relationship-aware

A menu item should not appear as if a feature exists when the user has no access to it.

However, security cannot depend on hiding menu items.

---

# 52. Mobile / Responsive Standard

Cline should ensure that accounting workflows remain usable on smaller screens.

Priority:

1. review
2. data entry
3. evidence
4. exceptions
5. status
6. reporting

Large accounting tables may use horizontal scrolling or responsive cards where appropriate.

Do not destroy important accounting context simply to force a desktop table into a narrow screen.

---

# 53. Accessibility Baseline

The UI should provide:

- keyboard-accessible controls
- clear labels
- distinguishable status states
- non-color-only status communication
- readable validation messages
- logical focus order
- accessible dialogs/forms
- meaningful table headers

Existing CarbonTally accessibility patterns should be reused.

---

# 54. Cline Discovery Requirement

Before changing UI or backend, Cline MUST inspect:

```text
Repository
   ↓
Existing routes
   ↓
Existing pages/components
   ↓
Existing navigation
   ↓
Existing API
   ↓
Existing services
   ↓
Existing schema/migrations
   ↓
Existing organization model
   ↓
Existing consultant/client relationships
   ↓
Existing authorization/RLS
   ↓
Existing accounting features
   ↓
Existing tests
```

Then produce an inventory.

---

# 55. Mandatory Existing-vs-Missing Matrix

Cline must create a matrix similar to:

| UX/Feature | Existing UI | Existing Backend | Existing DB | Existing Auth | Partial | Missing | Reuse/Extend | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Staff Accounting Overview | | | | | | | | |
| Customer Accounting Overview | | | | | | | | |
| Consultant Portfolio | | | | | | | | |
| Client Context Switching | | | | | | | | |
| Scope 1 Activities | | | | | | | | |
| Scope 2 Location-Based | | | | | | | | |
| Scope 2 Market-Based | | | | | | | | |
| Contractual Instruments | | | | | | | | |
| Scope 3 Categories 1–15 | | | | | | | | |
| Evidence | | | | | | | | |
| Supplier Management | | | | | | | | |
| Review Queue | | | | | | | | |
| Exceptions | | | | | | | | |
| Reportability | | | | | | | | |
| Reporting | | | | | | | | |
| Organization Capabilities | | | | | | | | |
| Consultant Delegation | | | | | | | | |
| Audit/History | | | | | | | | |

Cline must fill this based on repository evidence.

---

# 56. Mandatory UX Acceptance Matrix

For every major feature:

| Feature | Staff | Direct Org | Consultant Own | Consultant Client | Client User | Disabled State | Audit | Backend Auth | UI Complete |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Scope 1 | | | | | | | | | |
| Scope 2 | | | | | | | | | |
| Scope 3 | | | | | | | | | |
| Evidence | | | | | | | | | |
| Suppliers | | | | | | | | | |
| Review | | | | | | | | | |
| Reporting | | | | | | | | | |
| Client Delegation | | | | | | | | | |

Blank cells are for implementation verification, not permission assumptions.

---

# 57. Cline Must Evaluate Existing UI Against the ASCII Standard

The ASCII screens are not permission to rebuild the application blindly.

Cline must:

1. inspect current UI;
2. identify reusable components;
3. identify current navigation;
4. identify existing design system;
5. map existing screens to this standard;
6. identify gaps;
7. identify contradictions;
8. implement only the required gaps/changes;
9. verify the resulting UI against this standard.

---

# 58. No UI-Only Completion

A UI that merely displays accounting concepts without working backend/domain behavior is not accepted.

Likewise:

> backend + API without the required user workflow is not accepted as complete for UI/UX-scoped requirements.

The end-to-end path must work.

```text
UI
 ↓
API
 ↓
Authorization
 ↓
Domain/Service
 ↓
Database
 ↓
Audit/Provenance
 ↓
Calculation/Reportability
 ↓
UI reflects final state
```

---

# 59. No Backend-Only Feature Flags

Creating:

```text
scope3_customer_enabled = true
```

without the corresponding user experience is not a completed feature.

If a capability is implemented, the UI must correctly:

- expose it when enabled;
- hide or explain it when disabled;
- enforce permissions;
- display resulting state.

---

# 60. No Duplicate UX Systems

Do not build:

```text
Customer Scope 3 UI
Consultant Scope 3 UI
Staff Scope 3 UI
```

as three unrelated applications.

Build shared accounting components with role/context-specific capabilities.

Conceptually:

```text
Scope 3 UI
   |
   +-- organization context
   +-- role
   +-- capability
   +-- delegated relationship
```

---

# 61. Shared UI Component Principle

Where appropriate, components should be reusable across:

- Staff
- Direct Customer
- Consultant
- Consultant Client

Examples:

- Activity table
- Evidence panel
- Calculation detail
- Factor detail
- Review item
- Exception panel
- Reportability status
- Audit history
- Supplier record

The data and available actions vary according to authorization.

---

# 62. Scope-Specific UX Must Still Be Real

Shared components do not mean all scopes are identical.

Scope 2 must expose its:

- location-based
- market-based
- contractual-instrument

distinctions.

Scope 3 must expose:

- 15 categories
- supplier relationships
- estimation/methodology
- category-specific workflows.

Scope 1 must expose its applicable direct-emissions activity domains.

---

# 63. Consultant UX Must Not Leak Client Data

Portfolio views must only show clients the consultant is authorized to access.

Client switching must revalidate authorization.

The UI must not rely on:

```text
?client_id=...
```

or similar client-side selection as the security boundary.

The backend/database must enforce the relationship.

---

# 64. Organization Ownership UX

Whenever practical, the UI should make data ownership clear.

Example:

```text
Data Owner:
ABC Manufacturing

Operator:
Green Advisory / Jane

Acting For:
ABC Manufacturing
```

This is particularly important in:

- evidence
- activity data
- supplier data
- calculations
- reports
- audit history

---

# 65. Report Ownership UX

A consultant-generated report for a client should display:

```text
Report Organization:
ABC Manufacturing

Prepared By:
Green Advisory

Accounting Period:
FY2026

Prepared:
2026-09-25
```

The report remains part of ABC's accounting context.

---

# 66. Consultant's Own Accounting Must Be Separate

A consultant must be able to switch between:

```text
MY ORGANIZATION
Green Advisory
```

and:

```text
CLIENT
ABC Manufacturing
```

These are distinct accounting contexts.

Green Advisory's Scope 1/2/3 must never mix with ABC's Scope 1/2/3.

---

# 67. Staff Multi-Organization UX

Staff can operate across organizations according to permissions.

The UI should provide:

```text
Organizations
   ↓
Select Organization
   ↓
Carbon Accounting
```

Staff must always see the current organization context.

---

# 68. Review/Approval Authority

The UI must not show approval controls merely because a user can see a record.

Approval is a separate capability.

Example:

```text
User can:
✓ View
✓ Edit
✓ Submit

User cannot:
✗ Approve
✗ Make Reportable
```

The UI should communicate this clearly.

---

# 69. Controlled Overrides

Where controlled overrides exist, the UI should make them explicit.

```text
┌───────────────────────────────────────────────┐
│ CONTROLLED OVERRIDE                           │
│                                               │
│ Existing Factor: ...                          │
│ Proposed Factor: ...                          │
│                                               │
│ Reason *                                      │
│ [_________________________________________]   │
│                                               │
│ Evidence *                                    │
│ [_________________________________________]   │
│                                               │
│ This action will be recorded in audit history.│
│                                               │
│ [ Cancel ]              [ Confirm Override ]  │
└───────────────────────────────────────────────┘
```

Do not create silent overrides.

---

# 70. Confirmation for Destructive/Accounting Actions

For actions such as:

- invalidate
- reject
- remove a relationship
- revoke delegated access
- supersede a result

the UI should provide explicit confirmation and explain downstream consequences.

---

# 71. Cline Verification Requirements

Cline must test at minimum:

## Staff

- organization selection
- accounting access
- review
- governance controls
- audit

## Direct customer

- own accounting
- enabled capabilities
- disabled capabilities
- evidence
- review
- reporting

## Consultant

- own accounting
- client portfolio
- client switching
- delegated access
- client-specific permissions

## Consultant client

- own accounting
- own users
- consultant access visibility
- delegated capability boundaries

## Security

- cross-tenant denial
- unauthorized client denial
- incorrect acting-for context denial
- backend authorization
- RLS where applicable

---

# 72. Acceptance: UI Must Reflect Actual Backend State

Examples:

If Scope 3 is disabled:

```text
UI = disabled/not available
Backend = denied
```

If consultant review is disabled:

```text
UI = no review action
Backend = denied
```

If reportability is not approved:

```text
UI = NOT FOR REPORTING
Backend = reportability state prevents reporting use
```

If a result is invalidated:

```text
UI = INVALIDATED
Backend = historical state preserved
```

---

# 73. Cline Completion Report

Every implementation task based on this standard must produce a Markdown report containing:

- unique task ID
- starting commit
- ending commit
- discovery results
- existing UI reused
- existing backend reused
- existing schema reused
- existing authorization reused
- new implementation
- UI/UX changes
- backend changes
- database changes
- API changes
- authorization/RLS changes
- consultant/client relationship changes
- tests
- screenshots/evidence where available
- known failures
- regressions
- remaining gaps
- exact files changed
- acceptance matrix
- final verdict

---

# 74. Mandatory Final UX Verdict

Cline must classify the UX implementation as one of:

- `UIUX_PASS`
- `UIUX_PARTIAL`
- `UIUX_FAIL`
- `UIUX_BLOCKED`

A `UIUX_PASS` requires:

1. Existing-vs-missing discovery completed.
2. Existing components reused where appropriate.
3. Required UI implemented.
4. Backend/domain behavior connected.
5. Authorization enforced.
6. Organization context correct.
7. Consultant delegated context correct.
8. Scope-specific UX implemented.
9. Disabled/error/loading/empty states implemented.
10. Relevant tests passed or failures explicitly classified.
11. No known Class-A defect.
12. Production remains untouched.

---

# 75. Product Owner Acceptance Principle

The goal is not maximum screen count.

The goal is a coherent carbon-accounting product in which:

- the right user sees the right organization;
- the right user sees the right accounting data;
- the right user can perform the right action;
- the wrong user cannot;
- the UI accurately communicates accounting state;
- Scope 1/2/3 are correctly differentiated;
- customers can contribute their own data;
- consultants can manage authorized clients;
- clients remain independent organizations;
- accounting history remains auditable;
- reporting only uses appropriate reportable results;
- existing CarbonTally functionality is reused rather than duplicated.

---

# 76. Final PO Decision

This ASCII UI/UX standard is an **acceptance reference for P17 CAMS implementation**.

Cline must not interpret it as an instruction to rebuild CarbonTally from scratch.

The required sequence is:

```text
DISCOVER
   ↓
MAP EXISTING
   ↓
IDENTIFY GAPS
   ↓
RECONCILE ARCHITECTURE
   ↓
IMPLEMENT BACKEND + UI/UX
   ↓
VERIFY
   ↓
REPORT
```

No production deployment is authorized.

---

# 77. Document Control

**Document ID:** `CT-PO-P17-UIUX-01-UNIFIED-CARBON-ACCOUNTING-UX-STANDARD`  
**Version:** 1.0.0  
**Status:** APPROVED PRODUCT-OWNER UI/UX STANDARD  
**Baseline:** `P17-ARCH-01-20250925-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT`  
**Related PO Decision:** `CT-PO-P17-POST-ARCH-DECISIONS-20260925`  
**Production:** NOT AUTHORIZED  
**Implementation:** Must follow discovery → reconciliation → implementation → verification → report
