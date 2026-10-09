# CarbonTally Organisation Workspace — Refactored UI/UX
## Based on current Organisation workspace screenshot + approved consultant model

Status: Product/UX design review only
Source reviewed: `organization-workspace-1.pdf`, current CarbonTally V3 customer workspace screenshot.

---

# 1. What exists today

The current CarbonTally Organisation shell contains:

- Home
- Documents
- Processing
- Manual processing
- Review & approve
- Emissions
- Reports
- Issues
- Billing
- Organisation
- Messaging
- Insight
- Existing data
- Capabilities
- Notifications

The current Home page contains:

- Ready reports
- Queued reports
- Documents
- Members
- Emissions rows
- Total tCO2e
- Reporting overview
- Monthly emissions trend
- Activity by member
- Quick actions
- Latest reports

This is a strong operational foundation.

The goal is NOT to replace it with a separate consultant application.

---

# 2. Main UX problem

The current workspace assumes:

```text
Current model

User
  ↓
Organisation
  ↓
Organisation workspace
```

The new model requires:

```text
Direct customer

User
  ↓
Organisation
  ↓
Organisation workspace


Consultant

Consultant Firm
  ↓
Consultant User
  ↓
Managed Organisation
  ↓
Same Organisation workspace
```

Therefore the same workspace must support both contexts without duplicating the product.

---

# 3. Refactored global architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ CarbonTally / Consultant Brand                              User ▾          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ FIRM / ORGANISATION CONTEXT                                                │
│                                                                             │
│ [Consultant Firm ▾]   [Working on: Acme Manufacturing ▾]                   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dashboard │ Data │ Processing │ Review │ Emissions │ Reports │ Issues       │
│ Organisation │ Messages │ Insight │ Existing data │ Notifications           │
└─────────────────────────────────────────────────────────────────────────────┘
```

The critical addition is the persistent context selector.

For a direct customer:

```text
[Acme Manufacturing]
```

For a consultant:

```text
[GreenLeaf Consulting ▾]
[Working on: Acme Manufacturing ▾]
```

---

# 4. Consultant navigation should be separated into two planes

The consultant needs:

```text
FIRM PLANE
├── Dashboard
├── Clients
├── Team
├── Templates / Rules
├── Branding
├── Subscription
├── Billing
└── Firm Settings

CLIENT / ORGANISATION PLANE
├── Home
├── Data / Documents
├── Processing
├── Review
├── Emissions
├── Reports
├── Issues
├── Organisation
├── Messaging
├── Insight
└── Existing Data
```

Do not mix firm billing/settings with client Organisation billing/settings.

---

# 5. Proposed consultant shell

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [GreenLeaf Logo] CarbonTally                                  [Sarah ▾]    │
├─────────────────────────────────────────────────────────────────────────────┤
│ FIRM                                                                        │
│                                                                             │
│ Dashboard   Clients   Team   Templates   Branding   Subscription   Billing │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ WORKING ON                                                                  │
│                                                                             │
│ [ Acme Manufacturing ▾ ]                            [← Back to Clients]    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Home │ Documents │ Processing │ Review │ Emissions │ Reports │ Issues       │
│      │ Manual processing │ Organisation │ Messaging │ Insight │ Existing    │
├─────────────────────────────────────────────────────────────────────────────┤
```

The user should always know:

1. Which consultant firm they are operating under.
2. Which Organisation they are currently operating.
3. Whether they are in the firm plane or Organisation plane.

---

# 6. Organisation Home — recommended refactor

