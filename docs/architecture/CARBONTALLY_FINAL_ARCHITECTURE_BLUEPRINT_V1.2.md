# CarbonTally Final Architecture Blueprint v1.2

**Status:** APPROVED — ARCHITECTURE FREEZE  
**Date:** 2 September 2026  
**Product:** CarbonTally  
**Canonical version:** V3
**Blueprint version:** V1.2  
**Purpose:** Single authoritative architecture source of truth for implementation

---

## 1. Executive Architectural Statement

CarbonTally is one coherent multi-actor platform with multiple explicit application/trust surfaces.

The platform uses:

- one canonical V3 backend/domain architecture;
- one primary PostgreSQL/Supabase database;
- one Supabase Auth identity system;
- one shared domain/service layer;
- one D21 UI foundation;
- server-side authorization;
- PostgreSQL RLS as defense in depth;
- explicit application/access contracts for each actor;
- assignment-based Processing Entity access;
- auditable evidence and workflow controls.

The target application surfaces are:

| Surface | Route | Actor | Purpose |
|---|---|---|---|
| Public | `/` | Visitor | Marketing, information, signup |
| Customer | `/app` | Customer | Own organization and emissions work |
| Consultant | `/consultant` | Consultant | Managed client organizations |
| Processing Entity | `/pe` | Third-party PE | Assigned processing work |
| Operations | `/ops` | CarbonTally staff | Internal operational processing |
| Administration | `/admin` | CarbonTally administrators | Privileged platform control plane |

These are separate application/access surfaces over one platform. They are not six independent products or six independent databases.

---

## 2. Architectural Principles

### 2.1 Zero Trust

No implicit trust is granted because of:

- network location;
- IP address;
- geography;
- hostname;
- URL;
- frontend route;
- previous authentication alone.

Authorization is based on:

**Identity + organization/entity + resource + action + policy**

### 2.2 Least Privilege

Every actor receives only the permissions and information required for their function.

### 2.3 Separation of Duties

CarbonTally separates:

- customer activity;
- consultant activity;
- PE processing;
- CarbonTally operational staff;
- CarbonTally administration;
- customer approval.

### 2.4 Defense in Depth

Security is enforced through multiple layers:

```text
Application surface
        ↓
API access contract
        ↓
Authentication
        ↓
Server-side authorization
        ↓
Domain authorization
        ↓
PostgreSQL RLS
        ↓
Database / Storage
```

### 2.5 Frontend Is Never the Security Boundary

Frontend route guards and navigation restrictions improve UX but never establish authorization.

A direct API request must receive the same authorization decision regardless of the frontend route used.

---

## 3. Canonical Application Architecture

```text
                         PUBLIC
                           /
                           │
                    ┌──────▼──────┐
                    │ Supabase    │
                    │ Auth        │
                    │ One Identity│
                    └──────┬──────┘
                           │
       ┌──────────┬────────┼────────┬──────────┬──────────┐
       │          │        │        │          │
       ▼          ▼        ▼        ▼          ▼
    CUSTOMER   CONSULTANT   PE      OPS       ADMIN
      /app    /consultant  /pe     /ops      /admin
       │          │        │        │          │
       └──────────┴────────┼────────┴──────────┘
                           │
                    ┌──────▼──────┐
                    │ V3 API      │
                    │ Access      │
                    │ Contracts   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Domain &    │
                    │ Services    │
                    │ Engines     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Repositories│
                    └──────┬──────┘
                           │
             ┌─────────────▼─────────────┐
             │ PostgreSQL / Supabase     │
             │ RLS / Audit / Storage     │
             └───────────────────────────┘
```

---

## 4. Canonical Technology Architecture

### 4.1 Identity

Supabase Auth is the single identity system.

There are no separate authentication databases for:

- customers;
- consultants;
- PEs;
- CarbonTally staff;
- administrators.

A person has one CarbonTally account.

The account's authorized actor scope is determined by server-side domain relationships.

### 4.2 Backend

FastAPI/V3 is the canonical business-processing backend.

Business logic is shared.

Application surfaces expose different access contracts but do not duplicate business logic.

### 4.3 Database

PostgreSQL/Supabase remains the primary database.

Do not split the platform into separate customer, consultant, PE, operations or admin databases merely to create application separation.

### 4.4 Storage

Customer source documents remain in private storage.

Access is mediated through server-side authorization and short-lived signed URLs.

PE source-document access is browser-based and download-restricted.

