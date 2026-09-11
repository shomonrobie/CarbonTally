# CarbonTally — Agent Operating Constitution

> This file is the durable project-level instruction set for AI coding, audit,
> QA, architecture, and implementation agents working on CarbonTally.
>
> It is intentionally different from temporary task instructions and audit
> reports.
>
> Current runtime state, current Git state, current database state, and
> verified test results always take precedence over historical memory.

---

# 1. PROJECT IDENTITY

CarbonTally is a commercial emissions-data processing platform.

Its purpose is to transform messy organisational activity/emissions source
data into structured, validated, calculated, traceable emissions data and
ultimately reporting outputs.

CarbonTally is primarily a:

- data-processing platform
- emissions calculation platform
- evidence/provenance platform
- workflow platform
- multi-organisation SaaS
- consultant/client operating platform
- processing-entity operating platform
- internal CarbonTally operations platform

It is NOT merely:

- a file uploader
- a document repository
- a PDF converter
- a generic CRM
- a public chatbot
- a static reporting website

The core business value is the reliable transformation:

SOURCE DATA
→ EXTRACTION
→ MAPPING
→ VALIDATION
→ CALCULATION
→ EVIDENCE
→ REVIEW
→ CUSTOMER APPROVAL
→ REPORTING

All implementation decisions should preserve this purpose.

---

# 2. SOURCE-OF-TRUTH HIERARCHY

When sources disagree, use this hierarchy.

## Current runtime truth

1. Actual running application behaviour
2. Actual database state
3. Actual API/OpenAPI contract
4. Current Git source
5. Current migrations
6. Current automated tests

## Product/design truth

7. Ratified Product Owner decisions
8. Frozen UX/design architecture
9. Current implementation backlog
10. Historical audit reports

## Historical context

11. Hindsight memories
12. Older conversations
13. Older implementation claims

Hindsight is contextual memory, NOT proof of current state.

An agent MUST verify remembered behaviour against the current repository,
database, runtime, and tests before changing code.

---

# 3. HINDSIGHT POLICY

Hindsight is the shared long-term CarbonTally project memory.

Hindsight bank:

    carbontally-full-ui

Hindsight API:

    http://localhost:8888

At the beginning of a substantial task:

1. Recall relevant project context.
2. Identify applicable historical decisions.
3. Inspect the current repository.
4. Inspect current runtime/database state where relevant.
5. Check the latest audit/backlog.
6. Determine whether the remembered issue still exists.

When a durable project fact is discovered:

- architectural decision
- Product Owner decision
- important workflow rule
- important security rule
- durable implementation convention

retain it in Hindsight when appropriate.

Do NOT store:

- temporary debugging output
- secrets
- passwords
- access tokens
- JWTs
- signed URLs
- temporary test data
- speculative conclusions
- unverified claims

Hindsight must never override current verified system state.

---

# 4. GENERAL AGENT BEHAVIOUR

Agents must:

- inspect before changing
- understand existing architecture before adding code
- prefer existing models/services/routes over duplicates
- preserve working functionality
- make the smallest correct architectural change
- test changes
- document important changes
- preserve tenant isolation
- preserve provenance
- preserve auditability
- preserve security boundaries

Agents must NOT:

- invent APIs
- invent database tables
- duplicate existing models
- duplicate business logic
- move business logic into the frontend unnecessarily
- bypass RLS
- bypass authorization
- weaken tenant isolation
- silently alter Product Owner decisions
- silently redesign frozen UX
- reset production
- reset the investor demo database
- delete legitimate demo data
- commit secrets
- force-push
- rewrite Git history

When requirements are unclear, distinguish:

IMPLEMENTATION DECISION

from

PO DECISION REQUIRED

Do not invent business policy.

---

# 5. CARBONTALLY ARCHITECTURE

CarbonTally V3 uses:

Frontend:
React application

Backend:
FastAPI business/domain processing API

Database:
Supabase PostgreSQL

Authentication:
Supabase Auth

Authorization:
Supabase RLS + server-side authorization

Storage:
Supabase Storage

Realtime:
Supabase Realtime

Email:
Resend

The intended production topology includes:

Public frontend:
Vercel

Backend:
Render

Database/Auth/Storage/Realtime:
Supabase

The public website and authenticated application are related but must not be
treated as the same business surface.

---

# 6. FRONTEND / BACKEND RESPONSIBILITY

## Frontend

React/Supabase may directly handle:

- authentication
- session management
- RLS-protected simple reads
- simple CRUD where appropriate
- relationships
- storage interaction
- Realtime
- presentation
- UI state
- navigation

## FastAPI

FastAPI handles business/domain operations such as:

- factor matching
- emissions calculations
- complex validation
- extraction
- OCR
- automatic document processing
- workflow transitions
- report generation
- business authorization
- processing orchestration
- domain-specific operations
- complex cross-table operations
- durable processing jobs

