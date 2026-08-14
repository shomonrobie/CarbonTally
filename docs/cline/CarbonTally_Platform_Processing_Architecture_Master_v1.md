# CarbonTally Platform & Data Processing Architecture Master Reference
## Business Model, Organizational Boundaries, RBAC, Database, RLS, Storage, Processing, QA and Cline Audit Specification
### Version 1.0 — 8 August 2026
### Status: Architecture discussion concluded — audit/implementation baseline

---

# 1. Purpose

This document is the **current architecture baseline** for CarbonTally.

It consolidates the decisions made during the architecture discussion and is intended to be the primary reference for:

- future conversations
- database redesign
- RBAC redesign
- RLS review
- Supabase Storage review
- backend review
- processing workflow review
- UI/UX redesign
- Cline architecture audit
- future implementation planning

This document describes the **target business and technical architecture**.

It does **not** claim that the current codebase already implements every requirement.

Cline must inspect the actual repository and identify the gap between:

```text
CURRENT IMPLEMENTATION
        +
TARGET ARCHITECTURE
        =
ACTUAL REQUIRED CHANGES
```

The goal is **minimum necessary change**, not a rewrite.

---

# 2. Executive Summary

CarbonTally is a platform owned and operated by:

**CarbonTally (UK) Limited**

Its primary current commercial purpose is:

> **Data processing and carbon-data conversion.**

CarbonTally receives business source data, processes it through automated and human-assisted workflows, maps it to carbon activity categories/emission factors, validates the resulting data, and provides structured output.

CarbonTally may show customers emission trends and aggregated information derived from their processed data.

CarbonTally is **not currently positioned as an audited carbon-reporting or assurance service**.

Human processing is separated from CarbonTally UK operations.

External companies will provide human data-processing services to CarbonTally UK under contract.

The first processing provider is:

**Babui Limited, Bangladesh**

Future providers may be added.

The central architecture is:

```text
                    CARBONTALLY PLATFORM
                           |
                           v
                 CARBONTALLY (UK) LTD
                           |
       +-------------------+-------------------+
       |                   |                   |
       v                   v                   v
   PLATFORM            CUSTOMER          PROCESSING
   OPERATIONS          OPERATIONS          OPERATIONS
       |                   |                   |
       |                   |             Processing Providers
       |                   |                   |
       |                   |        +----------+----------+
       |                   |        |          |          |
       |                   |        v          v          v
       |                   |      Babui    Provider B  Provider C
       |                   |        |
       |                   |     Manager
       |                   |        |
       |                   |   Supervisors
       |                   |        |
       |                   |  Extractors / Validators
       |                   |
       |                   v
       |              Customer Service
       |                   |
       +-------------------+
                           |
                           v
                       CUSTOMER
```

---

# 3. Non-Negotiable Customer Communication Boundary

This is a **hard business and security rule**.

> **Customers can never communicate directly with Data Processing Entities or their employees/workers.**

Customers communicate only with:

**CarbonTally Customer Service**

The communication path is:

```text
CUSTOMER
    |
    | Chat / support request
    v
CARBONTALLY CUSTOMER SERVICE
    |
    | Internal operational request
    v
CARBONTALLY OPERATIONS
    |
    v
DATA PROCESSING PROVIDER
    |
    v
Provider workforce
```

The response path is:

```text
Provider workforce
    |
    v
Provider Manager / CarbonTally Operations
    |
    v
Customer Service
    |
    v
CUSTOMER
```

There must never be a direct customer-to-provider communication channel.

Customers should not receive:

- provider employee contact details
- provider worker names
- provider internal chat
- provider internal notes
- provider queues
- provider internal escalation discussions
- provider workforce information

---

# 4. Current Product Position

CarbonTally's primary role is:

## Data Processing + Conversion

The platform can process:

- messy CSV
- Excel/XLSX
- PDF
- image
- batches of documents
- structured data
- future API submissions

The processing pipeline can include:

```text
Source Data
    |
    v
Ingestion
    |
    +--> Automated Processing
    |
    +--> Human Processing
             |
             v
        Data Extraction
             |
             v
        Validation
             |
             v
        Carbon Mapping
             |
             v
        Factor Matching
             |
             v
        Structured Data
```

Customers can review/validate the resulting data where supported.

Customers can see emission trends on their dashboard based on processed data.

Customers can export their data.

This dashboard functionality is based on the data processed by CarbonTally and is not an audited assurance service.

---

# 5. Existing CarbonTally Technical Context

The project already has significant functionality.

Known current project capabilities include:

- Supabase
- Supabase RLS
- Supabase Storage buckets
- Supabase Realtime/chat capability
- automated CSV/Excel mapping
- document extraction workflows
- customer validation workflows
- batch processing concepts
- carbon factor mapping engine
- multi-source factor architecture
- 7,700+ UK DEFRA factors imported
- API/data delivery concepts
- existing Customer functionality
- existing Consultant functionality
- existing organization/RBAC functionality

The architecture audit must verify the current implementation.

Do not recreate existing features simply because they are described in this document.

---

# 6. Important Scope Decision

The current architecture exercise focuses on:

```text
CARBONTALLY UK
        +
DATA PROCESSING PROVIDERS
        +
PROCESSING WORKFORCE
```

The existing:

- Customer
- Consultant
- Organization
- customer-side RBAC

functionality already exists and should be treated as existing functionality.

It should **not be unnecessarily redesigned** during this provider-architecture exercise.

However, Cline must check whether introducing Data Processing Entities affects existing customer/consultant isolation.

Customer/Consultant redesign is not the goal of this audit.

---

# 7. CarbonTally UK vs Processing Providers

The original architecture treated processing workers as CarbonTally staff.

That is no longer the target architecture.

The correct model is:

```text
CARBONTALLY (UK) LIMITED
        |
        | Owns and operates platform
        |
        +------------------------------+
                                       |
                                       v
                           DATA PROCESSING ENTITY
                                       |
                              +--------+--------+
                              |                 |
                         Provider Manager   Provider Users
                              |
                         Supervisors
                              |
                     Extractors / Validators
```

Babui is therefore:

> **A Data Processing Entity / Processing Provider**