---

# 5. Actor Model

## 5.1 Customer

A customer is a CarbonTally customer organization.

Customer users access `/app`.

Customer authorization is organization-scoped.

Customers can access their own authorized:

- organizations;
- locations/facilities;
- assets;
- suppliers;
- documents;
- processing data;
- emissions calculations;
- reports;
- approvals.

Customers cannot access PE-only, internal Operations or CarbonTally Admin functionality.

## 5.2 Consultant

A consultant is a professional organization managing client organizations.

Consultants access `/consultant`.

Consultant access is based on active client relationships/grants.

A consultant relationship can be:

```text
ACTIVE
SUSPENDED
ENDED
```

Ending a relationship revokes access but does not delete:

- organizations;
- customer data;
- provenance;
- history;
- processing records.

Consultants access calculation snapshots through the API, not direct Supabase access.

## 5.3 Processing Entity

A Processing Entity is an independent third-party service-provider company performing CarbonTally-assigned processing work.

A PE is not a customer.

PE staff are not CarbonTally staff.

PE Admin is not CarbonTally Admin.

PE access is entity-scoped and assignment-based.

PE users access `/pe`.

## 5.4 CarbonTally Staff

CarbonTally staff access `/ops`.

Operations is the internal operational workforce surface.

Typical functions include:

- queue management;
- work assignment;
- extraction;
- mapping;
- validation;
- review;
- QC;
- PE management;
- staff operations;
- SLA/workflow management;
- operational messaging;
- operational audit.

## 5.5 CarbonTally Admin

CarbonTally administrators access `/admin`.

Admin is the privileged platform control plane.

It is separate from ordinary Operations.

Typical functions include:

- platform administration;
- privileged configuration;
- system-wide governance;
- high-risk administrative operations;
- commercial configuration;
- platform-level role/permission administration;
- governance/audit controls appropriate to admin authority.

The legacy `admin/` CRA is not the target architecture and must not be revived as the final Admin application.

---

# 6. Processing Entity Architecture

## 6.1 PE Application

The target PE application is:

```text
/pe
```

with a dedicated `PEShell`.

PE pages must not expose customer, consultant, Operations or Admin navigation.

PE functionality is migrated non-destructively from the existing PE branch.

## 6.2 PE API

The target PE API contract is:

```text
/api/v3/pe/*
```

This is a thin access-contract layer.

It delegates to shared V3 domain services and repositories.

It must not create a second business-processing implementation.

Existing entity-scoped backend authorization remains the security foundation.

## 6.3 PE Roles

Processing Entities use dedicated operational roles aligned with the CarbonTally processing workflow:

- **Data Entry Operator**
- **Reviewer**
- **QC Specialist**
- **Admin**

### Data Entry Operator

Performs assigned extraction and mapping work.

### Reviewer

Reviews and approves extracted/mapped work at the PE level.

### QC Specialist

Performs PE-level quality-control activities.

### Admin

Manages PE users and PE-level administration.

PE roles are:

- scoped to the Processing Entity membership;
- separate from CarbonTally internal staff roles;
- not global user roles;
- not interchangeable with Customer, Consultant, CarbonTally Operations, or CarbonTally Admin roles.

Where role responsibilities or names overlap with CarbonTally staff roles, the authorization namespace/trust domain remains separate.

PE approval is **not** equivalent to:

- CarbonTally QC; or
- final customer approval.

A PE role never grants Customer, Consultant, CarbonTally Operations, or CarbonTally Admin privileges.

All permissions remain entity-scoped.

**CarbonTally QC authority:** CarbonTally QC is an internal CarbonTally responsibility and is not a PE capability. A PE QC Specialist may perform PE-level QC on PE-originated work, but PE membership/role never grants authority to perform CarbonTally QC. CarbonTally internal processing staff may perform extraction/processing work, while CarbonTally QC remains a distinct internal quality-control responsibility wherever an independent QC gate is required.

## 6.4 PE Work Assignment

CarbonTally controls assignment.

PEs cannot:

- select arbitrary customer work;
- claim arbitrary documents;
- enumerate customers;
- browse other PEs' work;
- access unassigned work.

A customer may have work processed by multiple processing entities and/or CarbonTally staff.

There is no permanent customer-to-PE exclusivity requirement.

---

# 7. PE Privacy Architecture

PE-visible information must follow data minimization.

PE must never receive:

- customer account administration;
- customer billing;
- unrelated customer data;
- internal CarbonTally audit information;
- other PE data;
- unrestricted customer organization lists;
- customer contact information unless specifically required by an approved processing task.

The target privacy architecture is:

```text
Actual customer identity
        ↓
CarbonTally internal mapping
        ↓
PE-safe alias / pseudonym
        ↓
PE application
```

Where necessary, original source documents should eventually be transformed into sanitized/redacted derivatives before PE access.

This privacy layer is server-side.

Frontend masking is not sufficient.

---

# 8. PE Document Security

PE users must not download or obtain unrestricted source documents.

Required architecture:

```text
Private Storage
      ↓
Authorized API request
      ↓
Server-side entity/work authorization
      ↓
Short-lived signed URL
      ↓
SecureDocumentViewer
```

The viewer must render documents inline without providing a PE download control.

The existing render-scope defect is an implementation blocker and must be fixed before PE acceptance.

---

# 9. Processing Workflow

The canonical processing and quality model supports **two processing origins**: CarbonTally internal processing and external Processing Entity (PE) processing.

### Internal CarbonTally processing path

```text
Extraction
    ↓
Mapping
    ↓
Validation
    ↓
Review
    ↓
CarbonTally QC
    ↓
Customer Approval
```

### External PE processing path

```text
Extraction
    ↓
Mapping
    ↓
Validation
    ↓
PE Review
    ↓
PE QC
    ↓
CarbonTally QC
    ↓
Customer Approval
```

### CarbonTally QC is an independent internal quality gate

CarbonTally may maintain its own internal Data Processing / Extraction department and may perform the same manual extraction and processing work that is assigned to external PEs. PEs are additional controlled processing capacity, not the exclusive source of manual processing.

**CarbonTally QC may verify processed data regardless of its origin.** It may review data processed by:

- CarbonTally internal processing staff;
- any external Processing Entity;
- PE work that has already passed PE Review and PE QC;
- corrected, reassigned, or otherwise reprocessed work where QC is required.

PE QC is an additional PE-level control. It does **not** replace, satisfy, or become equivalent to CarbonTally QC. CarbonTally QC remains a CarbonTally-controlled responsibility and is separate from final Customer Approval.

The processing origin must be preserved as auditable provenance, including which CarbonTally team/member or Processing Entity performed each relevant stage. Processing origin affects which upstream controls apply; it does not change CarbonTally's authority over CarbonTally QC.

CarbonTally retains control of assignment, workflow governance and final customer-facing processing quality.

Customer Owner may self-approve customer factors according to the later ratified product decision.

---

# 10. Automatic Processing

The durable processing pipeline is canonical.

Target:

```text
Upload
  ↓
Durable Job
  ↓
Extraction
  ↓
Mapping
  ↓
Validation
  ↓
Calculation
  ↓
Immutable Snapshot
  ↓
Review / QC
```

AI extraction may assist extraction/classification/mapping, but deterministic server-side calculation remains authoritative.

The AI extraction engine should be integrated into the durable pipeline with a deterministic fallback.

The existing durable pipeline must be completed rather than replaced by a second pipeline.

---

# 11. Evidence and Provenance

CarbonTally is evidence-first.

The target provenance chain is:

```text
Source Document
      ↓
Extracted Value
      ↓
Mapped Activity
      ↓
Emission Factor
      ↓
Calculation
      ↓
Immutable Snapshot
      ↓
Review / QC
      ↓
Approval
```

Every important emissions result should be traceable to the relevant source, factor and calculation history.

---

# 12. Emission Factor Architecture

The existing unified factor architecture remains canonical.

The current critical factor dataset contains:

**7,049 emission factors**

and must not be lost during architectural work.

Architecture migrations, application separation and UI changes must preserve:

- factors;
- reporting years;
- sources;
- factor sets;
- aliases;
- provenance.

No application-surface migration may require destructive factor-table changes.

---

# 13. Authorization Architecture

Authorization must be server-authoritative.

### Customer

```text
identity
+
organization
+
resource
+
action
```

### Consultant

```text
identity
+
consultant firm
+
active client grant
+
resource
+
action
```

### PE

```text
identity
+
processing entity
+
assigned work
+
resource
+
action
```

### Staff

```text
identity
+
internal staff status
+
permission
+
resource
+
action
```

### Admin

```text
identity
+
admin authority
+
resource
+
action
```

No route or URL is itself a permission.

---

