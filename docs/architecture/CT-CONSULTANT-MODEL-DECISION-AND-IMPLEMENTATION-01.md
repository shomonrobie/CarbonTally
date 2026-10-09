# CT-CONSULTANT-MODEL-DECISION-AND-IMPLEMENTATION-01

**Status:** PRODUCT OWNER DECISION BASELINE — IMPLEMENTATION AUTHORIZED
**Date:** 2026-10-06
**Purpose:** Establish the final CarbonTally consultant/partner operating model, benchmark it against current carbon-accounting platforms, and provide the implementation mandate for Cline.

---

## 1. Executive Decision

CarbonTally shall support consultants as a first-class commercial customer and service operator.

A consultant-managed client is a **normal CarbonTally Organisation**, not a reduced or separate mini-product.

The commercial and access model is:

```text
DIRECT CUSTOMER
CarbonTally -> Organisation -> Customer Team

CONSULTANT CUSTOMER
CarbonTally -> Consultant Firm -> Consultant Team -> Managed Organisations
```

The consultant firm pays CarbonTally for consultant-managed service. The managed client is not independently billed by CarbonTally while the consultant relationship is active.

Consultant-side permissions are controlled by consultant RBAC/capabilities. Consultant employees are **not** inserted into `organization_members` merely because they manage a client Organisation.

Client access is a separate, optional access plane and is controlled by the consultant's commercial subscription and per-client choice.

---

## 2. Final Subscription / Client Access Policy

### 2.1 Standard Consultant subscription

Client login/access is **not permitted**.

The consultant operates the client's Organisation on behalf of the client.

```text
Consultant -> full authorised service operation -> Client Organisation
Client -> no CarbonTally login
```

### 2.2 Co-Branded subscription

Client access is permitted.

The consultant decides, per managed Organisation, whether client access is enabled and what permitted client access profile is assigned.

The CarbonTally platform enforces that the subscription permits client access.

### 2.3 White-Label subscription

Client access is permitted.

The consultant decides, per managed Organisation, whether client access is enabled and what permitted client access profile is assigned.

White-label removes/replaces CarbonTally presentation according to the subscription/branding configuration: logo, colours, domain/login presentation, reports/exports/emails where supported.

### 2.4 Client access is not a binary "full access" flag

Client access shall use RBAC/capabilities.

Minimum conceptual profiles:

| Client profile | Typical capabilities |
|---|---|
| `NONE` | No client login/access |
| `READ_ONLY` | Dashboards, emissions, reports, historical results, permitted downloads |
| `COLLABORATIVE` | Read-only + submit data/evidence, upload permitted documents, answer requests, comments/review participation |
| `MANAGED` | Organisation administration and operational capabilities permitted to the client role; review/approval according to role |

The exact persisted role/capability names must be derived from the existing CarbonTally authorization model rather than invented independently.

The consultant may choose only profiles enabled by its subscription and platform policy.

---

## 3. Consultant Authority Model

A consultant-managed Organisation is fully operational.

The consultant firm may perform the complete carbon-accounting service according to its consultant RBAC, including where authorized:

- organisation/profile data management
- locations/facilities/assets/vehicles and similar master data
- supplier/custom-factor management where supported
- document upload and evidence collection
- manual extraction / batch processing
- imports and mappings
- emissions calculations
- review
- issue management
- report generation
- report lifecycle operations
- **final approval**
- client communication/messaging
- organisation/team administration where the consultant role permits it

The consultant does **not** receive all permissions merely by having a consultant-client relationship.

Required authorization dimensions are:

1. active consultant firm membership
2. active consultant-client relationship/grant
3. target Organisation
4. target tenant is live/not suspended
5. consultant role/capability permits the requested action
6. target resource belongs to the target Organisation
7. any additional platform/security boundary is satisfied

A capability-blind `is_org_consultant` admission path is unacceptable.

---

## 4. Direct Customer vs Consultant-Managed Final Approval

This supersedes the earlier assumption that consultant-managed final approval must remain customer-only.

### Direct customer mode

Existing direct-customer approval rules remain intact unless the final implementation explicitly identifies a separate PO decision.

### Consultant-managed mode

An appropriately authorized consultant role may perform final approval because the consultant is the service operator and commercial CarbonTally customer.

Approval must remain capability/role controlled. It must not become an implicit permission for every consultant member.