It is not simply a group of CarbonTally employees.

---

# 8. Data Processing Entity

A Data Processing Entity is an external company contracted by CarbonTally UK to perform human data-processing services.

Initial provider:

```text
Babui Limited
Country: Bangladesh
Status: Active
```

Future examples:

```text
Processor B
Processor C
Processor D
```

The database must not hard-code Babui as a special architectural case.

Babui is simply the first processing provider.

---

# 9. Processing Provider Lifecycle

The architecture should be capable of representing provider lifecycle states such as:

```text
PENDING
ONBOARDING
ACTIVE
SUSPENDED
OFFBOARDING
TERMINATED
```

A provider that is suspended or terminated should:

- stop receiving new processing work
- retain appropriate historical records
- allow existing work to be completed or reassigned
- preserve audit history
- not cause historical processing data to be deleted automatically

The exact contractual metadata can be implemented later.

---

# 10. Provider Contract / Commercial Metadata

A future Data Processing Entity may require information such as:

```text
Legal entity
Country
Contract status
Effective date
Termination date
Processing scope
Status
Service level
```

Cline should determine whether the existing schema already has an appropriate place for this information.

Do not create speculative fields simply because they are listed here.

---

# 11. CarbonTally UK Internal Roles

The current CarbonTally UK internal domain should conceptually include:

```text
CEO
CTO
System Administrator
Customer Service
CarbonTally Operations Manager
```

Other specialized roles may be introduced later if necessary.

These are **CarbonTally UK roles**, not provider roles.

---

# 12. CEO

Primary responsibility:

**Business ownership and executive oversight.**

Potential CEO dashboard:

```text
Executive Dashboard
|
+-- Revenue
+-- Customers
+-- Processing volume
+-- SLA performance
+-- Provider performance
+-- Quality trends
+-- Operational backlog
+-- Security overview
+-- Business KPIs
```

CEO is not automatically a technical superuser.

CEO should not automatically have:

- database credentials
- API secrets
- Supabase service keys
- worker passwords
- system secrets

Raw customer-document access should be controlled and auditable.

---

# 13. CTO

Primary responsibility:

**Technology, architecture, infrastructure and security oversight.**

Potential CTO dashboard:

```text
Technology Dashboard
|
+-- Infrastructure
+-- Application health
+-- Database health/metadata
+-- API health
+-- Processing pipeline
+-- Integrations
+-- Deployment status
+-- Security posture
+-- Incidents
+-- Technical audit information
```

CTO is not automatically entitled to unrestricted customer-document access.

If technical investigation requires specific customer data:

```text
Technical issue
    |
    v
Controlled access
    |
    v
Reason recorded
    |
    v
Document inspected
    |
    v
Audit event
```

---

# 14. System Administrator

Primary responsibility:

**Platform administration.**

Responsibilities may include:

- user administration
- role administration
- permissions
- authentication
- platform configuration
- feature flags
- system settings
- processing-provider administration
- platform support

System Administrator is not automatically entitled to unrestricted customer content.

Exceptional customer-data access should be controlled and auditable.

---

# 15. Customer Service

Customer Service is the **sole customer communication layer**.

Responsibilities:

- customer chat
- customer support
- customer requests
- customer-visible processing status
- customer-safe information
- report requests
- escalation to CarbonTally Operations
- customer-facing responses

Customer Service should not have unrestricted access to internal provider operations.

---

# 16. CarbonTally Operations Manager

This role operates on the CarbonTally UK side.

Primary responsibility:

> **Manage contracted processing operations across Data Processing Entities.**

Responsibilities:

- assign processing work to providers
- monitor provider capacity
- monitor provider SLA
- monitor provider quality
- monitor backlog
- provider escalation
- cross-provider workload balancing
- provider-level reporting
- coordinate with Customer Service
- investigate operational issues

The CarbonTally Operations Manager manages **providers**, not individual provider workers.

---

# 17. Provider Operations Manager

Each Data Processing Entity can have its own internal manager.

Example:

```text
Babui Limited
      |
      v
Provider Operations Manager
      |
      +-- Supervisor A
      |
      +-- Supervisor B
      |
      +-- Supervisor C
```

Provider Manager responsibilities:

- manage provider workforce
- distribute work packets
- manage supervisors
- monitor processing
- monitor provider QA
- reassign unfinished work
- manage provider capacity
- manage provider-level performance
- escalate problems to CarbonTally Operations

---

# 18. Two Management Levels

This distinction is critical.

## CarbonTally Operations Manager

```text
CarbonTally Operations Manager
          |
      +---+---+---+
      |       |   |
    Babui   Proc B  Proc C
```

Manages:

- provider allocation
- provider performance
- SLA
- cross-provider capacity
- provider escalation

## Provider Operations Manager

```text
Babui Operations Manager
        |
   +----+----+
   |         |
Supervisor A Supervisor B
   |         |
Workers    Workers
```

Manages:

- workers
- supervisors
- work packets
- provider QA
- provider workload

---

# 19. Provider Hierarchy

Each provider may have:

```text
Data Processing Entity
|
+-- Provider Operations Manager
|
+-- Supervisor
|
+-- Data Extractor
|
+-- Data Validator
|
+-- QA
```

Provider roles are scoped to their provider.

Provider A must not see Provider B.

---

# 20. Data Extractor

The Data Extractor has highly restricted access.

Normal workflow:

```text
MY QUEUE
    |
    v
ASSIGNED WORK ITEM
    |
    v
AUTHORIZED SOURCE DOCUMENT
    |
    v
EXTRACTION FORM
    |
    v
SAVE
    |
    v
SUBMIT
```

Extractor should not have:

- unrestricted customer access
- unrestricted document access
- database credentials
- Supabase service-role credentials
- system administration
- unrelated provider access
- customer administration
- unrelated batch access

---

# 21. Data Validator

Validator sees:

- assigned validation work
- source document
- extracted data
- mapping
- factor
- scope
- validation history

Validator can:

- approve
- correct
- reject
- return to extractor
- flag exceptions

Validator should not automatically have final batch approval authority unless explicitly assigned that permission.

---

# 22. Supervisor

