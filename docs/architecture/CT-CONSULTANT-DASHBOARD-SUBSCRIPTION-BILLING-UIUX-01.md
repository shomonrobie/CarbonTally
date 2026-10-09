# CarbonTally Consultant Dashboard + Subscription & Billing UI/UX
## Product-owner review draft — v1

Status: DESIGN REVIEW ONLY  
No implementation decision is implied by this document.

---

# 1. Core consultant model

CarbonTally supports three consultant delivery modes:

1. **Consultant-operated**
   - Client has no CarbonTally login.
   - Consultant operates the Organisation.
   - Available to standard Consultant subscription.

2. **Co-Branded**
   - Consultant decides per client whether client access is OFF, READ_ONLY, COLLABORATIVE, or MANAGED.
   - Client-facing UI visibly carries consultant + CarbonTally branding.
   - Client access is an entitlement of the Co-Branded subscription.

3. **White-Label**
   - Same access choices as Co-Branded.
   - Client-facing UI is primarily the consultant's brand.
   - CarbonTally branding can be suppressed/replaced where the plan supports it.

The consultant remains the commercial customer and CarbonTally bills the consultant firm.

---

# 2. Consultant dashboard information architecture

```text
CONSULTANT FIRM
│
├── Dashboard
├── Clients
│   ├── All Clients
│   ├── Needs Attention
│   ├── Data Collection
│   ├── Processing
│   ├── Review
│   ├── Approval
│   └── Reporting
│
├── Team
├── Templates / Rules
├── Branding
│   ├── Co-Brand
│   └── White-Label
│
├── Subscription
├── Billing
└── Settings
```

---

# 3. MODE A — CONSULTANT-OPERATED

## 3.1 Dashboard

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  [CONSULTANT LOGO]  CarbonTally Consultant                     [User ▾]    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dashboard │ Clients │ Team │ Templates │ Branding │ Subscription │ Billing │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Good morning, Sarah                                                       │
│  Your client portfolio                                                     │
│                                                                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │ 24         │ │ 7          │ │ 5          │ │ 3          │               │
│  │ Clients    │ │ Data due   │ │ In review  │ │ Approval   │               │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘               │
│                                                                             │
│  CLIENT PORTFOLIO                                      [ + Add Client ]    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Client             Period       Status          Progress     Action   │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │ Acme Manufacturing FY2026       Data collection ███████░░ 78% [Open] │  │
│  │ Green Retail      FY2026        In review       █████████  100% [Open]│  │
│  │ Delta Logistics   FY2025        Approval        █████████  100% [Open]│  │
│  │ ABC Foods         FY2026        Attention       ████░░░░░  42% [Open] │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  NEEDS ATTENTION                                                           │
│  • 3 clients missing supplier data                                         │
│  • 2 calculation issues awaiting review                                    │
│  • 1 report awaiting approval                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key behaviour

Clicking `[Open]` enters the normal CarbonTally Organisation workspace.

```text
Consultant · Working on: Acme Manufacturing · GreenLeaf Consulting
```

The consultant is never forced into a separate "mini client dashboard".

---

# 4. MODE A — CLIENT WORKSPACE

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Consultant Logo]  CarbonTally                                             │
│                                                                             │
│ Consultant · Working on: Acme Manufacturing                                │
│ [← Client Portfolio]                                      [Client Context] │
├─────────────────────────────────────────────────────────────────────────────┤
│ Overview │ Data │ Documents │ Emissions │ Review │ Reports │ Organisation  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Acme Manufacturing                                                         │
│ FY2026 Carbon Footprint                                                     │
│                                                                             │
│ Scope 1          Scope 2          Scope 3          Total                    │
│ 1,240 tCO₂e      860 tCO₂e        3,420 tCO₂e     5,520 tCO₂e             │
│                                                                             │
│ Data completeness: 92%                                                     │
│                                                                             │
│ [Upload Data] [Run Processing] [Review Issues] [Generate Report]            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

No client login is required.

---