The existing Home should become a more actionable operational dashboard.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Home                                                                         │
│ Acme Manufacturing · FY2026                                                 │
│ Consultant · GreenLeaf Consulting                                           │
│                                                                             │
│ [Change client ▾]                                      [Client access ▸]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA HEALTH                                                                │
│                                                                             │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │
│ │ 92%          │ │ 18           │ │ 5            │ │ 3                  │  │
│ │ Completeness │ │ Documents    │ │ Open issues  │ │ Awaiting client    │  │
│ └──────────────┘ └──────────────┘ └──────────────┘ └────────────────────┘  │
│                                                                             │
│  EMISSIONS                                                                  │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ FY2026 total                                                            │ │
│ │                                                                         │ │
│ │ 5,520 tCO2e                                                             │ │
│ │                                                                         │ │
│ │ Scope 1        Scope 2        Scope 3                                   │ │
│ │ 1,240          860            3,420                                     │ │
│ │                                                                         │ │
│ │ [View emissions] [View trend]                                           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  WORKFLOW STATUS                                                            │
│                                                                             │
│ Data collection   ████████████████░░ 92%                                   │
│ Processing        ██████████████████ 100%                                  │
│ Review            ██████████████░░░░ 78%                                   │
│ Approval          ████████████░░░░░░ 65%                                   │
│ Reporting         ██████████░░░░░░░░ 52%                                   │
│                                                                             │
│  NEEDS ATTENTION                                                            │
│  ⚠ 5 items need mapping                                                    │
│  ⚠ 3 client data requests unanswered                                       │
│  ⚠ 1 calculation issue                                                     │
│                                                                             │
│  QUICK ACTIONS                                                              │
│  [Upload data] [Process data] [Review issues] [Generate report]            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 7. Why this is better than the current Home

The current screenshot gives strong summary metrics, but the workflow state is fragmented.

The new Home answers immediately:

1. How complete is the accounting?
2. What is the current footprint?
3. What stage is the engagement at?
4. What is blocked?
5. What should I do next?
6. If I am a consultant, is the client waiting for something?

This is particularly important for a consultant managing 10–50 Organisations.

---

# 8. Consultant portfolio dashboard

The firm-level Dashboard should NOT duplicate the Organisation Home.

It should answer:

> Which clients need my attention?

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Consultant Dashboard                                                       │
│ GreenLeaf Consulting                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 24 Active Clients   7 Data Due   5 In Review   3 Approval   4 Reports      │
│                                                                             │
│ CLIENT WORKFLOW                                                            │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Client             Stage          Health       Due        Action        │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ Acme Manufacturing  Review         ● Good       8 Oct      Open          │ │
│ │ Green Retail        Data           ● Attention  7 Oct      Open          │ │
│ │ Delta Logistics     Approval       ● Good       9 Oct      Open          │ │
│ │ ABC Foods           Processing     ● Blocked    6 Oct      Open          │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ FILTER: [All ▾] [Needs attention] [Data] [Review] [Approval] [Reporting]   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 9. Client switcher

Do NOT force consultants to return to the portfolio every time they switch Organisations.

```text
┌─────────────────────────────────────────────────────────────┐
│ WORKING ON                                                  │
│                                                             │
│ 🔎 Search clients...                                       │
│                                                             │
│ ★ Recent                                                   │
│   Acme Manufacturing       Review                          │
│   Green Retail             Reporting                       │
│                                                             │
│ All clients                                                │
│   ABC Foods                Data collection                 │
│   Delta Logistics          Approval                        │
│   Northstar Energy         Processing                      │
│                                                             │
│ [Open client portfolio]                                    │
└─────────────────────────────────────────────────────────────┘
```

The switcher must only return authorised consultant-client relationships.

---

# 10. Client access control

Place this under the consultant's client settings, not in the normal Organisation navigation.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Client Access                                                               │
│ Acme Manufacturing                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Subscription entitlement                                                   │
│ ✓ Co-Branded — Client access enabled                                       │
│                                                                             │
│ Client portal                                              [ ON ● ]         │
│                                                                             │
│ Access profile                                                             │
│                                                                             │
│ ○ Read-only                                                                │
│ ● Collaborative                                                            │
│ ○ Managed                                                                  │
│                                                                             │
│ Client users                                                               │
│                                                                             │
│ John Smith      Contributor          Active                                │
│ Maria Khan      Viewer               Active                                │
│                                                                             │
│ [Invite user]                                                              │
│                                                                             │
│ The consultant remains the service operator.                               │
│ Client access does not change consultant permissions.                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 11. Organisation navigation refactor

The current navigation is too flat.

Instead of treating every item equally:

```text
Home
Documents
Processing
Manual processing
Review & approve
Emissions
Reports
Issues
Billing
Organisation
Messaging
Insight
Existing data
Capabilities
Notifications
```

use logical groups.

```text
WORKSPACE

Home

DATA
  Documents
  Existing data
  Manual processing
  Processing

ACCOUNTING
  Emissions
  Issues

REVIEW & REPORTING
  Review & approve
  Reports

COLLABORATION
  Messaging
  Notifications
  Insight

ORGANISATION
  Organisation
  Capabilities

COMMERCIAL
  Billing
```