Supervisor manages provider-level processing operations.

Responsibilities:

- assign work
- monitor workers
- reassign unfinished work
- review exceptions
- validation
- QA
- batch approval
- worker performance
- escalation

Supervisor scope must be limited to their authorized processing provider/workspace.

---

# 23. Batch vs Work Item

Core architecture rule:

> **Batch = operational grouping. Work Item / Document = atomic processing and audit unit.**

Example:

```text
Batch #10482
|
+-- Document 001
+-- Document 002
+-- Document 003
...
+-- Document 500
```

A batch must not be permanently owned by one worker.

Each work item must be independently traceable.

---

# 24. Example: 500-Document Batch

Customer uploads:

```text
500 PDFs
```

CarbonTally creates:

```text
Batch #10482
500 work items
```

CarbonTally UK assigns:

```text
Processing Provider:
Babui Limited
```

Babui distributes:

```text
Supervisor A -> 200
Supervisor B -> 150
Supervisor C -> 150
```

Supervisors distribute individual work items to workers.

---

# 25. Worker Failure / Sick Leave

Suppose:

```text
Worker A
Assigned: 100
Completed: 30
Remaining: 70
Status: Unavailable
```

The 30 completed documents remain associated with Worker A.

The 70 remaining documents can be reassigned:

```text
Worker B -> 35
Worker C -> 35
```

The original assignment history must remain.

Do not overwrite historical assignment information.

---

# 26. Assignment History

A reassignment should create additional history.

Example:

```text
Document 031

Assignment 1
Worker: Worker A
Assigned: 08:10
Status: Not started

Assignment 2
Worker: Worker B
Assigned: 14:35
Reason: Worker unavailable
```

Historical attribution must remain.

---

# 27. Partial Work Recovery

If a worker has partially processed a document:

```text
Document 031
Status: IN_PROGRESS
Worker: A
Last saved: 14:21
```

and Worker A becomes unavailable, the system should be able to recover the saved state where supported.

The new worker should not have to recreate valid existing work unnecessarily.

---

# 28. Suggested Work Item States

Potential conceptual states:

```text
NOT_STARTED
ASSIGNED
IN_PROGRESS
SAVED
SUBMITTED
AUTO_VALIDATION
VALIDATION_REQUIRED
RETURNED_FOR_CORRECTION
VALIDATED
QA_SAMPLE
QA_FAILED
APPROVED
REJECTED
REASSIGNED
CANCELLED
```

Cline must compare these concepts against the actual implementation.

Do not automatically create new enums/tables.

---

# 29. Automated Validation

After extraction:

```text
Extraction
    |
    v
Automatic Validation
    |
    +--> Pass
    +--> Low confidence
    +--> Missing data
    +--> Invalid data
    +--> Factor mismatch
    +--> Mapping exception
    +--> Duplicate
```

Automated validation should reduce unnecessary human review.

It must not silently approve records that fail required validation rules.

---

# 30. Human QA

Two important QA dimensions:

## Extraction QA

- supplier
- date
- description
- quantity
- unit
- amount
- source accuracy

## Carbon Mapping QA

- activity/category
- Scope
- emission factor
- factor source
- unit conversion
- calculation
- mapping correctness

Example:

```text
Extraction: PASS
Mapping: FAIL
```

This should enter the appropriate exception process.

---

# 31. QA Sampling

A supervisor does not necessarily need to inspect every document.

Example:

```text
500 documents
|
+-- Exceptions -> 100% review
|
+-- High-confidence -> QA sample
```

Sampling percentages should be configurable.

The example above is illustrative, not a fixed business rule.

---

# 32. Approval Separation

There are three separate concepts.

### Worker submission

> I completed extraction.

### Provider/Supervisor approval

> Processing and QA requirements were satisfied.

### Customer approval

> I accept or reject the processed result.

Workflow:

```text
Worker
  |
  v
Extraction complete
  |
  v
Automatic validation
  |
  v
Provider QA
  |
  v
Supervisor approval
  |
  v
CarbonTally UK
  |
  v
Customer review
  |
  +--> Approve
  |
  +--> Reject / Rework
```

A provider must not approve customer acceptance on behalf of the customer.

---

# 33. Customer-Safe Information

Customers normally see:

- their processing status
- their documents/data
- extracted results
- customer-visible validation information
- dashboard trends
- exports
- customer-visible information
- Customer Service conversations

Customers normally do not see:

- worker names
- worker productivity
- provider staffing
- provider queues
- provider internal notes
- internal QA discussions
- internal escalation notes
- other providers
- other customers
- provider contact information

---

# 34. Customer Service Information Boundary

Customer Service should not be given unrestricted database access just to answer customers.

Preferred flow:

```text
Customer
   |
   v
Customer Service
   |
   | Request filtered information
   v
CarbonTally Operations
   |
   v
Authorized customer-safe result
   |
   v
Customer Service
   |
   v
Customer
```

Customer Service receives only the information needed to answer the customer.

---

# 35. Provider Performance vs Worker Performance

These metrics should be separate.

CarbonTally UK cares about:

```text
Provider
|
+-- SLA
+-- QA
+-- Throughput
+-- Backlog
+-- Turnaround
+-- Exceptions
+-- Capacity
```

Provider Manager cares about:

```text
Worker
|
+-- Workload
+-- Productivity
+-- Correction rate
+-- QA
+-- Availability
```

CarbonTally UK does not need to micromanage every worker.

---

# 36. Provider Capacity

CarbonTally Operations should eventually be able to see:

```text
Babui
Available capacity: 4,000
Current workload:   3,200
SLA risk:           Low
```

and compare providers:

```text
Provider A
Capacity: 4,000
Used: 3,200

Provider B
Capacity: 2,500
Used: 2,450
```

This enables future workload allocation.

---

# 37. Work Allocation Authority

Recommended authority chain:

```text
CarbonTally Operations
        |
        | Assigns batch/provider
        v
Processing Provider
        |
        | Provider Manager
        v
Supervisor
        |
        | Assigns work items
        v
Worker
```

A provider must not take or access a batch belonging to another provider.

---

# 38. Provider Replacement

A strong architecture test is:

```text
Batch #1000
Provider: Babui
```

Babui becomes unavailable.

CarbonTally should be able to:

```text
Batch #1000
      |
      v
Remaining work
      |
      v
Provider B
```

without destroying:

- original assignment history
- completed records
- audit history
- validation history

This is an important acceptance test.

---

# 39. Provider Offboarding

When a provider contract ends:

```text
ACTIVE
  |
  v
SUSPENDED
  |
  v
No new work
  |
  v
Existing work completed/reassigned
  |
  v
OFFBOARDED
```

Historical processing records should remain available to CarbonTally according to applicable retention rules.

Do not automatically cascade-delete historical data.

---

# 40. Provider Worker Offboarding

If a worker leaves a provider:

```text
Worker -> INACTIVE
```

Do not delete the worker record if historical attribution is required.

Historical processing records should retain the identity of the actor.

---

# 41. Provider Isolation

Target:

```text
CarbonTally UK
       |
       +-------------------+
       |                   |
       v                   v
   Babui Ltd          Provider B
       |                   |
   Own users           Own users
   Own queues          Own queues
   Own batches         Own batches
```

Provider A cannot see Provider B.

CarbonTally UK authorized roles may have cross-provider visibility.

---

# 42. Data Minimization for Providers

Provider workers should receive only the information needed to perform processing.

Potentially:

```text
Provider sees:
✓ Assigned document
✓ Required extraction fields
✓ Processing instructions
✓ Necessary source information
```

Provider does not necessarily need:

```text
✗ Customer billing
✗ Customer subscription
✗ Customer internal notes
✗ Customer support history
✗ Other customer documents
✗ Unrelated customer contact details
```

Cline must inspect what the current worker UI actually exposes.

---

# 43. Carbon Factor / Methodology Authority

Provider workers must not freely modify global CarbonTally emission-factor methodology.

Provider workers can perform authorized:

- mapping
- validation
- exception handling

But central factor/methodology changes should remain under CarbonTally-controlled authority.

This prevents one provider from unintentionally changing carbon calculations for other customers/providers.

---

# 44. Provider-Specific Instructions

Providers may eventually require:

- training instructions
- SOPs
- document-processing rules
- QA requirements
- language instructions
- escalation procedures

However:

> Global CarbonTally methodology and factor logic should remain centrally controlled.

---

# 45. Provider-to-CarbonTally Communication

Internal communication should be separate from customer communication.

```text
CARBONTALLY OPERATIONS
        ↕
PROVIDER MANAGER
```

This is not the same channel as:

```text
CUSTOMER
        ↕
CUSTOMER SERVICE
```

Provider internal communications should not accidentally become customer-visible.

---

# 46. Provider Internal Communication

A provider may eventually need:

```text
Provider Manager
       ↕
Supervisor
       ↕
Worker
```

This should be separate from customer chat.

Cline must inspect whether the current Realtime/chat implementation keeps these communication domains isolated.

---

# 47. Supabase Storage

Current storage uses:

**Supabase Storage buckets.**

Cline must inspect the actual implementation, including:

- bucket configuration
- public/private status
- Storage policies
- object paths
- signed URLs
- signed URL lifetime
- direct object access
- provider access
- customer access
- service-role access

Preferred model:

```text
Private storage
      |
      v
Authorized request
      |
      v
Controlled document access
```

The frontend must not be treated as the security boundary.

---

# 48. Controlled Document Processing

Preferred worker workflow:

```text
Private source document
        |
        v
Authorized processing job
        |
        v
Controlled document viewer
        |
        +--------------------+
        |                    |
        v                    v
Source document        Extraction form
        |                    |
        +---------+----------+
                  |
                  v
              Save/Submit
```

The normal workflow should not require workers to download PDFs to personal devices.

Technical controls cannot guarantee prevention of screenshots, photography or screen recording.

Security therefore also relies on:

- contracts
- confidentiality
- training
- least privilege
- audit logs
- monitoring
- controlled access

---

# 49. RLS / Organization and Provider Isolation

The target architecture requires isolation between:

```text
CarbonTally UK
Provider A
Provider B
Provider C
```

Provider users must not access another provider's:

- users
- batches
- documents
- work items
- extraction results
- validation results
- internal notes
- queues
- reports

CarbonTally UK authorized roles can have cross-provider visibility according to role.

RLS must enforce these boundaries at the database layer.

Frontend filtering is insufficient.

---

# 50. Customer / Consultant Isolation

Customer and Consultant functionality already exists.

The current redesign must not unnecessarily disturb it.

Cline must nevertheless verify that adding processing-provider scope does not weaken existing:

- customer organization isolation
- consultant access
- customer RBAC
- RLS
- Storage access

The target architecture is additive where possible.

---

# 51. API Boundary

Future external platforms may submit:

- individual files
- PDF/image batches
- CSV/XLSX batches
- structured data

The API must not bypass:

- authentication
- authorization
- organization scope
- processing provider scope
- audit requirements
- data isolation

The processing pipeline should remain:

```text
External API
    |
    v
CarbonTally
    |
    v
Processing Batch
    |
    v
Processing Provider
    |
    v
Work Items
```

---

# 52. Service-Role / Background Job Risk

Because Supabase is used, Cline must specifically inspect background processing and service-role access.

RLS may protect normal user requests, but backend/service-role operations can bypass RLS.

Trace:

```text
API
 |
 v
Backend
 |
 v
Background Job
 |
 v
Supabase
 |
 v
Service Role?
 |
 v
How is customer/provider scope enforced?
```

Cline must determine whether service-role/background jobs can accidentally bypass:

- customer isolation
- provider isolation
- document isolation
- assignment boundaries

This is a critical audit area.

---

# 53. Audit Trail

Important events should preserve:

- actor
- actor role
- actor organization/provider scope
- resource
- action
- timestamp
- relevant reason/context

Potential events:

- provider assignment
- batch assignment
- work item assignment
- reassignment
- document access
- extraction
- correction
- validation
- QA
- approval
- rejection
- export
- customer approval
- exceptional access
- RBAC changes
- provider changes

A useful conceptual audit record is:

```text
Actor
+
Role
+
Provider/CarbonTally scope
+
Resource
+
Action
+
Timestamp
+
Context/Reason
```

---

# 54. Break-Glass Access

Powerful roles should not receive unlimited invisible access.

Normal access:

```text
Least privilege
```

Exceptional access:

```text
Explicit authorization
       |
       v
Reason
       |
       v
Temporary/controlled access
       |
       v
Audit event
```

This applies especially to:

- CEO
- CTO
- System Administrator
- CarbonTally Operations

---

# 55. Data Versioning / Rework

The architecture should consider:

- customer rejection
- correction
- re-extraction
- factor remapping
- source-document replacement
- AI rerun
- validation rerun

Important history should not be silently overwritten.

Potential conceptual lifecycle:

```text
Version 1 -> Extracted
Version 2 -> Human corrected
Version 3 -> Customer requested correction
Version 4 -> Revalidated
```

Cline must inspect the actual current implementation.

---

# 56. Batch Reliability / Idempotency

Large batch processing must be safe to retry.

Cline must inspect whether retries can duplicate:

- documents
- extraction results
- mappings
- emissions
- notifications
- audit events

Partial completion must be recoverable.

---

# 57. Provider Dashboard

Example:

```text
BABUI LIMITED

Active batches:       18
Documents assigned:  8,420
Completed:           7,890
Validation:            320
Exceptions:             210
SLA at risk:              2

Supervisors:
A     98.7% QA
B     97.9% QA
C     99.1% QA
```

This is a provider dashboard.

It must not expose other providers.

---

# 58. CarbonTally Operations Dashboard

Example:

```text
PROCESSING PROVIDERS

Babui Limited
    Active batches: 18
    SLA: 99.2%
    QA: 98.7%
    Capacity: 82%

Processor B
    Active batches: 7
    SLA: 98.1%
    QA: 97.8%
    Capacity: 91%

Processor C
    Active batches: 4
    SLA: 99.7%
    QA: 99.3%
    Capacity: 63%
```

CarbonTally Operations sees provider-level information.

It does not need to micromanage every worker.

---

# 59. CarbonTally UK Dashboard Separation

Do not create one giant dashboard with every feature hidden by frontend conditions.

Use role/workspace-oriented experiences.

```text
CEO
→ Executive Dashboard

CTO
→ Technology Dashboard

System Admin
→ Administration Dashboard

Customer Service
→ Customer Service Workspace

CarbonTally Operations
→ Provider Operations Dashboard
```

---

# 60. Provider Workspace Separation

```text
Provider Manager
→ Provider Operations Dashboard

Supervisor
→ Supervisor Workspace

Extractor
→ My Queue

Validator
→ Validation Queue

QA
→ QA Workspace
```

These dashboards are presentation layers.

Actual security must be enforced through:

```text
Authentication
+
Authorization
+
Backend
+
RLS
+
Storage policies
```

---

# 61. Role Visibility Matrix — Draft

| Area | CEO | CTO | Sys Admin | CT Operations | Provider Manager | Supervisor | Validator | Extractor | Customer Service |
|---|---|---|---|---|---|---|---|---|---|
| Business KPIs | Full | Overview | No | Overview | No | No | No | No | Limited |
| Platform health | Overview | Full | Operational | Overview | No | No | No | No | No |
| Users | Overview | Oversight | Full | Provider scope | Provider scope | Team scope | No | Own identity | Customer scope |
| RBAC | Oversight | Oversight | Full | No | No | No | No | No | No |
| Providers | Full/Overview | Technical | Admin | Full operational | Own only | Own only | No | No | No |
| Provider users | Overview | Technical | Admin | Operational | Own provider | Own team | Assigned only | Self | No |
| Processing batches | Overview | Technical support | Admin support | Cross-provider | Own provider | Managed scope | Assigned | Assigned | Customer-visible status |
| Work items | Controlled | Controlled | Break-glass | Operational | Own provider | Own scope | Assigned | Assigned | No internal view |
| Raw documents | Controlled | Controlled | Break-glass | Controlled | Operational | Assigned scope | Assigned | Assigned | Customer case only |
| Extraction data | Controlled | Controlled | Break-glass | Operational | Own provider | Own scope | Assigned | Own work | Customer-visible data |
| QA | Overview | Overview | Admin support | Cross-provider | Own provider | Own scope | Execute | No | Customer-visible result |
| Worker assignment | Overview | No | Admin support | Provider oversight | Own provider | Own workers | No | Own work | No |
| Customer chat | Overview | No | Controlled support | Escalation | No direct | No direct | No direct | No direct | Full customer-service scope |
| Internal provider chat | No/overview | Technical if required | Admin support | Cross-provider | Own provider | Own team | Own team | Own team | No |
| Internal notes | Limited | Technical where needed | Controlled | Operational | Own provider | Own scope | Relevant | Own work | No |
| Audit logs | Read | Full technical | Full | Operational | Provider scope | Team scope | Own work | Own work | Support scope |
| Secrets | No | Controlled | Controlled | No | No | No | No | No | No |
| System configuration | No | Technical oversight | Full | No | No | No | No | No | No |

This matrix is a **target draft**. Cline must compare it against the actual implementation.

---

# 62. Important Security Principle

Do not implement authorization as:

```text
if role == CEO:
    allow everything
```

Use:

```text
ROLE
+
ORGANIZATIONAL SCOPE
+
PROCESSING ENTITY
+
RESOURCE SCOPE
+
ACTION
+
CONTEXT
```

Example:

```text
Can User X view Document Y?

1. Is user authenticated?
2. What role?
3. Which CarbonTally/provider scope?
4. Is document within authorized scope?
5. Is role allowed to view documents?
6. Is assignment required?
7. Is this exceptional access?
8. Should action be audited?
```

---

# 63. Data Processing Provider Does Not Equal Tenant

Terminology matters.

Customers/consultants may have tenant-like organizational concepts.

A Data Processing Provider is different:

> It is a contracted service provider to CarbonTally UK.

Preferred terminology:

**Data Processing Entity**

or:

**Processing Provider**

Do not automatically model providers as customer tenants unless the actual architecture requires it.

---

# 64. Database Direction