# 14. RLS Architecture

RLS remains a critical defense-in-depth mechanism.

The platform continues using:

- organization RLS;
- consultant relationship RLS;
- PE entity RLS;
- server-side authorization helpers;
- explicit resource checks.

FORCE RLS remains a separate security-hardening investigation and is not a prerequisite for architectural freeze.

No security migration may weaken existing tenant/entity isolation.

---

# 15. Application Navigation and Routing

### Public

```text
/
```

### Customer

```text
/app
```

### Consultant

```text
/consultant
```

### PE

```text
/pe
```

### Operations

```text
/ops
```

### Admin

```text
/admin
```

Each surface has:

- its own shell;
- role-aware navigation;
- explicit route guards;
- a defined API contract.

The backend independently enforces authorization.

---

# 16. Operations/Admin Separation

This is a deliberate separation of duties.

```text
/ops
=
CarbonTally operational workforce
```

```text
/admin
=
CarbonTally privileged control plane
```

Operations should not silently become the universal administrator interface.

Admin should not become the ordinary operational workbench.

Shared domain services are acceptable.

Shared UI primitives are required.

Shared privilege is not.

---

# 17. UI/UX Architecture

CarbonTally uses one unified D21 design system.

All applications share the same foundation:

- design tokens;
- typography;
- spacing;
- buttons;
- forms;
- inputs;
- dialogs;
- tables;
- badges;
- navigation primitives;
- responsive rules.

Do not create separate PE, Operations, Customer or Admin design systems.

Do not introduce shadcn/ui solely for popularity.

Existing D21 primitives remain canonical unless a separate architectural decision explicitly changes this.

---

# 18. Workbench UX

The processing workbench uses workflow-first top navigation:

```text
Queue → Extract → Map → Validate → Review → QC → Evidence
```

The workbench is desktop-first.

Primary processing layout:

```text
┌─────────────────────────────────────────────────────────────┐
│ Queue → Extract → Map → Validate → Review → QC → Evidence  │
├───────────────────────────┬─────────────────────────────────┤
│                           │                                 │
│ Source Document           │ Processing Workspace            │
│                           │                                 │
│ PDF / document            │ Extract / map / validate        │
│                           │                                 │
└───────────────────────────┴─────────────────────────────────┘
```

No conventional left sidebar should consume processing workspace unnecessarily.

---

# 19. DataTable Architecture

CarbonTally should progressively converge on one canonical DataTable.

It must support:

- server-side pagination;
- server-side sorting;
- search;
- filtering;
- loading;
- error;
- empty state;
- honest totals;
- page-size selection;
- accessibility;
- responsive table handling.

Migration is incremental.

Do not rewrite all existing tables simultaneously.

---

# 20. Responsive Architecture

100% browser zoom is the acceptance baseline.

Required verification widths:

```text
1920
1440
1280
1024
768
390
```

The application must not rely on 60% browser zoom to become usable.

Shared responsive foundations should address:

- `min-width: 0`;
- `overflow-wrap: anywhere`;
- table scroll wrappers;
- duplicate grid rules;
- form/grid behavior;
- long text;
- narrow viewport navigation.

---

# 21. Billing Architecture

Billing remains provider-neutral.

The commercial core should support:

- plans;
- entitlements;
- credits;
- usage;
- subscription state;
- pricing rules;
- versioning;
- auditability.

Payment-provider integration is a later adapter layer.

Do not embed provider-specific business logic throughout CarbonTally.

---

# 22. Retention Architecture

Retention is configurable and auditable.

Destructive enforcement remains deferred until policy/legal requirements are finalized.

Ending a relationship or changing access must not automatically destroy historical data.

---

# 23. Consultant Messaging and PE Messaging

Customer ↔ PE direct communication is prohibited.

Consultant/customer communication follows the consultant-client access model.

## 23.1 PE Operational Messaging

PE communication is permitted only between:

```text
Processing Entity ↔ CarbonTally Operations
```

PE users may not directly communicate with:

```text
Customer
Other Processing Entity
```

Customer communication remains exclusively through CarbonTally.

PE operational messaging must be:

- controlled;
- auditable;
- entity-scoped;
- work-item and/or issue-scoped;
- restricted to the minimum operational context required.

Messaging must never grant access to unrelated customer data, documents, work items, organizations, or other Processing Entities.

## 23.2 Issue and Conversation Separation

Where implemented, structured operational issues and human conversation should remain conceptually separate:

```text
Issue = operational state, ownership, severity, resolution
Conversation = human communication around the work item/issue
```

A PE user may raise an operational issue or communicate with CarbonTally Operations about assigned work, but this does not grant direct customer access.

The communication boundary is therefore:

```text
PE
 ↓
CarbonTally Operations
 ↓
Customer
 ↓
CarbonTally Operations
 ↓
PE
```

where customer clarification is required.

There is no direct PE ↔ Customer communication channel.
There is no unrestricted PE ↔ PE communication channel.

---

# 24. White-Label Architecture

White-label capability remains a platform capability.

Consultants may eventually use:

- custom domains;
- consultant branding;
- consultant-controlled email infrastructure;
- consultant-branded client experiences.

CarbonTally remains the underlying platform.

Full white-label rendering is future functionality and must not be represented as already complete.

---

# 25. Independent Deployment Architecture

Every application surface should be capable of future independent deployment.

Possible future hostnames include:

```text
carbontally.co.uk
app.carbontally.co.uk
consultant.carbontally.co.uk
pe.carbontally.co.uk
ops.carbontally.co.uk
admin.carbontally.co.uk
```

These hostnames are deployment/access controls.

They are never the security boundary.

A PE may eventually be deployed on separate infrastructure without requiring a domain-model redesign.

---

# 26. Legacy Architecture Policy

Legacy architecture is transitional.

Rules:

1. No new feature should be designed around legacy architecture.
2. Existing legacy routes remain only while required.
3. Dependency inventory determines removal.
4. Replacement functionality must pass acceptance tests before deletion.
5. Legacy removal must be non-destructive.
6. The legacy `admin/` CRA is quarantined and is not the target Admin implementation.
7. Historical documents remain preserved as history but do not override this blueprint.

---

# 27. Migration Safety

Application separation must be non-destructive.

For PE migration:

```text
Existing /ops PE branch
        ↓
New /pe application
        ↓
Temporary redirect/bridge
        ↓
Acceptance verification
        ↓
Remove old PE branch
```

Do not delete:

- users;
- PE entities;
- assignments;
- work items;
- documents;
- extraction data;
- QC records;
- audit history;
- provenance;
- emission factors.

---

# 28. Security Invariants

The following are mandatory:

1. Authorization is identity + organization/entity + resource + action.
2. IP, geography, hostname and route are not authorization boundaries.
3. Frontend code is never a security boundary.
4. PE is never a customer.
5. PE staff are never CarbonTally staff.
6. PE Admin is never CarbonTally Admin.
7. PE cannot enumerate customer organizations.
8. PE cannot access unassigned work.
9. PE cannot access another PE's work.
10. PE cannot download unrestricted source documents.
11. PE cannot communicate directly with customers.
12. CarbonTally controls PE assignment.
13. PE QC is not customer approval.
14. Customer approval remains customer-side authority.
15. One identity system is used.
16. One primary database is used.
17. One shared V3 domain/service layer is used.
18. Different applications use different access contracts, not duplicated business logic.
19. One D21 UI foundation is used.
20. RLS and server-side authorization provide defense in depth.
21. Customer, Consultant, PE, Operations and Admin remain distinct authorization surfaces.
22. All existing critical data must be preserved.
23. Legacy removal is dependency-gated.
24. Future independent deployment must not require domain redesign.
25. PE-visible data must follow data minimization.
26. AI must not silently become the authoritative accounting engine.

---

# 29. Architecture Acceptance Tests

## PE

- PE login lands on `/pe`.
- PE dashboard shows only its own entity.
- PE role navigation is correct.
- PE sees only assigned work.
- PE document viewer renders inline.
- PE has no download control.
- PE extraction/mapping/validation/PE Review/PE QC actions are authorized according to role.
- PE users cannot perform CarbonTally QC.
- CarbonTally QC can receive and verify both PE-originated and CarbonTally-originated processing work.
- Cross-PE access returns 403.
- Cross-customer access returns 403.
- PE → `/ops` is denied.
- PE → `/admin` is denied.
- PE → `/app` is denied.
- Direct unauthorized API requests return 403.
- PE cannot enumerate customer organizations.

## Customer

- Customer reaches `/app`.
- Customer can access only authorized organization data.
- Cross-customer requests return 403.
- Customer cannot use PE/Operations/Admin functions.

## Consultant