If the current capability model lacks a clean approval capability, Cline shall inspect the existing RBAC design and introduce the minimum coherent capability/role mapping needed rather than bypassing RBAC.

---

## 5. Consultant vs Organisation Membership

Keep these concepts separate:

```text
organization_members
    = customer/client organisation membership

consultant firm members / roles
    = consultant-side identity and permissions

consultant_clients
    = consultant firm <-> managed Organisation relationship
```

Do not add consultant employees to `organization_members` merely to make authorization work.

---

## 6. Relationship Modes

The platform should support these relationship states conceptually:

### A. Consultant-operated

```text
Consultant operates Organisation
Client access = OFF
```

This is available to standard consultant subscriptions and is the default service-delivery mode.

### B. Collaborative

```text
Consultant operates Organisation
Client access = ON
Client profile = READ_ONLY / COLLABORATIVE / MANAGED as permitted
```

Available to Co-Branded and White-Label subscriptions.

### C. Client handover / direct customer transition

When a client ends the consultant relationship and becomes a direct CarbonTally customer:

- retain the same Organisation
- retain historical data
- retain documents/evidence
- retain calculations and factor mappings
- retain reports
- retain audit history
- change the commercial/access relationship
- do not migrate/copy data into a new Organisation
- optionally allow the former consultant read-only/advisor access if commercially and technically supported

This is a relationship/access transition, not a data migration.

---

## 7. Commercial Model

### Consultant billing

CarbonTally bills the consultant firm for consultant-managed service according to its subscription/entitlement model.

### Managed client billing

A managed client is not independently billed by CarbonTally while it remains under the consultant-managed commercial relationship.

### Direct customer conversion

If the client becomes a direct CarbonTally customer, the commercial relationship changes and direct-customer billing/plan rules apply. The Organisation and data remain intact.

### Billing security

A managed client must not gain access to consultant-firm billing merely because a consultant relationship grants access to its Organisation.

Conversely, authorized consultant-firm users should retain access to the firm-level billing/subscription plane appropriate to their firm role.

---

## 8. Consultant Portfolio / Firm UX

CarbonTally should have two distinct UI planes.

### Consultant firm plane

Examples:

- Consultant Dashboard / Cockpit
- Clients
- Client portfolio/status
- Team
- Roles & permissions
- Firm branding
- Co-branding / white-label configuration
- Templates / reusable configuration where supported
- Subscription
- Firm billing
- Firm-level settings

### Managed Organisation plane

A selected client should open the normal CarbonTally Organisation workspace, not a reduced `ClientWorkspace` mini-dashboard.

The UI should maintain clear context such as:

> Consultant · Working on: Client Organisation · Firm Name

The consultant should be able to switch between authorised client Organisations without losing tenant isolation.

---

## 9. Client UX for Co-Branded / White-Label

If client access is enabled:

### Read-only

Client can see permitted:

- dashboard
- emissions results
- reporting periods
- reports
- historical results
- evidence/results permitted by the consultant configuration

No mutation capabilities outside the assigned role.

### Collaborative

Client can additionally:

- submit requested activity data
- upload permitted evidence/documents
- respond to data requests
- participate in review/comment workflows
- see processing status

### Managed

Client can additionally operate permitted Organisation functions through client RBAC.

Do not equate `MANAGED` with unrestricted platform administration. Security-sensitive platform/tenant operations remain governed by explicit platform boundaries.

---

## 10. Branding / Co-Branded / White-Label UX

Subscription entitlement must control access to branding features.

### Standard Consultant

No client-facing co-brand/white-label experience.

### Co-Branded

Support, where implemented:

- consultant brand + CarbonTally identity
- firm logo
- colours/theme
- branded reports/exports/emails where supported
- client-facing branding configuration

### White-Label

Support, where implemented:

- consultant brand as primary identity
- custom domain where supported
- branded login/entry experience
- branded application shell
- branded reports/exports/emails
- removal/minimization of CarbonTally visual identity according to plan

Branding must be tenant/firm scoped and must never permit cross-tenant leakage.

---

## 11. External Benchmark — Current Carbon Accounting Market

The benchmark is directional product research, not a claim that competitors implement identical RBAC internally.