Do not move substantial business logic into the frontend simply to avoid
creating/using an API.

Do not create generic CRUD endpoints in FastAPI when Supabase/RLS is the
appropriate mechanism.

---

# 7. MULTI-TENANT MODEL

CarbonTally is multi-organisation.

An organisation is a customer/client data tenant.

An organisation is NOT the same thing as a Processing Entity.

All organisation-scoped data must remain isolated.

Tenant isolation is enforced by:

- authenticated identity
- organisation membership
- consultant/client relationship
- processing-entity assignment
- API authorization
- Supabase RLS

The UI is NEVER a security boundary.

A hidden button is not authorization.

A disabled button is not authorization.

Every sensitive operation must be protected server-side.

---

# 8. PROCESSING ENTITY MODEL

Processing Entities are first-class V3 entities.

An organisation and Processing Entity are different concepts.

Staff may be:

Internal CarbonTally staff

OR

Processing Entity staff.

The backend must preserve:

- user context
- organisation context
- entity context
- role context
- consultant/client context

Do not bypass RLS to simplify entity-scoped operations.

---

# 9. USER / ROLE MODEL

CarbonTally supports several distinct operating domains.

## CUSTOMER

- Owner
- Admin
- Member
- Viewer

Customer users operate their organisation.

## CONSULTANT

- Consultant
- Consultant team member

Consultants are first-class operators.

Consultants are NOT merely read-only advisers.

## CLIENT

A consultant can have customer/client organisations.

Client owners operate their own organisation.

## PROCESSING ENTITY

- PE Manager
- PE Staff/Operator

Processing Entities perform assigned processing work.

## CARBONTALLY INTERNAL

- Operator
- Reviewer
- QC
- Staff Admin
- System Admin

Roles must have explicit capabilities.

Do not assume that one staff role is equivalent to another.

---

# 10. CONSULTANT OPERATING MODEL — RATIFIED

Consultants can have their own customers.

This is a fundamental CarbonTally requirement.

A consultant may:

- create customers
- manage customers
- manage their customer portfolio
- create/manage consultant team members
- assign team members
- switch active clients
- operate client workspaces
- upload client documents
- process client documents
- perform automatic processing
- perform manual processing
- map data
- validate data
- calculate emissions
- participate in review workflows
- generate/access permitted reports
- communicate with authorised clients

Consultants must NOT be treated as merely a dashboard/portfolio viewer.

Consultant access is limited to customers/organisations they are authorised
to operate.

Cross-consultant client access must be denied.

---

# 11. CONSULTANT / CLIENT RELATIONSHIP

A consultant-client relationship is an explicit relationship.

A client initially belongs to a consultant according to the established
consultant operating model.

A client may later:

- remain with the consultant
- leave the consultant
- become a direct CarbonTally customer
- use another consultant

When a consultant relationship ends:

- the same organisation.id is preserved
- data is preserved
- history is preserved
- provenance is preserved
- consultant access is revoked

Do NOT clone the organisation merely to change consultant ownership.

---

# 12. PROCESSING ENTITY OPERATING MODEL

Processing Entities are operational actors.

PE Managers manage assigned work.

PE Staff/Operators perform permitted processing work.

PE users must be able to see work assigned to their Processing Entity.

PE users must NOT automatically gain unrestricted access to customer data.

In particular, preserve the approved PE source-document boundary.

Where download/view access is restricted, authorization must be enforced
server-side.

PE A must not access PE B's work.

PE users must not gain internal CarbonTally administrative privileges.

---

# 13. INTERNAL CARBONTALLY OPERATIONS

Internal roles have distinct responsibilities.

Typical domains include:

Operator:
processing operations

Reviewer:
review/quality workflow

QC:
quality-control workflow

Staff Admin:
approved staff/user administration

System Admin:
system-level administrative controls

Do not use "admin" as a universal permission shortcut.

System Admin is a distinct approved role.

Where Product Owner decisions require System Admin authority, legacy
authorizers must recognize the role.

---

# 14. USER AND ROLE ADMINISTRATION

Creating users and managing roles are privileged administrative operations.

The system must distinguish:

ordinary operational roles

from

administrative roles.

CarbonTally Reviewers/Operators/QC must not automatically gain user/role
management privileges merely because they can view or process work.

Approved Staff Admin/System Admin capabilities must remain explicit.

Do not broaden permissions merely to make a workflow convenient.

---

# 15. CUSTOMER FACTORS

Factor precedence is:

1. APPROVED CUSTOMER FACTOR
2. CARBONTALLY FACTOR MATCHING
3. UNRESOLVED / MANUAL REVIEW

Approved customer factors must take precedence over generic CarbonTally
factors.

An approved customer factor must not silently be replaced by a generic
factor.

Calculation snapshots must preserve provenance.

Where applicable preserve:

- factor_id
- factor_kind
- customer_factor_id

and the exact factor source used.

---

# 16. CUSTOMER FACTOR APPROVAL — PO DECISION

Product Owner decision:

Customer Owner MAY self-approve a custom factor.

Therefore:

Owner:
allowed to approve own customer factor.

Customer Member:
not allowed unless separately authorized.

Customer Viewer:
not allowed.

Other roles:
follow explicit capability rules.

Do not reintroduce a blanket "no self-approval" rule that contradicts this
ratified decision.

---

# 17. EMISSIONS PROVENANCE

Every calculated emissions result must be traceable.

Preferred chain:

document/source
→ extraction item
→ mapped factor
→ validation
→ calculation
→ calculation snapshot
→ emissions
→ evidence
→ approval/report

Where supported, calculation snapshots must carry source_item_id.

Never produce an emissions number without preserving its provenance.

Do not silently overwrite calculation history.

---

# 18. CORE PROCESSING PIPELINE

The fundamental business pipeline is:

UPLOAD
→ ENQUEUE
→ INGEST
→ EXTRACT
→ MAP
→ VALIDATE
→ CALCULATE
→ EVIDENCE
→ REVIEW
→ CUSTOMER APPROVAL
→ COMPLETED
→ REPORTING

A manual-review branch may occur:

VALIDATE
→ BLOCKED / MANUAL REVIEW
→ HUMAN ACTION
→ RESUME
→ CALCULATE / CONTINUE

The system must persist workflow state.

A UI spinner is not processing.

A frontend animation is not processing.

The database/job state is authoritative.

---

# 19. DURABLE AUTOMATIC PROCESSING

Automatic document processing must be:

- durable
- server-side
- resumable
- idempotent
- observable
- retryable
- failure-aware
- persisted

The processing system should support:

- durable job records
- explicit state machine
- attempt_count
- retry
- failure/dead-letter
- stale-lock recovery
- resume
- persisted progress
- manual-review gates
- deterministic calculation request IDs
- duplicate prevention
- persisted evidence
- notifications

Repeated processing must not create duplicate calculation snapshots.

---

# 20. DOCUMENT TYPES

The platform should support appropriate processing for:

- PDF
- scanned PDF/image
- CSV
- XLSX
- other supported structured inputs

Extraction may use:

- direct parsing
- OCR
- fallback OCR engines

OCR availability must be treated as an environment dependency.

Production deployment must explicitly verify required OCR capabilities.

---

# 21. EXTRACTION

Extraction converts source documents into structured data.

The extracted result must preserve enough context for:

- mapping
- validation
- calculation
- review
- evidence

Extraction failures should result in useful states/errors.

Do not pretend a document was processed merely because it was uploaded.

---

# 22. MAPPING

Mapping connects extracted activity data to emissions factors.

Mapping should support:

- factor search
- unit normalization
- activity matching
- customer-factor precedence
- unresolved/manual review

Mapping must not silently choose an inappropriate factor.

When no factor exists, the UI should explain why.

Avoid dead-end empty dropdowns without explanation.

---

# 23. UNIT NORMALIZATION

Equivalent units should be normalized consistently.

Examples include:

L ↔ litres

t ↔ tonnes

kWh ↔ kWh (Gross CV)

m3 ↔ cubic metres

Do not duplicate unit-alias logic across multiple parts of the application.

Use a central normalization mechanism.

---

# 24. VALIDATION

Validation must identify:

- missing required fields
- incompatible units
- invalid values
- insufficient data
- mapping problems
- business-rule violations

Blocking validation issues must have a lifecycle.

When an issue is resolved through the approved workflow, its state must
reflect that resolution.

The dashboard must not permanently show stale blocking issues.

---

# 25. CALCULATION

Calculation is server-authoritative.

Do not calculate authoritative emissions solely in JavaScript.

The calculation engine must:

- use the selected factor
- use normalized units
- preserve factor provenance
- persist calculation snapshots
- prevent duplicates
- associate the result with its source item
- produce auditable results

---

# 26. REVIEW AND APPROVAL

Review and approval are explicit workflow stages.

The UI must clearly communicate:

- what requires review
- why it requires review
- who can review
- what action is required
- what happens next

Do not allow a workflow to appear "complete" when approval is still required.

---

# 27. REPORTING

Reports must be generated from real persisted emissions data.

Reports must retain traceability to:

- source
- calculation
- evidence
- approval

Never create reports from hard-coded demo strings.

---

# 28. MESSAGING

Messaging is a first-class authenticated application feature.

Authenticated users should use Supabase Realtime-based messaging according to
their authorized relationships.

Messaging boundaries are role/org/client/entity scoped.

Frozen N1 principles:

Customer:
internal/support messaging

Consultant:
internal/support/authorised active-client messaging

CarbonTally:
authorised support/admin messaging