Conceptually, the architecture may require relationships similar to:

```text
CarbonTally UK
     |
     +-- users
     +-- roles
     +-- permissions
     |
     +-- data_processing_entities
              |
              +-- processing users
              +-- processing batches
              +-- work items
              +-- assignments
              +-- QA
              +-- approvals
```

A processing batch may need a processing-provider relationship.

A work item should be independently assignable.

Assignment history should be preserved.

However:

> **Do not create these tables merely because they are listed here.**

Cline must inspect the current schema and determine whether existing tables already represent the required concepts.

---

# 65. Database Redesign Principle

The preferred approach is:

```text
Current working architecture
        |
        v
Identify actual architectural gaps
        |
        v
Minimum required schema changes
        |
        v
Introduce provider boundary
        |
        v
Preserve existing functionality
```

Do not perform a database rewrite unless evidence demonstrates that it is necessary.

Do not duplicate concepts already represented by existing tables.

---

# 66. Cline Audit Objective

Cline must compare the current CarbonTally repository against this document.

The audit should answer:

> **Can the existing CarbonTally architecture support CarbonTally UK as the platform owner and multiple external Data Processing Entities, while preserving the existing Customer, Consultant and organization functionality?**

And:

> **What is the minimum database/backend/RBAC/RLS/Storage/UI change required?**

---

# 67. Cline Audit Rules

The first audit is **READ-ONLY**.

Do not:

- modify application code
- modify database
- create migrations
- modify RLS
- modify Storage policies
- modify APIs
- modify UI
- install dependencies
- refactor
- rename existing tables
- create speculative tables
- rewrite working functionality

Cline must inspect the actual repository.

Every major conclusion should reference:

- file
- function/class
- route
- table
- column
- policy
- component
- relevant code path

where applicable.

---

# 68. Phase 1 — Repository Discovery

Inspect:

- project structure
- backend
- frontend
- database/migrations
- Supabase configuration
- RLS policies
- Storage
- Realtime
- API routes
- authentication
- authorization
- RBAC
- batch processing
- document processing
- extraction
- validation
- mapping
- audit logging
- notifications
- customer/consultant functionality

Output:

```text
PHASE_1_REPOSITORY_MAP.md
```

---

# 69. Phase 2 — Current Organizational Model

Determine how the current system represents:

- CarbonTally staff
- customers
- consultants
- organizations
- users
- roles
- memberships/access
- processing personnel

Determine whether all processing personnel are currently modeled as CarbonTally staff.

Determine where the new Data Processing Entity boundary would need to be introduced.

Output:

```text
PHASE_2_CURRENT_ORGANIZATIONAL_MODEL.md
```

---

# 70. Phase 3 — Current RBAC Audit

Identify actual roles.

For each role determine:

- role name
- source of truth
- scope
- permissions
- frontend routes
- backend authorization
- RLS
- Storage access
- API access
- Realtime access

Compare against:

CarbonTally UK:

- CEO
- CTO
- System Administrator
- Customer Service
- CarbonTally Operations Manager

Provider:

- Provider Operations Manager
- Supervisor
- Data Extractor
- Data Validator
- QA

Do not require all these roles to already exist.

Classify:

```text
IMPLEMENTED
PARTIAL
MISSING
NOT REQUIRED
UNCLEAR
```

Output:

```text
PHASE_3_RBAC_AUDIT.md
```

---

# 71. Phase 4 — Provider Architecture Gap

Determine whether the current schema can represent:

```text
CarbonTally UK
      |
      +-- Provider A
      +-- Provider B
      +-- Provider C
```

Check whether provider-specific users can be isolated.

Check whether provider-specific batches/work items can be isolated.

Check whether provider lifecycle can be represented.

Determine the minimum schema change required.

Output:

```text
PHASE_4_PROCESSING_PROVIDER_ARCHITECTURE_AUDIT.md
```

---

# 72. Phase 5 — Database Gap Analysis

Inspect actual schema for:

- users
- roles
- permissions
- organizations
- access/membership
- documents
- batches
- processing jobs
- work items
- assignments
- assignment history
- extraction
- validation
- QA
- approvals
- audit events
- chat
- reports
- exports
- API credentials
- provider scope

For each gap classify:

```text
NO GAP
MINOR CODE GAP
MINOR SCHEMA GAP
SIGNIFICANT SCHEMA GAP
ARCHITECTURAL GAP
NOT REQUIRED
```

Output:

```text
PHASE_5_DATABASE_GAP_ANALYSIS.md
```

---

# 73. Phase 6 — RLS / Storage / Realtime Audit

Trace:

```text
User
→ Role
→ Scope
→ Backend
→ RLS
→ Storage
→ Realtime
```

Test conceptually:

### Provider isolation

Provider A cannot see Provider B.

### Provider/customer isolation

Provider cannot see unrelated customer data.

### CarbonTally UK oversight

Authorized UK roles can see required provider-level data.

### Customer communication

Customer cannot access provider chat.

### Storage

Provider cannot retrieve unauthorized customer/provider documents.

### Realtime

Unauthorized subscriptions cannot expose internal messages.

Output:

```text
PHASE_6_RLS_STORAGE_REALTIME_AUDIT.md
```

---

# 74. Phase 7 — Backend / Service Role Audit

Trace:

- API
- background jobs
- worker processes
- service-role usage
- direct database calls
- scheduled jobs
- asynchronous processing

Determine whether service-role/background jobs enforce the correct scope explicitly.

Pay special attention to operations that bypass RLS.

Output:

```text
PHASE_7_BACKEND_AUTHORIZATION_AUDIT.md
```

---

# 75. Phase 8 — Batch / Work Item Audit

Determine whether the current architecture supports:

```text
Batch
 |
 +-- Work Item
 +-- Work Item
 +-- Work Item
```

Check:

- batch
- document
- processing job
- work item
- assignment
- worker ownership
- status
- progress
- submission
- validation
- QA
- approval

Determine whether 500 documents can be safely distributed among multiple workers.

Output:

```text
PHASE_8_BATCH_WORK_ITEM_AUDIT.md
```

---

# 76. Phase 9 — Reassignment / Failure Recovery