- Consultant reaches `/consultant`.
- Active client grants permit authorized access.
- Unauthorized clients return 403.
- Ended relationship removes access.
- Historical data remains.

## Staff

- Staff reaches `/ops`.
- Staff can perform authorized operational work.
- Staff can assign PE work.
- Staff permissions remain explicit.

## Admin

- Admin reaches `/admin`.
- Admin receives only permissions appropriate to admin authority.
- Admin remains separate from ordinary Operations.
- Legacy admin CRA is not the final control plane.

## Responsive

All new PE pages pass at:

- 1920px;
- 1440px;
- 1280px;
- 1024px;
- 768px;
- 390px;

at 100% browser zoom.

---

# 30. Current Known Implementation Gates

Architecture freeze does not mean the product is production-ready.

Known implementation gates include:

### P0

1. Fix document preview render scope.
2. Fix SecureDocumentViewer rendering/sandbox alignment.
3. Fix calculation-engine unit normalization.
4. Ensure methodology values are normalized server-side.
5. Fix shared responsive foundation.

### P1

6. Complete durable automatic AI extraction integration.
7. Complete PE `/pe` application migration.
8. Implement the deliberate PE API contract.
9. Complete DataTable/UI convergence.
10. Complete functional acceptance testing.

### P2

11. Implement V3 Admin control plane.
12. Remove quarantined legacy Admin after dependency verification.
13. Remove legacy routes after dependency verification.
14. Complete PE privacy/pseudonymization layer.
15. Complete production security hardening.

These are implementation tasks, not reasons to redesign the architecture.

---

# 31. Architectural Decisions Explicitly Superseded

Where earlier documents conflict with this blueprint, the following principles apply:

- V3 supersedes RC1/V2 architecture.
- Current ratified PO decisions supersede earlier proposals.
- D21 supersedes pre-D21 static UI mockups.
- The current consultant relationship model supersedes early multi-company proposals.
- Current PE third-party processor architecture supersedes any interpretation of PE as a customer.
- `/ops` is internal Operations.
- `/admin` is the target privileged control plane.
- `/pe` is the target PE application.
- Legacy Admin CRA is not the target architecture.
- Historical D-number collisions must not be used as an authority mechanism; decision names and this blueprint are authoritative.

---


## 31.1 Frozen PE Product Owner Amendments — 2 September 2026

The following decisions were approved after the original v1.0 freeze candidate was reviewed and are incorporated into this v1.2 blueprint.

### PE-ROLE-001

Processing Entities use four dedicated operational roles:

1. Data Entry Operator
2. Reviewer
3. QC Specialist
4. Admin

Roles are scoped to PE membership and are separate from CarbonTally internal staff roles. PE approval is not equivalent to CarbonTally QC or final customer approval. PE roles do not grant privileges in Customer, Consultant, CarbonTally Operations, or CarbonTally Admin domains.

### PE-MSG-001

Processing Entities may communicate with CarbonTally Operations through controlled, auditable, work-item/issue-scoped messaging.

PE users may not directly communicate with customers or other Processing Entities. Customer communication remains exclusively through CarbonTally. Messaging does not grant access to unrelated customer data or work.

# 32. Authority Rule

This document is:

**CARBONTALLY FINAL ARCHITECTURE BLUEPRINT v1.2**

It is the architectural source of truth.

Version 1.2 incorporates the following frozen Product Owner decisions approved on 2 September 2026:

- **PE-ROLE-001:** Processing Entity roles are Data Entry Operator, Reviewer, QC Specialist, and Admin; roles are PE-membership scoped and separate from CarbonTally internal staff roles.
- **PE-MSG-001:** Processing Entities communicate with CarbonTally Operations through controlled, auditable, work-item/issue-scoped messaging; no direct PE ↔ Customer or unrestricted PE ↔ PE communication.

If an older document conflicts with this blueprint:

1. This blueprint wins for architecture.
2. Current ratified Product Owner policy wins for product policy where this blueprint does not explicitly decide.
3. Security invariants cannot be weakened by an older document.
4. Implementation reports describe what exists; they do not override architecture.
5. Historical proposals remain evidence/history only.

Any future architectural change requires an explicit architecture decision and an updated blueprint version.

If an older document conflicts with this blueprint:

1. This blueprint wins for architecture.
2. Current ratified Product Owner policy wins for product policy where this blueprint does not explicitly decide.
3. Security invariants cannot be weakened by an older document.
4. Implementation reports describe what exists; they do not override architecture.
5. Historical proposals remain evidence/history only.