Processing Entity:
operational CarbonTally messaging

There is NO unrestricted Customer ↔ PE communication.

The UI is not the security boundary.

Messaging authorization must be enforced server-side.

---

# 29. PUBLIC CARBONTALLY ASSISTANT

The CarbonTally Assistant is primarily a public visitor-facing feature.

It is not the replacement for authenticated-user messaging.

Authenticated users should receive the appropriate authenticated messaging
experience.

The Assistant must inherit applicable permissions if it is ever exposed in
an authenticated context.

Do not expose visitor-only functionality as a substitute for internal
messaging.

---

# 30. PUBLIC WEBSITE VS APPLICATION

These are distinct product surfaces.

PUBLIC WEBSITE:

    https://carbontally.co.uk

This is the customer-facing public marketing/visitor surface.

It should contain things such as:

- marketing
- information
- public content
- visitor assistance

AUTHENTICATED CUSTOMER APPLICATION:

customer workspace

CONSULTANT WORKSPACE:

consultant operational workspace

PROCESSING ENTITY WORKSPACE:

PE operational workspace

CARBONTALLY INTERNAL:

internal operations workspace

ADMIN CONTROL PLANE:

privileged administration

Do not assume all users should see the same dashboard/navigation.

---

# 31. ADMIN CONTROL PLANE

CarbonTally internal administration should have an appropriate dedicated
control-plane experience.

The public/customer website must not be treated as the internal
administrative interface.

Where the architecture calls for:

    /admin

or an equivalent dedicated administrative surface, preserve that separation.

Administrative UI should expose only the appropriate internal capabilities.

Do not mix customer-facing navigation with privileged system administration.

---

# 32. PE APPLICATION SEPARATION

Processing Entity users have an operational role distinct from customers.

The architecture should preserve a clear PE workspace rather than forcing PE
users through an inappropriate customer-facing experience.

Whether implemented as:

- a dedicated application
- dedicated route/shell
- dedicated frontend package
- dedicated workspace

must follow the current ratified architecture and not be improvised.

The important requirement is clear role-appropriate separation.

---

# 33. ORGANISATION PROFILE

Organisation profile is a first-class feature.

It must support appropriate persistence and management of organisation data.

Do not assume that an organisation is merely:

name + user.

Organisation relationships, facilities, assets, suppliers, documents, users,
consultants, and processing relationships must remain coherent.

---

# 34. MASTER DATA

Master data includes, where applicable:

- Facilities
- Locations
- Assets
- Vehicles
- Suppliers

Facilities/locations/assets must have meaningful relationships.

Do not display raw UUIDs where a human-readable relationship is available.

For example, an asset table should preferably show its facility name rather
than only a facility UUID.

CRUD operations must provide appropriate:

- create
- read
- edit
- validation

behaviour.

---

# 35. LOCATION / FACILITY UX

Locations are first-class operational data.

Creation should have clear validation.

Optional fields must not unexpectedly cause raw database 500 errors.

Expected validation failures should return appropriate 4xx responses.

Do not expose database exceptions directly to users.

---

# 36. TABLE / DATA-GRID STANDARD

Operational tables are expected to scale.

Where a table can grow materially, consider:

- pagination
- page-size selection
- sorting
- filtering
- search
- record counts
- meaningful columns
- contextual organisation/client/entity information

Do not blindly add controls to tiny static tables.

The appropriate controls depend on the table's purpose and expected scale.

Large operational queues must not become unusable walls of rows.

---

# 37. OPERATIONAL TABLE CONTEXT

Operational users must understand what a record belongs to.

A generic row such as:

    Uploads
    open
    25%

is insufficient when multiple organisations/entities/consultants/clients
may be involved.

Where relevant, show:

- organisation
- client
- consultant
- Processing Entity
- batch name
- source
- status
- assigned party

Business context is more important than internal IDs.

---

# 38. WORKSPACE UX

Operational workspaces must prioritize the work being performed.

Avoid:

25-item queue
↓
huge table
↓
Open Workspace
↓
workspace appears far below the queue

For long queues, preferred behaviour is:

QUEUE
→ OPEN WORKSPACE
→ FOCUSED WORKSPACE PAGE/ROUTE
→ BACK TO QUEUE

A dedicated route/page is generally preferable when the inline workspace
would create excessive scrolling.

The principle is universal:

The user should not have to hunt for the active work area.

---

# 39. D19 WORKBENCH

D19 is a frozen UX decision.

The processing workbench is workbench-first.

Preserve:

- top navigation
- approved workbench structure
- approved pane relationships
- source/data context
- validation visibility
- evidence context
- keyboard accessibility
- appropriate responsive behaviour

Do not replace D19 casually.

Any proposed architectural change to D19 requires PO review.

---

# 40. D21 DESIGN SYSTEM

D21 is the unified CarbonTally design system.

New UI should use the established semantic design tokens.