# 5. MODE B — CO-BRANDED

## 5.1 Consultant dashboard

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [CONSULTANT LOGO] × CarbonTally                               [User ▾]     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dashboard │ Clients │ Team │ Templates │ Branding │ Subscription │ Billing │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CLIENT PORTFOLIO                                                          │
│                                                                             │
│  Client               Access       Service Status        Client Login      │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Acme Manufacturing   Collaborative  In Review            ● Active        │
│  Green Retail         Read-only      Reporting             ● Active        │
│  Delta Logistics      No access      Processing             —              │
│  ABC Foods             Managed        Data collection       ● Active        │
│                                                                             │
│  [Open Client]   [Manage Access]   [Invite Client]                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 6. CO-BRANDED — MANAGE CLIENT ACCESS

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ ← Clients / Acme Manufacturing                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Client Access                                                               │
│                                                                             │
│ Client login                                             [ ON  ● ]          │
│                                                                             │
│ Access profile                                                              │
│                                                                             │
│   ( ) Read-only                                                             │
│   (●) Collaborative                                                        │
│   ( ) Managed                                                               │
│                                                                             │
│ ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│ Client users                                                                │
│                                                                             │
│  John Smith       john@acme.com       Contributor       [Edit]              │
│  Maria Khan       maria@acme.com      Viewer            [Edit]              │
│                                                                             │
│  [+ Invite client user]                                                     │
│                                                                             │
│ Consultant remains the service operator.                                   │
│ Client access does not change consultant permissions.                      │
│                                                                             │
│                                      [Cancel] [Save Access Settings]         │
└─────────────────────────────────────────────────────────────────────────────┘
```

The consultant can choose the access profile **per Organisation**.

---

# 7. CO-BRANDED — CLIENT VIEW

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [CLIENT LOGO]  ×  [CONSULTANT LOGO]                           [John ▾]     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Overview │ My Data │ Documents │ Emissions │ Reports │ Requests            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Acme Manufacturing                                                         │
│ FY2026 Carbon Accounting                                                    │
│                                                                             │
│ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                  │
│ │ 5,520          │ │ 92%            │ │ FY2026         │                  │
│ │ tCO₂e          │ │ Complete       │ │ In Progress    │                  │
│ └────────────────┘ └────────────────┘ └────────────────┘                  │
│                                                                             │
│ REQUESTS FROM YOUR CONSULTANT                                              │
│                                                                             │
│  ⚠ Supplier electricity invoices                    [Provide Data]          │
│  ⚠ Fleet fuel records                                [Upload]               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 8. MODE C — WHITE-LABEL

## 8.1 Consultant dashboard

The consultant-side dashboard can remain visibly connected to CarbonTally because the consultant is the CarbonTally customer.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [CONSULTANT BRAND]                                             [User ▾]     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Dashboard │ Clients │ Team │ Templates │ Branding │ Subscription │ Billing │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Your Carbon Accounting Practice                                            │
│                                                                             │
│  31 Active Clients   8 Data Due   6 In Review   4 Reports Ready            │
│                                                                             │
│  CLIENT PORTFOLIO                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Client             Access         Status             Progress          │  │
│  │ Acme               Collaborative  Data collection    ████████░         │  │
│  │ Green Retail       Read-only      Reporting          ██████████         │  │
│  │ Delta Logistics    Off            Processing         ██████░░░          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 9. WHITE-LABEL — CLIENT EXPERIENCE

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         [CONSULTANT LOGO]                                   │
│                                                                             │
│                    Carbon Accounting Portal                                 │
│                                                                             │
│                 Welcome back, John                                         │
│                 Acme Manufacturing                                         │
│                                                                             │
│                 ┌──────────────────────────────┐                            │
│                 │ Email                       │                            │
│                 └──────────────────────────────┘                            │
│                                                                             │
│                 ┌──────────────────────────────┐                            │
│                 │ Password                     │                            │
│                 └──────────────────────────────┘                            │
│                                                                             │
│                         [ Sign in ]                                         │
│                                                                             │
│                  Powered by [consultant brand]                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

The exact degree of CarbonTally identity suppression should be controlled by the white-label entitlement and branding configuration.

---

# 10. WHITE-LABEL — CLIENT DASHBOARD

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [CONSULTANT BRAND]                                           [John ▾]       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Overview │ Data │ Documents │ Emissions │ Reports │ Requests               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Welcome to your Carbon Accounting Portal                                   │
│ Acme Manufacturing                                                         │
│                                                                             │
│       FY2026 FOOTPRINT                                                      │
│                                                                             │
│             5,520 tCO₂e                                                     │
│                                                                             │
│      Scope 1       Scope 2       Scope 3                                    │
│      1,240         860           3,420                                      │
│                                                                             │
│  Your consultant: GreenLeaf Sustainability                                 │
│                                                                             │
│  NEXT ACTIONS                                                               │
│  [Provide supplier data]   [Upload evidence]   [View report]               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 11. Subscription page

## Consultant subscription overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Subscription                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ GreenLeaf Sustainability                                                    │
│                                                                             │
│ Current plan                                                               │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ CO-BRANDED                                                            │  │
│ │                                                                       │  │
│ │ Multi-client carbon accounting                                        │  │
│ │ Client access enabled                                                  │  │
│ │ Co-branded client experience                                           │  │
│ │                                                                       │  │
│ │ Renewal: 14 November 2026                              [Manage Plan]  │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ INCLUDED                                                                    │
│ ✓ Consultant client portfolio                                              │
│ ✓ Consultant team                                                         │
│ ✓ Client access controls                                                   │
│ ✓ Read-only client access                                                  │
│ ✓ Collaborative client access                                             │
│ ✓ Co-branding                                                              │
│ ✓ Carbon accounting workspace                                              │
│                                                                             │
│ WHITE-LABEL                                                               │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ White-label client portal                                               │  │
│ │ Custom client-facing branding                                           │  │
│ │ Custom domain where supported                                            │  │
│ │                                                                       │  │
│ │ [ Upgrade to White-Label ]                                             │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 12. Subscription comparison

The actual prices should NOT be hard-coded in the UI design until commercial pricing is approved.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONSULTANT PLAN COMPARISON                              │
├────────────────────────┬─────────────┬──────────────┬──────────────────────┤
│ Capability             │ Consultant  │ Co-Branded   │ White-Label          │
├────────────────────────┼─────────────┼──────────────┼──────────────────────┤
│ Consultant workspace   │ ✓           │ ✓            │ ✓                    │
│ Client portfolio       │ ✓           │ ✓            │ ✓                    │
│ Consultant RBAC        │ ✓           │ ✓            │ ✓                    │
│ Client login           │ —           │ ✓            │ ✓                    │
│ Client read-only       │ —           │ ✓            │ ✓                    │
│ Client collaborative   │ —           │ ✓            │ ✓                    │
│ Client managed         │ —           │ ✓            │ ✓                    │
│ Co-branding            │ —           │ ✓            │ ✓                    │
│ White-label            │ —           │ —            │ ✓                    │
│ Custom domain          │ —           │ Optional     │ Plan-dependent       │
│ Consultant billing     │ ✓           │ ✓            │ ✓                    │
└────────────────────────┴─────────────┴──────────────┴──────────────────────┘
```