Any future architectural change requires an explicit architecture decision and an updated blueprint version.

---

# 33. What This Blueprint Does Not Decide

The following remain product/commercial/implementation details unless separately approved:

- final payment provider;
- final pricing;
- final credit packages;
- VAT/tax arrangements;
- exact AI provider/cost model;
- final audit-readiness scoring weights;
- exact report-pack composition;
- legal wording of customer-facing claims;
- detailed legal retention policy;
- optional advanced masking scope;
- optional token audience/scope hardening;
- final MFA enforcement configuration;
- individual/personal-user workspace architecture;
- whether an individual user may hold personal emissions data, documents, reports, or subscriptions outside an organization;
- multi-organization and dual-actor workspace precedence where one identity belongs to more than one actor domain;
- the final consultant self-service vs. invitation/provisioning onboarding policy;
- any new authorization surface required for individual users.

These may affect implementation but must not silently change the fundamental architecture.

---

## 31.2 Processing-Origin and CarbonTally QC Amendment — 2 September 2026

This amendment is frozen as part of V1.2.

### CT-QC-001

CarbonTally may perform manual extraction/processing through its own internal Data Processing / Extraction department as well as through external Processing Entities.

### CT-QC-002

CarbonTally QC is an independent CarbonTally-controlled quality gate that may verify processed data from either origin: CarbonTally internal processing or Processing Entity processing.

### CT-QC-003

PE QC remains a distinct PE-level quality-control stage. PE QC does not replace or become equivalent to CarbonTally QC.

### CT-QC-004

The system must preserve processing-origin and stage-level provenance so CarbonTally can identify whether work was processed internally or by a specific PE and which controls have already been completed.

### CT-QC-005

The workflow must support the two canonical paths defined in Section 9 without treating PE processing as mandatory.


---

### 33.1 Individual User Architecture — Design Gate

The next project implementation phase after V1.2 acceptance is **Phase 4 — Individual User Architecture**. This phase is a **design-before-implementation gate**. It is not an authorization to create an individual/personal workspace.

Before any code, migration, route, or UI implementation is introduced for individual users, the implementation agent must:

1. inspect the current identity, actor, workspace, onboarding, membership, subscription, reporting, document, and authorization models;
2. identify what the existing `users.user_type` and related structures already support;
3. identify conflicts or ambiguities involving organization membership, consultant membership, Processing Entity membership, CarbonTally staff identity, and multiple simultaneous identities;
4. produce explicit candidate architectures for individual users;
5. define the security, data-ownership, workspace, billing, reporting, document, and lifecycle implications of each candidate;
6. recommend one architecture only after the alternatives and trade-offs are documented; and
7. stop for Product Owner approval before implementing the selected individual-user architecture.

No individual workspace, personal data store, personal subscription model, or new actor/authorization surface may be introduced merely to make an onboarding screen or existing route function.

Until a separate Product Owner architecture decision is approved, individual-user behavior remains **undecided** and existing organization, consultant, Processing Entity, Operations, and Admin boundaries remain unchanged.

# 34. Final Target State

CarbonTally's final architectural shape is:

```text
                         CARBONTALLY
                              │
                 ┌────────────┴────────────┐
                 │                         │
              IDENTITY                 PUBLIC WEB
           Supabase Auth                   /
                 │
     ┌───────────┼───────────┬───────────┬───────────┐
     │           │           │           │           │
     ▼           ▼           ▼           ▼           ▼
 CUSTOMER    CONSULTANT      PE         OPS        ADMIN
   /app      /consultant     /pe        /ops        /admin
     │           │           │           │           │
     └───────────┴───────────┼───────────┴───────────┘
                             │
                       V3 API Contracts
                             │
                       Authorization
                             │
                       Shared Domain
                             │
                  ┌──────────┴──────────┐
                  │                     │
             Processing             Commercial
             Evidence               Billing
             Workflow               Entitlements
                  │                     │
                  └──────────┬──────────┘
                             │
                     PostgreSQL/Supabase
                             │
                     RLS + Audit + Storage
```

The governing architectural principle is:

> **One platform. One identity. One canonical V3 domain. One primary database. One design system. Multiple explicit trust/access surfaces. Server-authoritative authorization. Least privilege. Separation of duties. Evidence-first processing.**

This is the architecture CarbonTally should implement and stabilize rather than repeatedly redesign.