Do not reintroduce legacy styling merely because it is convenient.

Do not create arbitrary one-off visual systems for individual pages.

Maintain consistency across:

- typography
- spacing
- buttons
- forms
- status indicators
- tables
- dialogs
- navigation
- colours
- responsive behaviour

---

# 41. D17 MASTER DATA UX

D17 covers master data including:

- Facilities
- Locations
- Assets
- Vehicles
- Suppliers

Preserve the approved information architecture.

Do not casually merge unrelated master-data concepts.

---

# 42. N3 RETENTION

Retention is configurable.

It must be managed through the appropriate Settings/Admin control plane.

Retention is server-side.

Do not invent retention durations.

Potential retention domains include:

- documents
- extraction data
- evidence
- reports
- messages
- audit logs

Retention must NOT weaken:

- auditability
- evidence
- regulatory traceability
- required history

Configuration must persist and be enforced server-side.

---

# 43. BILLING / SUBSCRIPTION

Billing/subscription is a configurable commercial capability.

The system should allow appropriate administrative configuration rather than
hard-coding commercial rules into the frontend.

Before replacing existing billing/subscription architecture:

1. inspect existing implementation
2. inspect database structures
3. inspect APIs
4. identify existing subscription state
5. preserve useful existing behaviour
6. make configuration available through the approved administrative surface

Do not create a parallel subscription system without first understanding the
existing one.

---

# 44. SECURITY

Security is foundational.

Always enforce:

- authentication
- authorization
- organisation isolation
- consultant/client isolation
- PE isolation
- role boundaries
- storage boundaries
- API boundaries
- RLS

The frontend is NEVER the security boundary.

Every security-sensitive endpoint must enforce authorization independently.

Never rely on:

- hidden buttons
- route hiding
- frontend role checks
- disabled controls

as the sole authorization mechanism.

---

# 45. SECURITY TESTING

Important negative tests include:

Customer A → Customer B

Client A → Client B

Consultant A → Consultant B

Consultant A → Consultant B's client

PE A → PE B

PE → prohibited customer document

Viewer → prohibited write

Member → admin operation

Staff → Staff Admin operation

Staff Admin → System Admin-only operation

Customer → internal operations

PE → internal operations

Every unexpected ALLOW is a serious security finding.

---

# 46. ERROR HANDLING

Users must not receive raw technical errors.

BAD:

    orgs.map is not a function

BAD:

    column reference "id" is ambiguous

BAD:

    duplicate key constraint ...

GOOD:

    Unable to load organisations.
    Please try again.

Technical details should remain available in developer logs/evidence, but not
be the normal user experience.

Expected validation failures should use appropriate status codes.

Do not convert application errors into misleading success states.

---

# 47. LOADING STATES

Never confuse:

loading

with

working.

A spinner does not prove that a process is executing.

Important operations should expose meaningful state such as:

queued

processing

extracting

mapping

validation

calculating

awaiting review

awaiting approval

completed

blocked

failed

retrying

Where appropriate show progress and timestamps.

---

# 48. EMPTY STATES

Every important list should have a meaningful empty state.

Avoid:

blank screen

empty white table

endless spinner

technical exception

The user should understand:

- what is empty
- why it may be empty
- what they can do next

---

# 49. RESPONSIVE DESIGN

Important workspaces must work across:

1920x1080
1440x900
1280x800
1024x768
768x1024
430x932
390x844
375x812

Watch for:

- horizontal overflow
- clipped tables
- broken forms
- inaccessible dialogs
- unusable workspaces
- broken navigation
- unreadable operational information

---

# 50. ACCESSIBILITY

Accessibility is part of product quality.

Important UI must consider:

- keyboard navigation
- focus management
- labels
- semantic headings
- ARIA
- buttons
- forms
- dialogs
- tables
- contrast
- alt text
- responsive behaviour

Use automated accessibility testing where possible.

---

# 51. QA PHILOSOPHY

CarbonTally must not depend on the Product Owner manually clicking every
feature.

Independent automated QA is required.

The QA system should eventually cover:

- database
- schema
- migrations
- RLS
- API
- authentication
- authorization
- workflows
- browser/UI
- UX
- tables
- responsive behaviour
- accessibility
- messaging
- automatic processing
- manual processing
- calculation
- evidence
- reporting
- security boundaries

The QA Harness is an independent verification system.

---

# 52. QA HARNESS

The project is developing:

    qa_harness/

The Harness should eventually provide:

    python qa_harness/scripts/run_all.py

and deterministic mode:

    python qa_harness/scripts/run_all.py --no-ai

AI analysis may be run separately.

The Harness must distinguish:

PASS

FAIL

SKIPPED

BLOCKED

UNVERIFIED

Do not claim acceptance merely because the Harness itself runs.

---

# 53. QA EVIDENCE

Important QA findings should preserve evidence such as:

- role
- organisation
- route
- workflow
- URL
- viewport
- screenshot
- console errors
- network evidence
- API request/response
- database evidence
- Git SHA
- timestamp

Screenshots must show the meaningful application state.

Do not create large numbers of useless screenshots of:

- landing pages
- blank pages
- loading screens
- duplicate screens

Authenticated application workspaces are usually more important than the
public homepage during product QA.

---

# 54. INVESTOR DEMO DATA

The local investor demo environment is intentionally large.

The local identity manifest is:

    tools/seed_investor_demo/DEMO_IDENTITIES.md

It documents approximately:

- 50 direct customer organisations
- 4 customer roles per direct organisation
- 911 consultant-client owner identities
- 50 consultants
- 3 PE managers
- 3 PE staff
- 5 internal staff identities
- legacy/audit identities

Total demo identities:

    1185

All demo identities use the local demo credential mechanism.

Credentials must NEVER be committed.

Agents should use the manifest rather than inventing identity lists.

---

# 55. INVESTOR DEMO SAFETY

The investor demo dataset is valuable test infrastructure.

Never:

- reset it casually
- truncate it
- reseed it unnecessarily
- delete it
- modify it globally
- change credentials globally
- destroy legitimate demo relationships

If mutation testing is required:

1. create isolated QA records
2. label them clearly
3. track everything created
4. clean up only what the test created
5. verify cleanup

If safe cleanup cannot be guaranteed:

    BLOCKED — SAFE MUTATION NOT AVAILABLE

---

# 56. DEMO IDENTITIES AND TEST COVERAGE

Do not test only one "representative user" when a role-specific behaviour
matters.

The identity population is large enough to test:

- multiple organisations
- multiple consultants
- multiple clients
- multiple PE entities
- cross-boundary isolation
- different customer roles

Use representative deep workflows plus deterministic bulk checks.

Do not waste expensive AI calls testing 1,185 users individually when a
deterministic database/API check can establish the same property.

---

# 57. AI AGENT / OPENROUTER POLICY

The project may use an OpenRouter-based agent swarm.

Credential:

    OPENROUTER_AGEN_SWARM_V1_API_KEY

The key must be supplied through environment configuration.

Never hard-code it.

Never print it.

AI agents should primarily analyze deterministic evidence.

They should NOT replace deterministic tests.

Recommended roles:

- UX Analyst
- Workflow Analyst
- Security Analyst
- API Analyst
- Final Judge

Use AI selectively to control cost.

---

# 58. OHD RESPONSIBILITY

OpenHands/OHD is particularly useful for:

- independent acceptance audits
- UI/UX auditing
- persona testing
- workflow discovery
- architecture review
- security negative testing
- finding gaps
- generating implementation-ready findings
- reviewing Cline's work independently

OHD should not automatically fix application issues unless explicitly
instructed.

OHD findings should be evidence-based.

---

# 59. CLINE RESPONSIBILITY

Cline is primarily the implementation agent.

Cline should:

- inspect the current architecture
- inspect relevant audits/backlogs
- recall Hindsight context
- implement approved work
- preserve architecture
- write regression tests
- run relevant tests
- produce implementation reports
- state exactly what changed

Cline must not assume an old audit finding is still current.

Cline must verify.

---

# 60. OHD + CLINE RELATIONSHIP

The preferred development cycle is:

OHD / QA
    ↓
Independent findings
    ↓
Implementation backlog
    ↓
Cline
    ↓
Implementation
    ↓
Tests
    ↓
Git checkpoint
    ↓
Independent QA
    ↓
New findings
    ↓
Cline

Neither agent should be treated as the sole authority.

---

# 61. CURRENT AUDIT / IMPLEMENTATION WORKFLOW

When an OHD audit identifies a defect:

1. Record evidence.
2. Assign severity.
3. Determine whether it is a real current defect.
4. Identify affected role/workflow.
5. Identify root cause if possible.
6. Determine whether a PO decision is required.
7. Create an implementation-ready Cline item.

Cline then:

1. Reads the finding.
2. Verifies the problem.
3. Inspects current implementation.
4. Implements the fix.
5. Adds regression coverage.
6. Runs tests.
7. Reports exactly what changed.

After significant changes:

Independent QA should re-test the affected workflow.

---

# 62. PO DECISION RULE

Do not silently change business policy.

If a behaviour requires product/business choice, mark:

    PO DECISION REQUIRED

Examples:

- who can approve something
- who can create users
- who can manage roles
- retention duration
- communication boundaries
- consultant capabilities
- PE capabilities
- billing rules
- workflow transitions

Existing ratified PO decisions must be respected.

---

# 63. FROZEN UX DECISIONS

The CarbonTally UX baseline includes the frozen D1–D21 decisions.

Important known decisions include:

D17:
Master data architecture

D19:
Processing workbench