Test conceptually:

```text
Worker A
100 assigned
30 completed
70 remaining

Worker unavailable
```

Can the system:

- preserve 30 completed
- identify 70 remaining
- reassign 70
- preserve history
- preserve partial progress
- prevent duplicate work
- prevent conflicting workers
- preserve audit events

Also test:

```text
Provider A unavailable
Remaining batch work
        |
        v
Provider B
```

Output:

```text
PHASE_9_REASSIGNMENT_RECOVERY_AUDIT.md
```

---

# 77. Phase 10 — Validation / QA Audit

Trace:

```text
Extraction
→ Automated validation
→ Exception
→ Human validation
→ QA
→ Supervisor approval
→ Customer review
```

Determine which stages exist.

Check whether the system distinguishes:

- extraction quality
- mapping quality
- factor matching
- Scope classification
- unit conversion
- calculation validation

Output:

```text
PHASE_10_VALIDATION_QA_AUDIT.md
```

---

# 78. Phase 11 — Customer Service Boundary Audit

Determine whether:

```text
Customer
   ↕
Customer Service
```

is isolated from:

```text
Provider
   ↕
Provider Manager
   ↕
Workers
```

Check:

- chat
- Realtime
- messages
- internal notes
- customer-visible notes
- support tickets
- escalations
- report requests

Prove that customers cannot communicate with providers.

Output:

```text
PHASE_11_CUSTOMER_SERVICE_BOUNDARY_AUDIT.md
```

---

# 79. Phase 12 — Audit Trail

Identify existing audit/event infrastructure.

Check whether the system records:

- assignment
- reassignment
- document access
- extraction
- correction
- validation
- QA
- approval
- rejection
- export
- customer approval
- exceptional access
- RBAC changes
- provider changes

Determine whether actor role and provider/CarbonTally scope can be reconstructed.

Output:

```text
PHASE_12_AUDIT_TRAIL_REVIEW.md
```

---

# 80. Phase 13 — Versioning / Rework

Audit handling of:

- customer rejection
- correction
- re-extraction
- factor remapping
- source replacement
- AI rerun
- validation rerun

Identify destructive overwrite risks.

Output:

```text
PHASE_13_VERSIONING_REWORK_AUDIT.md
```

---

# 81. Phase 14 — Batch Reliability / Idempotency

Audit:

- queues
- background workers
- retries
- duplicate prevention
- idempotency
- partial failures
- notification duplication
- extraction duplication
- mapping duplication
- audit-event duplication

Output:

```text
PHASE_14_BATCH_RELIABILITY_AUDIT.md
```

---

# 82. Phase 15 — UI/UX Role Workspace Audit

Inspect actual current UI.

Do not redesign yet.

Determine whether current UI can support:

## CEO

Executive dashboard.

## CTO

Technology dashboard.

## System Admin

Administration dashboard.

## Customer Service

Customer service workspace.

## CarbonTally Operations

Provider operations dashboard.

## Provider Manager

Provider operations dashboard.

## Supervisor

Supervisor workspace.

## Extractor

My Queue.

## Validator

Validation queue.

## QA

QA workspace.

Output:

```text
PHASE_15_UI_UX_ROLE_WORKSPACE_AUDIT.md
```

---

# 83. Phase 16 — Final Architecture Recommendation

Create:

```text
CARBONTALLY_ARCHITECTURE_AUDIT_FINAL.md
```

Include:

## A. Current Architecture

What actually exists.

## B. Target Architecture

What this document requires.

## C. Gap Matrix

| Area | Current | Target | Gap | Severity | Recommendation |
|---|---|---|---|---|---|

## D. Database Changes

Separate:

- Required
- Recommended
- Optional
- Not needed

## E. RBAC Changes

Separate:

- Required
- Recommended
- Optional
- Not needed

## F. RLS Changes

Separate:

- Required
- Recommended
- Optional
- Not needed

## G. Storage Changes

Separate:

- Required
- Recommended
- Optional
- Not needed

## H. Backend Changes

Separate:

- Required
- Recommended
- Optional
- Not needed

## I. UI/UX Changes

Separate:

- Required
- Recommended
- Optional
- Not needed

## J. Migration Risk

Determine whether the architecture can evolve incrementally.

## K. Final Recommendation

Answer explicitly:

1. Can the current database support Data Processing Entities?
2. Can CarbonTally UK have separate roles from provider roles?
3. Can providers be isolated from each other?
4. Can CarbonTally UK oversee multiple providers?
5. Can provider users be scoped correctly?
6. Can customer communication remain CarbonTally-only?
7. Can current Customer/Consultant functionality remain intact?
8. Can RLS enforce provider isolation?
9. Can Supabase Storage enforce document isolation?
10. Can Realtime enforce chat isolation?
11. Can background/service-role jobs enforce the same boundaries?
12. Can batches be assigned to providers?
13. Can work items be assigned/reassigned?
14. Can historical attribution be preserved?
15. Can provider replacement work without destroying history?
16. Does the current UI need changes?
17. What is the minimum database change?
18. Is a major rewrite actually necessary?

---

# 84. Cline Final Verification

Before completing the audit, verify:

```text
CODE MODIFIED: NO
DATABASE MODIFIED: NO
MIGRATIONS CREATED: NO
RLS MODIFIED: NO
STORAGE POLICIES MODIFIED: NO
API MODIFIED: NO
UI MODIFIED: NO
DEPENDENCIES INSTALLED: NO
```

The audit is read-only.

---

# 85. Architecture Acceptance Tests

The final architecture should be considered successful if the audited implementation can demonstrate:

## Test 1 — Provider isolation

```text
Babui user
   X
Provider B data
```

## Test 2 — Provider worker isolation

```text
Babui worker
   X
Babui unrelated customer's work
```

where not assigned/authorized.

## Test 3 — Customer communication isolation

```text
Customer
   X
Babui worker
```

## Test 4 — Customer Service

```text
Customer
   ✓
Customer Service
```

## Test 5 — CarbonTally Operations

```text
CarbonTally Operations
   ✓
Babui
   ✓
Provider B
   ✓
Provider C
```

according to authorization.