---

# 13. Billing page

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Billing                                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ BILLING ACCOUNT                                                             │
│ GreenLeaf Sustainability                                                    │
│ Billing contact: finance@greenleaf.example                                 │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ CURRENT PLAN                                                           │  │
│ │ Co-Branded                                                             │  │
│ │                                                                       │  │
│ │ Subscription                         £XXX / month                      │  │
│ │ Next billing date                    14 Nov 2026                       │  │
│ │ Active managed clients               24                                │  │
│ │                                                                       │  │
│ │ [Change Plan] [Update Payment]                                        │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ USAGE / ENTITLEMENTS                                                        │
│                                                                             │
│ Managed clients                         24 / 30                            │
│ Consultant team members                  7 / 10                            │
│ Client-access Organisations              18 / 30                           │
│                                                                             │
│ INVOICES                                                                    │
│                                                                             │
│ 14 Oct 2026       INV-2026-0104      £XXX        [Download]               │
│ 14 Sep 2026       INV-2026-0093      £XXX        [Download]               │
│ 14 Aug 2026       INV-2026-0081      £XXX        [Download]               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 14. Change-plan flow

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Change subscription                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Current: Consultant                                                        │
│                                                                             │
│ ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────────────┐ │
│ │ Consultant        │  │ Co-Branded        │  │ White-Label             │ │
│ │                   │  │                   │  │                         │ │
│ │ Consultant-only   │  │ Client access     │  │ Client access           │ │
│ │                   │  │ Co-branding       │  │ White-label             │ │
│ │                   │  │                   │  │                         │ │
│ │ [Current]         │  │ [Choose]          │  │ [Choose]                │ │
│ └───────────────────┘  └───────────────────┘  └─────────────────────────┘ │
│                                                                             │
│ Existing clients and data are retained when changing plans.                │
│ Downgrades may disable features that the new plan does not include.        │
│ No Organisation or historical accounting data is deleted automatically.    │
│                                                                             │
│                                      [Cancel] [Continue]                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 15. Downgrade warning