D21:
Unified design system

N1:
Authenticated messaging model

N3:
Configurable retention

Do not reopen frozen UX architecture casually.

If implementation conflicts with a frozen decision, identify the conflict
rather than silently changing the decision.

---

# 64. WHITE-LABEL MODEL

White-labeling is presentation/integration over the existing CarbonTally
platform.

Do NOT create:

- separate deployments
- separate databases
- duplicate tenant abstractions

Consultant custom domains may resolve through the existing web platform.

Verified senders may use the existing email provider infrastructure.

Customers/consultants own and manage their own:

- domains
- DNS
- email providers
- mailboxes
- MX/SPF/DKIM/DMARC
- renewals

CarbonTally provides integration/verification, not DNS/email administration.

---

# 65. API CONTRACT

Use the existing API contract.

The live production OpenAPI contract is associated with:

    https://carbontally-api.onrender.com/openapi.json

When working against the current local environment, inspect the locally
running OpenAPI specification where available.

Do NOT invent routes.

Do NOT invent request/response schemas.

Do NOT assume an endpoint exists because it would be convenient.

---

# 66. DATABASE CHANGE POLICY

Before changing the database:

1. inspect current schema
2. inspect existing migrations
3. inspect foreign keys
4. inspect RLS
5. inspect indexes
6. inspect application dependencies
7. determine whether the existing schema already supports the requirement

Avoid duplicate tables/models.

Prefer extending the established V3 model where appropriate.

Every schema change must have a migration.

Do not make ad-hoc production-only database modifications.

---

# 67. RLS POLICY

RLS is a core security layer.

Never disable RLS to make an operation work.

Never bypass RLS simply because FastAPI needs access.

If elevated service-role access is genuinely required, preserve explicit
application-level authorization and document the reason.

Any change to RLS requires careful regression testing of:

- same-tenant access
- cross-tenant denial
- role restrictions
- consultant/client boundaries
- PE boundaries
- internal boundaries

---

# 68. STORAGE POLICY

Documents live in Supabase Storage with database records linking them to
organisations/workflows.

Storage access must respect the same security model as database records.

A signed URL is sensitive.

Never expose signed URLs in logs/reports.

Never assume storage paths themselves are authorization.

Authorization must occur before issuing/accessing a signed URL.

---

# 69. AUTHENTICATION

Supported authentication includes:

- email/password
- Google OAuth

Authenticator-app TOTP MFA is part of the architecture.

Development may allow optional MFA behaviour where configured.

Production enforcement is a separate deployment/policy decision.

Do not weaken authentication to simplify testing.

---

# 70. GIT SAFETY

Before substantial work:

    git status
    git branch
    git rev-parse HEAD

Do not destroy unrelated working-tree changes.

Do not:

- git reset --hard
- git clean -fd
- force-push
- rebase shared history
- amend unrelated commits

unless explicitly instructed.

Do not commit:

- .env files
- credentials
- API keys
- passwords
- JWTs
- local demo credentials
- signed URLs
- generated secrets

---

# 71. IMPLEMENTATION CHANGE DISCIPLINE

Before changing code, identify:

1. existing implementation
2. affected layer
3. dependencies
4. security implications
5. database implications
6. API implications
7. frontend implications
8. regression risk

Prefer the smallest correct change.

Do not rewrite entire modules merely to fix one bug.

Do not replace architecture without justification.

---

# 72. TESTING REQUIREMENT

A meaningful implementation should normally include:

- relevant unit tests
- relevant integration tests
- API tests
- regression tests
- security tests where appropriate
- frontend tests where appropriate

For workflow changes, test the workflow rather than only isolated functions.

For security changes, test both:

ALLOW

and

DENY

cases.

---

# 73. ACCEPTANCE LANGUAGE

Agents must distinguish:

IMPLEMENTED

TESTED

VERIFIED

ACCEPTED

These are not synonyms.

Example:

"Implemented but not independently verified"

is valid.

"Tests pass"

does not necessarily mean:

"Investor accepted."

Never report an acceptance verdict without sufficient evidence.

---

# 74. NO FALSE COMPLETION

Do not declare a task complete because:

- code compiles
- a page loads
- a button exists
- a spinner moves
- one API call succeeds
- a unit test passes

A workflow is complete only when its actual business outcome works.

Example:

Uploading a PDF is NOT document-processing completion.

The real workflow is:

upload
→ extraction
→ mapping
→ validation
→ calculation
→ evidence
→ review
→ approval
→ emissions
→ reporting

---

# 75. BUSINESS-FIRST UI PRINCIPLE

CarbonTally UI should communicate business state rather than implementation
details.

Prefer:

    2,661.55 kg CO₂e

over:

    240 KB

when the user is trying to understand emissions.

Prefer:

    Awaiting customer approval

over:

    status_code=7

Prefer:

    Birmingham Head Office