| Platform | Consultant / partner model | Multi-client operation | Client access | Branding / white-label | Key lesson for CarbonTally |
|---|---|---|---|---|---|
| **Greenly Pro** | Partner licence for ESG consultants | Yes; consultant cockpit / multiple projects | Collaborative consultant + client workspaces | Custom branding | Consultant cockpit + collaborative client workspace is a strong reference model |
| **Gaia** | Refer, run Gaia as part of consultant service, or API | Yes; client book | Enterprise supports clients in same account; consultant can access client account | Full white-label at Enterprise | Strongest reference for consultant-owned client book + optional client access + white-label |
| **Avarni** | Partner-centric consultant model | Yes | View-only interactive reports explicitly offered | Firm logo/colour branding; white-label feature | Validates read-only client access as a useful consultant option |
| **Carbonly.ai** | Platform underneath consulting practice | Yes; N client tenants | Auditor/client access and handover patterns | White-label exports | Strong reference for consultant-owned multi-tenant architecture and role-based handover |
| **Persefoni Pro** | Consultant network / licensed platform | Consultant serves multiple client engagements | Client empowerment is part of positioning; exact client RBAC not publicly specified in reviewed source | Not established as the primary benchmark in reviewed material | Validates consultant licensing as a commercial model |
| **Normative** | Software + expert/managed services model | Enterprise/multi-org use cases | Client-side operational control is emphasized in direct-customer model | Not a primary consultant white-label benchmark in reviewed material | Validates software + managed service hybrid, but not a reason to copy its exact consultant model |

### Research evidence

- Greenly Pro currently advertises custom branding, a Consultant Cockpit for centralized oversight of 10+ projects, and collaborative expert workspaces with consultant/client access. Source: Greenly Partners.
- Gaia currently advertises three partner paths: referral, offering Gaia as part of the consultant's own service, and API integration. Gaia also states that its partner client book supports direct client-account access, audit-logged access, reusable libraries, and complete white-labeling. Enterprise supports multiple logins and client access.
- Avarni currently advertises consultant-focused carbon accounting, firm branding, and view-only access to interactive reports for clients.
- Carbonly currently describes one consulting workspace with multiple isolated client organisations, client tenant switching, white-label outputs, an auditor read-only workspace, and handover from consultant-owned to client-owned workspace without data migration.
- Persefoni currently advertises a Pro Consultant Network allowing consultants to use the platform to calculate client Scope 1–3 emissions.

---

## 12. Product Decisions Now Binding

The following decisions are binding for implementation unless superseded by a later Product Owner Decision Register entry:

1. Consultant firms are first-class CarbonTally commercial customers.
2. Consultant-managed clients are normal CarbonTally Organisations.
3. Consultant employees are not inserted into `organization_members` for authorization convenience.
4. Consultant-client access is relationship-based plus capability/role-based.
5. Consultant authorization must be capability-aware; relationship membership alone is insufficient.
6. Consultant roles can perform the complete service workflow when their capabilities authorize it.
7. Consultant-managed final approval is allowed for an authorized consultant role.
8. Direct-customer approval rules remain distinct from consultant-managed approval.
9. Standard Consultant subscription does not permit client login/access.
10. Co-Branded subscription permits client access.
11. White-Label subscription permits client access.
12. Under Co-Branded and White-Label, the consultant chooses per client whether access is OFF, READ_ONLY, COLLABORATIVE, or a permitted MANAGED profile.
13. Client access is governed by RBAC/capabilities, not a binary full-access flag.
14. Subscription entitlement must gate client access and branding features.
15. Consultant firm billing is separate from managed-client Organisation access.
16. Managed clients cannot access consultant-firm billing merely through client relationship access.
17. Client handover to direct CarbonTally customer is an access/commercial relationship transition, not data migration.
18. Historical data, evidence, calculations, reports and audit history remain with the same Organisation during handover.
19. The consultant workspace/client cockpit and Organisation workspace are distinct UI planes.
20. The managed Organisation workspace should reuse the normal CarbonTally Organisation surface rather than a consultant-only mini-product.
21. Co-Branded and White-Label branding must be subscription-gated and tenant-safe.
22. Cross-tenant isolation remains non-negotiable.
23. Legacy `/api/documents/*` is not required for V3 parity if the V3 workspace does not use it.
24. No production/hosted Supabase/Render access is permitted for this implementation task unless explicitly authorized.

---

## 13. Implementation Scope — This Is a Cross-Cutting Refactor

Do **not** treat this as a small consultant-route patch.

Cline shall first inspect the current repository and produce an implementation map covering at minimum:

### A. Database / schema

Inspect and, where required, refactor/add:

- consultant firms
- consultant firm members
- consultant roles/capabilities
- consultant-client relationships
- relationship status
- client access entitlement/profile
- subscription plan/entitlement model
- co-branding settings
- white-label settings
- domains/host configuration if already supported
- organisation ownership/commercial relationship representation
- handover state/history if needed
- audit events for relationship/access/branding changes

Do not create redundant parallel organisation models.

Prefer additive, backward-compatible migrations.

Do not destroy existing data.

### B. Authorization

Create or refactor a coherent authorization layer that evaluates:

- consultant firm membership
- consultant role/capability
- active consultant-client grant
- target Organisation
- tenant liveness
- requested action
- resource ownership/tenant scope

Avoid a generic consultant bypass such as:

```text
is_org_consultant == true -> allow everything
```

The existing direct customer authorization path must remain regression-safe.

### C. Processing

Fix the currently identified manual-processing parity gap so authorized consultant roles can perform processing through the existing pipeline.

Do not duplicate the customer pipeline for consultants.

### D. Documents / evidence

Fix the consultant document upload/evidence path for roles with the appropriate upload capability.

Resolve application authorization and RLS/service-role interaction coherently.

Do not weaken tenant isolation merely to make the endpoint pass.

### E. Organisation management

Bring consultant capabilities into parity for normal Organisation operations where the PO model permits them, including relevant master-data operations.

Use role/capability controls rather than owner-only shortcuts.

### F. Review / report lifecycle / approval

Implement consultant-managed review and final approval according to consultant capability.

Do not preserve the obsolete rule that only direct customer owners/admins can finalize consultant-managed work.

### G. Subscription / entitlement

Subscription must become an authorization input for:

- client login/access
- client access profiles
- co-branding
- white-label branding
- relevant domains/branding controls
- consultant portfolio/client limits if the existing commercial model defines them

Do not hard-code plan checks throughout individual routes. Prefer a central entitlement service/policy.

### H. UI/UX

Refactor the consultant shell and client workspace so that:

- consultant portfolio/cockpit is separate from managed Organisation workspace
- selected client context is persistent and unmistakable
- client switching is supported only among authorized Organisations
- normal Organisation pages are reused
- unavailable client-access features are hidden/disabled based on subscription
- consultant roles see only permitted actions
- client roles see only permitted client actions

### I. Co-Branded UI/UX

Implement or refactor subscription-aware:

- branding settings
- preview where appropriate
- branded client shell
- reports/exports/email branding hooks where existing architecture supports them
- clear fallback to CarbonTally identity when branding is not entitled

### J. White-Label UI/UX

Implement/refactor the white-label architecture as a first-class tenant/firm branding layer rather than ad-hoc CSS overrides.

Consider:

- firm identity
- logo
- colours/theme tokens
- favicon
- login/entry presentation
- custom domain architecture if currently supported or planned
- report/export/email branding
- safe fallback
- tenant isolation

### K. Billing

Verify and, where required, refactor:

- consultant firm subscription/billing
- managed-client billing denial
- entitlement checks
- plan upgrade/downgrade behaviour
- client access activation/deactivation based on plan

Do not assume that current billing tests prove consultant-firm billing is complete; independently verify it.

### L. Handover

Design/implement the smallest coherent mechanism for:

```text
CONSULTANT-MANAGED
        ↓
relationship ends / client converts
        ↓
DIRECT CUSTOMER
```

Preserve the Organisation identity and historical records.

If full UI for conversion is outside safe implementation scope, document the gap explicitly rather than inventing a destructive migration.

---

## 14. Required Test Matrix

Cline must add/update automated tests covering at minimum:

### Consultant roles

- consultant owner: expected broad permissions
- consultant admin/manager: expected management permissions
- processing/data operator: processing/upload permissions only as defined
- reviewer: review permissions
- approver: final approval permission
- viewer/no-capability consultant: denied mutation and denied access where no read capability exists

### Client profiles

- access OFF
- read-only
- collaborative
- managed

### Subscription gating

- standard consultant cannot enable client access
- co-branded can enable permitted client access
- white-label can enable permitted client access
- downgrade disables/removes unavailable entitlements safely without deleting data

### Tenant isolation

- consultant cannot access foreign Organisation
- consultant cannot access revoked relationship
- consultant cannot access suspended tenant
- client cannot access another client's Organisation
- consultant cannot use client access to reach firm billing