A downgrade should explicitly show affected clients/features.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Downgrade impact                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ You currently have 18 client Organisations with client access enabled.     │
│                                                                             │
│ Your selected plan does not include client access.                         │
│                                                                             │
│ The following will happen:                                                 │
│                                                                             │
│ • Client logins will be disabled                                           │
│ • Client data will remain intact                                           │
│ • Consultant access remains available                                      │
│ • Co-branding configuration will be retained but inactive                 │
│ • No Organisation will be deleted                                          │
│                                                                             │
│ [Cancel downgrade]                         [Confirm downgrade]              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 16. Important UX principle

Do not show the client-access controls when the subscription does not permit them.

Instead:

```text
Client Access

[ Locked ]

Available with Co-Branded and White-Label plans.

[ View upgrade options ]
```

This is preferable to displaying a toggle that later fails at save time.

---

# 17. Organisation-level client access

Inside the consultant's client settings:

```text
CLIENT ACCESS

Subscription entitlement: ✓ Enabled

Client access                          [ ON ● ]

Access profile

  ○ Read-only
  ● Collaborative
  ○ Managed

Branding

  ● Co-Branded
  ○ White-Label

Client portal status                   Active

[Save changes]
```

The consultant decides this per client.

---

# 18. Final product architecture represented by the UI

```text
                          CARBONTALLY
                              │
             ┌────────────────┴────────────────┐
             │                                 │
      DIRECT CUSTOMERS                   CONSULTANT FIRMS
             │                                 │
      Organisation                    Firm Dashboard
             │                                 │
      Customer RBAC                   Consultant RBAC
                                               │
                                       Subscription
                                               │
                                  ┌────────────┴────────────┐
                                  │                         │
                              Clients                  Branding
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                  Client A      Client B      Client C
                    │             │             │
               Access OFF     Read-only     Collaborative
                    │             │             │
              Consultant      Consultant     Consultant
              operates        operates       operates
```

---

# 19. Design decisions still requiring Product Owner confirmation

Before implementation, explicitly confirm:

1. Exact consultant plan names.
2. Exact commercial pricing.
3. Whether "Managed" client access is included in Co-Branded and White-Label.
4. Whether custom domains are included in White-Label or a higher tier.
5. Consultant client limits.
6. Consultant team-member limits.
7. Storage/document limits if subscription-based.
8. Whether clients can approve/finalize when assigned the Managed profile.
9. Whether client users can invite additional client users.
10. Whether former consultants retain optional read-only access after handover.
11. Exact white-label degree (login, emails, reports, exports, domain, support/legal identity).

These are commercial/product details and should not be invented by implementation agents.