## Test 6 — Provider Manager

```text
Babui Manager
   ✓
Babui workers
   X
Provider B
```

## Test 7 — Worker assignment

```text
Worker A
   ✓
Assigned documents
   X
Unassigned unrelated documents
```

## Test 8 — Reassignment

```text
Worker A
100 assigned
30 completed
70 remaining

        ↓

Worker B/C
70 reassigned

History preserved
```

## Test 9 — Provider replacement

```text
Provider A unavailable
        ↓
Provider B receives remaining work
        ↓
History preserved
```

## Test 10 — Factor authority

```text
Provider worker
   X
Unrestricted global factor methodology changes
```

## Test 11 — Service-role isolation

```text
Background job
   X
Accidental cross-provider/customer access
```

## Test 12 — Auditability

For sensitive actions, determine:

```text
Who?
Role?
Scope?
What?
When?
Why/context?
```

---

# 86. Important Architectural Principle

The system should not rely on dashboard visibility to provide security.

This:

```text
Babui Dashboard
```

does not itself isolate Babui.

Actual security must be:

```text
Authentication
     +
Authorization
     +
Backend checks
     +
RLS
     +
Storage policies
     +
Realtime authorization
```

The UI is only the presentation layer.

---

# 87. What We Are NOT Doing Now

Do not use this architecture exercise to:

- redesign existing Customer functionality
- redesign existing Consultant functionality
- redesign existing customer organizations
- redesign customer-side RBAC unnecessarily
- replace Supabase Storage
- replace Supabase
- build new reporting products
- build audited carbon assurance
- create a second customer-facing platform
- create a separate Babui domain
- create provider-facing customer communication
- rewrite the entire database without evidence

---

# 88. Documentation Cleanup

Older architecture documents may now be obsolete because the architecture has changed.

In particular, the following should not remain authoritative:

```text
CarbonTally_Babui_Processing_RBAC_Conclusion_v1.md

CarbonTally — Frontend Discovery, Database-to-UI Mapping & ASCII UX Architecture.md
```

Recommended approach:

```text
docs/
|
+-- architecture/
|      |
|      +-- CarbonTally_Platform_Processing_Architecture_Master_v1.md
|
+-- archive/
       |
       +-- ARCHIVED_CarbonTally_Babui_Processing_RBAC_v1.md
       +-- ARCHIVED_CarbonTally_Frontend_Discovery_v1.md
```

The old documents may be preserved for historical reference, but Cline should not treat them as current architecture.

After the architecture audit, create new authoritative documents based on the actual codebase.

---

# 89. Recommended Documentation Sequence

```text
CURRENT ARCHITECTURE MASTER
          |
          v
READ-ONLY CLINE AUDIT
          |
          v
DATABASE GAP ANALYSIS
          |
          v
MINIMUM DATABASE CHANGES
          |
          v
RBAC SPECIFICATION
          |
          v
RLS / STORAGE SPECIFICATION
          |
          v
UI/UX ROLE WORKSPACE ARCHITECTURE
          |
          v
IMPLEMENTATION
          |
          v
TESTING
```

Do not reverse this sequence.

---

# 90. Final Business Architecture

The target architecture is:

```text
                         CARBONTALLY PLATFORM
                                  |
                                  v
                         CARBONTALLY UK LTD
                                  |
          +-----------------------+------------------------+
          |                       |                        |
          v                       v                        v
       CEO / CTO            CUSTOMER SERVICE          OPERATIONS
       SYS ADMIN                    |                        |
                                   |                        v
                                   |               PROCESSING PROVIDERS
                                   |                        |
                                   |             +----------+----------+
                                   |             |          |          |
                                   |             v          v          v
                                   |           Babui    Provider B  Provider C
                                   |             |
                                   |          Manager
                                   |             |
                                   |        Supervisors
                                   |             |
                                   |      Extractors / Validators
                                   |
                                   v
                              CUSTOMER
```

Communication boundaries:

```text
CUSTOMER
   ↕
CARBONTALLY CUSTOMER SERVICE
```

and:

```text
CARBONTALLY OPERATIONS
   ↕
PROCESSING PROVIDER
```

and:

```text
PROCESSING PROVIDER
   ↕
PROVIDER WORKFORCE
```

There is no direct:

```text
CUSTOMER ↔ PROCESSING PROVIDER
CUSTOMER ↔ WORKER
CUSTOMER ↔ SUPERVISOR
```

---

# 91. Final Architecture Statement

The platform should be designed so that:

> **CarbonTally (UK) Limited owns and operates the platform, controls customer relationships and processing-provider relationships, and remains the central customer-facing entity.**

> **Data Processing Entities provide contracted processing capacity to CarbonTally UK and operate within their own controlled scope.**

> **Customers communicate only with CarbonTally Customer Service.**

> **Customers never communicate directly with Data Processing Entities or their workers.**

> **Data Processing Entities cannot see other Data Processing Entities.**

> **CarbonTally UK authorized roles can oversee contracted processing providers according to role and authorization.**

> **Individual processing workers receive only the minimum access required for their assigned work.**

> **Every processing document/work item remains independently traceable even when work is reassigned.**

> **RLS, Storage policies, backend authorization, API authorization and Realtime authorization must enforce these boundaries.**

> **The database should be modified only where the current architecture cannot safely represent these requirements.**

> **Existing Customer and Consultant functionality should be preserved unless the audit identifies a direct dependency requiring change.**

---

# 92. Final One-Sentence Product Architecture

> **CarbonTally is a UK-owned data-processing platform that receives and converts business data into structured carbon data using automated processing and contracted human-processing providers operating under controlled, isolated workflows, while keeping all customer communication exclusively within CarbonTally.**

---

# 93. Status

**Architecture discussion: CONCLUDED**

**Next step: READ-ONLY Cline architecture audit**

**Implementation changes: NOT YET AUTHORIZED**

**Database redesign: DEPENDS ON AUDIT FINDINGS**

**Customer/Consultant redesign: DEFERRED**

**Supabase Storage: EXISTING — AUDIT CURRENT IMPLEMENTATION**

**Primary architectural change: CarbonTally UK → Data Processing Entity boundary**