For consultant-managed Organisations, hide client billing if billing belongs to the consultant firm.

---

# 12. Processing workspace

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Processing · Acme Manufacturing                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ [All] [Queued] [Processing] [Needs review] [Complete]                     │
│                                                                             │
│ 18 documents · 5 processing items · 3 need attention                      │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Document          Source       Status        Mapping       Action       │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ Electricity.pdf   Supplier     Needs review  82%          [Review]      │ │
│ │ Fleet.xlsx        Manual       Processing    —            [View]        │ │
│ │ Waste.pdf         Supplier     Complete      100%         [View]        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ [Upload documents] [Create processing batch]                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 13. Review & approval

The existing "Review & approve" should become a true workflow.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Review & Approve · Acme Manufacturing                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ REVIEW QUEUE                                                               │
│                                                                             │
│ 5 Items require review                                                     │
│                                                                             │
│ [Data] [Mapping] [Calculation] [Report]                                    │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ Item                 Severity      Owner          Status                │ │
│ ├─────────────────────────────────────────────────────────────────────────┤ │
│ │ Electricity mapping  High          Sarah          Open                  │ │
│ │ Waste route          Medium        John           Open                  │ │
│ │ Fleet calculation    Low           Sarah          Resolved              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ REPORT APPROVAL                                                            │
│                                                                             │
│ FY2026 Carbon Report                                                       │
│ Status: Ready for approval                                                 │
│                                                                             │
│ [View report]                                      [Approve report]          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

For consultant-managed mode, the Approve action is available only to authorised consultant approver/admin roles.

For collaborative client access, it is separately controlled by client RBAC.

---

# 14. Organisation settings

Current Organisation settings should become a proper administration centre.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Organisation                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Overview   Members   Locations   Facilities   Assets   Suppliers   Factors │
│                                                                             │
│ PROFILE                                                                     │
│ Company name        Acme Manufacturing                                      │
│ Reporting period    FY2026                                                 │
│ Country             United Kingdom                                         │
│                                                                             │
│ MEMBERS                                                                     │
│ John Smith          Client Admin                                            │
│ Maria Khan          Contributor                                             │
│                                                                             │
│ CONSULTANT RELATIONSHIP                                                     │
│ Managed by          GreenLeaf Consulting                                   │
│ Service mode        Co-Branded                                              │
│ Client access       Collaborative                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 15. Direct customer mode

The same Organisation workspace should work without consultant context.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ CarbonTally                                                     [User ▾]   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Acme Manufacturing                                                         │
│                                                                             │
│ Home │ Documents │ Processing │ Review │ Emissions │ Reports │ Issues      │
│ Organisation │ Messaging │ Insight │ Notifications                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Home                                                                        │
│ Acme Manufacturing                                                         │
│                                                                             │
│ [same operational dashboard]                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

No consultant-specific controls should appear.

---

# 16. Consultant-managed Organisation

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Consultant Brand] CarbonTally                                  [Sarah ▾]  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Consultant Firm: GreenLeaf Consulting                                      │
│ Working on: Acme Manufacturing                                  [Change ▾] │
├─────────────────────────────────────────────────────────────────────────────┤
│ Home │ Documents │ Processing │ Review │ Emissions │ Reports │ Issues       │
│ Organisation │ Messaging │ Insight │ Existing Data                         │
├─────────────────────────────────────────────────────────────────────────────┤
```

This is the core reusable shell.

---

# 17. Co-branded client workspace

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [CLIENT LOGO] × [CONSULTANT LOGO]                              [John ▾]   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Overview │ My Data │ Documents │ Emissions │ Reports │ Requests             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Acme Manufacturing                                                         │
│ FY2026                                                                     │
│                                                                             │
│ 5,520 tCO2e       92% complete       3 requests outstanding               │
│                                                                             │
│ YOUR CONSULTANT                                                            │
│ GreenLeaf Consulting                                                       │
│                                                                             │
│ NEXT ACTION                                                                │
│ [Provide electricity data]                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

Client users should NOT see consultant-only functions such as:

- Subscription
- Billing
- Firm Team
- Consultant Clients
- Consultant Branding
- White-label settings

---

# 18. White-label client workspace

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [CONSULTANT BRAND]                                             [John ▾]    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Overview │ Data │ Documents │ Emissions │ Reports │ Requests                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Welcome to your Carbon Accounting Portal                                   │
│ Acme Manufacturing                                                         │
│                                                                             │
│ FY2026 footprint                                                           │
│ 5,520 tCO2e                                                                │
│                                                                             │
│ [Provide data] [Upload evidence] [View report]                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 19. Important distinction: firm dashboard vs Organisation dashboard

Do not merge these.

```text
CONSULTANT FIRM DASHBOARD