### Approval

- authorized consultant approver can finalize consultant-managed work
- unauthorized consultant cannot finalize
- direct customer approval regression remains correct

### Documents / processing

- authorized consultant upload succeeds
- unauthorized consultant upload denied
- authorized consultant manual batch succeeds
- unauthorized consultant manual batch denied

### Organisation management

Test the agreed consultant management capabilities across relevant master-data routes.

### Branding

- branding is tenant/firm scoped
- standard plan cannot activate co-brand/white-label features
- co-brand renders correctly
- white-label renders correctly
- no cross-tenant branding leakage

### Handover

- Organisation ID/data remains stable
- consultant access changes correctly
- direct customer access becomes available according to direct-customer rules
- historical data remains accessible

---

## 15. Required Verification Sequence

Cline implementation is not acceptance.

Required sequence:

```text
1. Cline research/implementation
          ↓
2. Cline mandatory implementation report
          ↓
3. Independent CoStrict verification
          ↓
4. PO acceptance
```

Cline must not declare the feature PO-accepted merely because unit tests pass.

CoStrict should independently verify:

- database/schema correctness
- authorization
- RLS/service-role boundaries
- subscription entitlements
- billing separation
- client access modes
- consultant final approval
- tenant isolation
- UI/UX routes
- branding isolation
- direct customer regression
- handover preservation

---

## 16. Required Cline Deliverable

Create:

```text
Research/CT-CONSULTANT-MODEL-IMPLEMENTATION-01/
    CT-CONSULTANT-MODEL-IMPLEMENTATION-01.md
```

The report must include:

1. exact files changed
2. exact migrations created
3. exact schema changes
4. exact authorization changes
5. exact subscription/entitlement changes
6. exact API changes
7. exact UI/UX changes
8. exact co-branding changes
9. exact white-label changes
10. exact tests added/changed
11. test commands and results
12. known gaps
13. security/RLS assessment
14. direct-customer regression assessment
15. no-production-access declaration
16. git status and starting/ending SHA
17. explicit statement that PO acceptance is still pending independent verification

Cline must provide the **absolute filesystem path** to the final report.

---

## 17. Repository Safety Rules

- Do not reset/clean the repository.
- Preserve all pre-existing working-tree changes.
- Do not overwrite unrelated work.
- Do not commit or push unless separately instructed.
- Do not access production/hosted Supabase/Render.
- Do not create destructive Demo Lab fixtures.
- Prefer existing Demo Lab identities/fixtures where possible.
- Do not weaken RLS as a shortcut.
- Do not add consultant users to `organization_members` as an authorization workaround.
- Do not duplicate the existing Organisation processing pipeline.
- Do not implement unapproved commercial pricing numbers.

---

## 18. Current Known Baseline Findings

The preceding independent CoStrict verification of the consultant organisation-parity implementation found:

- central consultant admission and tenant isolation were substantially working
- consultant role/capability checks were not consistently enforced on Organisation-parity routes
- manual processing remained owner/admin gated
- document upload remained blocked for consultants
- browser E2E was blocked by the local Demo Lab authentication path
- billing separation was partially verified, but consultant-firm billing required additional verification

Those findings are the starting point for this broader product-model refactor.

The earlier Final Approval finding that treated consultant approval as customer-only is superseded by the Product Owner decision in this document.

---

## 19. Non-Goals

This task does not authorize:

- production deployment
- production data changes
- changing carbon-accounting methodology
- changing emissions-factor methodology
- redesigning unrelated customer functionality
- deleting or migrating historical customer data
- inventing pricing tiers or commercial amounts not already approved
- replacing the entire RBAC system if an additive extension is sufficient

---

## 20. Final Product Principle

CarbonTally should not model consultants as customers who merely receive exceptional access to somebody else's Organisation.

It should model:

> **Consultant firms as first-class CarbonTally customers who operate a portfolio of normal CarbonTally Organisations on behalf of their clients, with consultant capabilities, subscription entitlements, optional client access, and optional co-branded/white-label delivery.**

This gives CarbonTally a scalable foundation for:

- consultant-operated services
- collaborative client engagements
- co-branded delivery
- white-label SaaS
- multi-client consultant portfolios
- client handover to direct CarbonTally ownership
- future reseller/partner models

while retaining strict tenant isolation and auditable authorization.