over:

    21111111-1111-4111-8111-111111111111

Technical details can remain available where useful, but should not dominate
the primary workflow.

---

# 76. UNIVERSAL OPERATIONAL UX PRINCIPLE

Every operational screen should answer:

1. Where am I?
2. What organisation/client/entity am I working on?
3. What needs attention?
4. What can I do?
5. What happened?
6. What happens next?
7. How do I go back?

If users must infer these answers from raw tables, UUIDs, logs, or API states,
the UX needs improvement.

---

# 77. OBSERVABILITY

Important background workflows must be observable.

Automatic processing should expose enough state to understand:

- queued
- started
- current stage
- progress
- blocked reason
- error
- retry count
- completion
- evidence

Logs should be useful to developers without exposing secrets.

---

# 78. LOGGING

Never log:

- passwords
- API keys
- JWTs
- refresh tokens
- signed URLs
- database credentials

Avoid excessive browser console errors.

Expected authorization denials may be recorded as test evidence but should not
be presented as application failures.

---

# 79. LEGACY CODE

CarbonTally V3 contains legacy code/routes/components.

Do not assume legacy code should be deleted merely because a V3 implementation
exists.

Before removing legacy functionality:

1. determine whether it is still referenced
2. determine whether it is still part of the application contract
3. inspect tests
4. inspect routes
5. inspect migrations
6. determine migration/deprecation requirements

Likewise, do not keep legacy behaviour merely because it exists if it
contradicts a ratified V3 architecture.

---

# 80. CURRENT STATE VS HISTORICAL FINDINGS

Previous audits have identified many issues.

Those findings are historical unless independently reverified.

Use previous findings as:

- regression targets
- requirements
- investigation hints

Do not report them as current defects without current evidence.

Latest verified implementation/audit reports take precedence over older
completion claims.

---

# 81. WHEN A TASK IS INTERRUPTED

If an agent/session is interrupted:

1. inspect Git state
2. inspect current files
3. inspect current database state
4. inspect the latest implementation report
5. inspect the latest audit checkpoint
6. inspect Hindsight
7. determine what actually completed
8. continue only from verified state

Never blindly restart an old task.

Never reset the repository merely because the previous session stopped.

---

# 82. AGENT SESSION START PROTOCOL

At the start of a substantial task:

1. Read this AGENTS.md.
2. Recall relevant Hindsight context.
3. Inspect Git state.
4. Inspect relevant source files.
5. Inspect relevant database/schema state.
6. Inspect current audit/backlog.
7. Identify applicable PO decisions.
8. State the intended scope internally.
9. Make changes only within scope.

---

# 83. AGENT SESSION END PROTOCOL

Before reporting completion:

1. Verify changed files.
2. Verify database changes.
3. Verify migrations.
4. Verify tests.
5. Verify Git state.
6. Verify no secrets were introduced.
7. Verify no unrelated changes were absorbed.
8. Produce an implementation/audit report.
9. Record durable architectural decisions in Hindsight where appropriate.
10. Clearly state remaining work.

---

# 84. REPORTING STANDARD

Implementation reports should contain:

- task
- scope
- files changed
- database changes
- migrations
- API changes
- frontend changes
- tests
- runtime verification
- security verification
- Git state
- remaining limitations

Audit reports should contain:

- environment
- Git SHA
- personas
- workflows
- tests
- evidence
- findings
- severity
- reproduction
- impact
- root cause
- acceptance status
- remaining unknowns

---

# 85. FINAL PRINCIPLE

CarbonTally is a real commercial multi-tenant emissions-processing platform.

The goal is NOT:

"make the demo look like it works."

The goal is:

"make the underlying business workflows actually work, securely,
traceably, reliably, and professionally."

Therefore:

REAL DATA over fake data.

REAL PROCESSING over animations.

REAL AUTHORIZATION over hidden buttons.

REAL PROVENANCE over unexplained numbers.

REAL WORKSPACES over navigation confusion.

REAL TESTS over completion claims.

REAL BUSINESS OUTCOMES over implementation details.

REAL EVIDENCE over assumptions.

When in doubt:

INSPECT → VERIFY → IMPLEMENT → TEST → REPORT.

<!-- HINDSIGHT:BEGIN -->
You have persistent long-term memory through the Hindsight MCP server (`recall`, `retain`, and `reflect`) tools.

At the start of each substantial task, call `recall` with the task/request to load
relevant project decisions and context before acting.

Use Hindsight for durable project memory, but never treat it as authoritative
proof of current code, database, runtime, security, or test state.

When you learn a durable architectural decision, Product Owner decision,
workflow rule, convention, or other cross-session fact worth remembering,
call `retain`.

Do not store secrets, credentials, tokens, signed URLs, or temporary debugging
information.

Do not mention memory operations unless the user asks.
<!-- HINDSIGHT:END -->