"What is happening across all my clients?"

        ↓

CLIENT PORTFOLIO

"What needs my attention?"

        ↓

ORGANISATION WORKSPACE

"What is happening inside this client's carbon account?"

        ↓

WORKFLOW PAGE

"What exactly do I need to do?"
```

This hierarchy should guide the entire frontend refactor.

---

# 20. Recommended desktop navigation

```text
FIRM LEVEL

Dashboard
Clients
Team
Templates
Branding
Subscription
Billing
Settings


ORGANISATION LEVEL

Home
Data
  Documents
  Existing data
  Manual processing
  Processing

Accounting
  Emissions
  Issues

Review & Reporting
  Review & approve
  Reports

Collaboration
  Messaging
  Insight
  Notifications

Organisation
  Overview
  Members
  Locations
  Facilities
  Assets
  Suppliers
  Factors
```

---

# 21. Mobile/responsive principle

Do not attempt to display the complete desktop navigation on mobile.

Use:

```text
┌──────────────────────────────┐
│ ☰   Acme Manufacturing   ▾  │
├──────────────────────────────┤
│                              │
│ Home                         │
│                              │
│ 5,520 tCO2e                  │
│ 92% complete                 │
│                              │
│ [Next action]                │
│                              │
├──────────────────────────────┤
│ Home   Data   Review   More  │
└──────────────────────────────┘
```

The consultant client switcher remains accessible from the top context control.

---

# 22. Product design principle

Do not create:

```text
Consultant Product
+
Client Product
+
Organisation Product
```

Create:

```text
CarbonTally Platform
│
├── Firm Context
│
├── Organisation Context
│
└── User Context
```

The same Organisation workspace is reused.

Access and navigation are dynamically controlled by:

- user type
- firm membership
- consultant role/capabilities
- client membership/role
- consultant-client relationship
- subscription entitlement
- client access profile
- branding mode

---

# 23. Refactor priorities

## P0

1. Context-aware application shell
2. Consultant client switcher
3. Firm vs Organisation navigation
4. Capability-aware navigation
5. Consultant-aware Organisation authorization
6. Client access entitlement
7. Client access profiles
8. Correct consultant processing/upload/review/approval workflow

## P1

9. Organisation Home redesign
10. Consultant portfolio dashboard
11. Client access settings
12. Organisation settings redesign
13. Review workflow redesign
14. Processing workflow redesign

## P2

15. Co-branding UI
16. White-label UI
17. Subscription UX
18. Billing UX
19. Upgrade/downgrade flows
20. Client handover UX

---

# 24. Do not implement yet

The following require Product Owner approval before coding:

- exact plan names
- exact pricing
- exact usage limits
- exact client role names
- exact consultant role names
- whether Managed client access can approve reports
- client invitation rules
- white-label custom domain
- white-label email identity
- post-handover consultant access

---

# 25. Final recommended UX architecture

```text
                           CARBONTALLY
                               │
                ┌──────────────┴──────────────┐
                │                             │
          DIRECT CUSTOMER              CONSULTANT FIRM
                │                             │
          Organisation                 Firm Dashboard
                │                             │
        Organisation UX              Client Portfolio
                                              │
                                  ┌───────────┼───────────┐
                                  │           │           │
                               Client A    Client B    Client C
                                  │           │           │
                               OFF       READ-ONLY   COLLABORATIVE
                                  │           │           │
                                  └───────────┴───────────┘
                                              │
                                  SAME ORGANISATION WORKSPACE
                                              │
                           ┌──────────────────┼──────────────────┐
                           │                  │                  │
                         Data             Accounting          Reporting
                           │                  │                  │
                     Documents         Emissions/Issues     Review/Reports
                           │
                     Processing
                           │
                    Organisation
```

The consultant layer should therefore be a **context and portfolio layer around the existing Organisation product**, not a separate replacement product.
