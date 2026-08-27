# ============================================================
# CARBONTALLY V3
# CURRENT-STATE ARCHITECTURE & IMPACT ASSESSMENT
# PHASE 1 — READ-ONLY / NO IMPLEMENTATION
# ============================================================

You are performing the official CarbonTally V3 Current-State
Architecture and Impact Assessment.

THIS IS AN ANALYSIS-ONLY TASK.

DO NOT IMPLEMENT V3.

DO NOT MODIFY EXISTING CODE.

DO NOT MODIFY THE DATABASE.

DO NOT CREATE MIGRATIONS.

DO NOT MODIFY RLS.

DO NOT MODIFY STORAGE POLICIES.

DO NOT MODIFY API ROUTES.

DO NOT MODIFY FRONTEND CODE.

DO NOT INSTALL PACKAGES.

DO NOT REFACTOR.

DO NOT RENAME EXISTING MODULES.

DO NOT DELETE ANYTHING.

DO NOT COMMIT OR PUSH CHANGES.

Your ONLY deliverable is:

docs/audit/CarbonTally_V3_Impact_Analysis.md

After creating the report, STOP.

============================================================
1. AUTHORITATIVE SOURCES
============================================================

Inspect and compare ALL available:

1. Current V2.1 database schema
2. Current database migrations
3. Current backend source code
4. Current RLS policies
5. Current Supabase Storage policies/configuration
6. Current API routes
7. Current authentication/RBAC implementation
8. Current frontend implementation where required to understand
   existing behavior
9. CarbonTally_Backend_Module_Inventory_V3.md
10. Existing CarbonTally architecture documentation

IMPORTANT:

The actual database schema, migrations and source code are
authoritative for CURRENT behavior.

CarbonTally_Backend_Module_Inventory_V3.md is an inventory and
analysis aid.

Its heuristic classifications may contain false positives.

VERIFY important findings against actual implementation.

DO NOT invent functionality.

DO NOT assume functionality merely because a table/module name exists.

When behavior cannot be verified, mark it:

UNKNOWN / REQUIRES VERIFICATION

============================================================
2. PRIMARY OBJECTIVE
============================================================

Determine the MINIMUM changes required to evolve the existing
CarbonTally V2.1 system into the agreed V3 architecture.

The central question is:

"Can V3 be implemented incrementally on top of the existing
CarbonTally architecture without a major rewrite?"

Do NOT answer from theory.

Answer from:

- actual schema
- actual migrations
- actual backend
- actual API
- actual RBAC
- actual RLS
- actual Storage policies
- actual frontend behavior where relevant

============================================================
3. CORE CARBONTALLY BUSINESS MODEL
============================================================

CarbonTally is a DATA PROCESSING AND CARBON DATA CONVERSION
PLATFORM.

CarbonTally is NOT currently being designed as an audited
carbon-reporting/assurance platform.

The customer receives processed carbon/emissions data, can review
results/trends through the platform, and can export the resulting
data.

Do NOT introduce:

- audited assurance workflows
- certification workflows
- formal ESG reporting architecture
- audit opinion functionality

unless already present in the current system.

============================================================
4. THREE DISTINCT CONCEPTS
============================================================

CarbonTally has THREE fundamentally different concepts.

------------------------------------------------------------
4.1 EMISSION FACTOR PROVIDERS
------------------------------------------------------------

Examples:

- DEFRA
- SEAI
- EPA
- ADEME
- IPCC
- future factor sources

These provide emission factors.

They are NOT human data-processing companies.

Existing emission-factor provider architecture must remain distinct.

Do NOT merge it with human data processing.

Do NOT call Babui or another human processing company an
"emission-factor provider."

------------------------------------------------------------
4.2 HUMAN DATA PROCESSING ENTITIES
------------------------------------------------------------

Examples:

- Babui Limited
- future subcontracted processing companies

These are HUMAN DATA PROCESSING ENTITIES.

They are subcontractors performing document/data processing work
for CarbonTally.

They are NOT:

- emission-factor providers
- carbon-data providers
- customers
- consultants

Their main responsibility is human extraction/data entry/validation/
operational approval of assigned work.

For example:

PDF
 ↓
Human extractor
 ↓
Structured raw data
 ↓
Entity validation/approval
 ↓
Return to CarbonTally

They do NOT own CarbonTally's carbon intelligence.

They do NOT own CarbonTally's emission-factor database.

They do NOT directly communicate with customers.

------------------------------------------------------------
4.3 CARBONTALLY
------------------------------------------------------------

CarbonTally UK Limited owns/operates the platform and customer
relationship.

CarbonTally owns:

- customer relationship
- carbon processing
- factor matching
- emission-factor usage
- calculation
- calculation lineage
- customer review
- exports
- API/data delivery
- platform management
- cross-entity operational oversight

============================================================
5. EXISTING CARBONTALLY INTERNAL MANUAL PROCESSING
============================================================

IMPORTANT:

CarbonTally ALREADY has its own internal manual data-entry/
document-processing workforce.

Do NOT replace this.

V3 extends the existing model so that human processing can be
performed by:

A. CarbonTally internal staff

AND

B. External Human Data Processing Entities.

This is NOT a new processing engine.

It is an extension of the existing human-processing/assignment
architecture.

============================================================
6. CANONICAL INPUT ARCHITECTURE
============================================================

All data acquisition methods eventually converge into ONE
CarbonTally downstream processing pipeline.

Inputs:

1. Customer CSV/Excel
2. Customer PDF/document → AI extraction
3. Customer PDF/document → human extraction
4. Manual data entry
5. Future API ingestion

Conceptually:

Customer
 |
 +-- CSV/Excel --------------------------+
 |                                       |
 +-- PDF → AI extraction ----------------+
 |                                       |
 +-- PDF → Human extraction -------------+
 |                                       |
 +-- Manual entry -----------------------+
 |                                       |
 +-- API --------------------------------+
                                         |
                                         v
                              Uploaded/Extracted Data
                                         |
                                         v
                                    Validation
                                         |
                                         v
                                   Normalization
                                         |
                                         v
                                  Factor Matching
                                         |
                                         v
                              Emission Factor Database
                                         |
                                         v
                                    Calculation
                                         |
                                         v
                                        CO2e
                                         |
                              +----------+----------+
                              |          |          |
                             CSV       Excel       API
                              |
                              v
                          Dashboard

IMPORTANT:

There must NOT be separate calculation engines for:

- CSV
- AI
- human extraction
- manual entry

All converge into the same CarbonTally downstream processing logic.

============================================================
6A. CANONICAL CARBONTALLY V3 PROCESSING ARCHITECTURE
============================================================

THIS DIAGRAM IS AUTHORITATIVE FOR THE V3 IMPACT ASSESSMENT.

Use this architecture when analyzing the existing database and
backend.

Do NOT interpret AI extraction, human extraction, CSV/Excel,
or manual entry as separate carbon-calculation systems.

                     CUSTOMER
                        │
         ┌──────────────┴──────────────┐
         │                             │
     CSV / Excel                   PDF / Documents
         │                             │
         │                    ┌────────┴────────┐
         │                    │                 │
         │                    ▼                 ▼
         │              AI Extraction     Human Extraction
         │                    │                 │
         │                    │          ┌──────┼──────┐──────┐
         │                    │          ▼      ▼      ▼      ▼
         │                    │       Babui A Babui B Other CarbonTally 
         │                    │          │      │      │      │  
         │                    │          └──────┼──────┘──────┘
         │                    │                 │
         │                    └────────┬────────┘
         │                             │
         └──────────────┬──────────────┘
                        ▼
              EXTRACTED / UPLOADED DATA
                        │
                        ▼
             CARBONTALLY PROCESSING
                     ENGINE
                        │
                        ▼
                   VALIDATION
                        │
                        ▼
                 NORMALIZATION
                        │
                        ▼
                FACTOR MATCHING
                        │
                 ┌──────┴──────┐
                 │             │
                 ▼             ▼
         Customer Factor   CarbonTally
         supplied         Factor Database
                 │             │
                 └──────┬──────┘
                        ▼
                Customer Review
                        │
                   ┌────┴────┐
                   ▼         ▼
                APPROVE    REJECT
                   │         │
                   │         └──► Correction
                   │
                   ▼
                CALCULATION
                   │
                   ▼
                  CO₂e
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
         CSV     Excel     JSON
                   │
                   ▼
              Dashboard/API

Human Extrction Detail:
                    PDF / Documents
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
            AI Extraction       Human Extraction
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
             CarbonTally         Babui A           Other Entity
             Internal Staff
                                     
                    └─────────────────┬─────────────────┘
                                      ▼
                              EXTRACTED RAW DATA
                                      │
                                      ▼
                           CARBONTALLY PROCESSING
                                  ENGINE

IMPORTANT INTERPRETATION:

1. CSV/Excel is uploaded directly by the customer.

2. PDF/document data may be extracted by:
   - AI
   - CarbonTally internal human processors
   - external Human Data Processing Entities

3. "Babui A", "Babui B", and "Other" represent separate
   Human Data Processing Entities or processing allocations.

4. Human Data Processing Entities perform extraction/data-entry/
   validation/operational approval work.

5. Human Data Processing Entities do NOT become emission-factor
   providers.

6. Human Data Processing Entities do NOT own the CarbonTally
   factor database.

7. Human Data Processing Entities do NOT own the CarbonTally
   calculation engine.

8. ALL resulting raw activity data converges into the same
   CarbonTally Processing Engine.

9. CarbonTally performs the downstream:
   - validation
   - normalization
   - factor matching
   - calculation

10. A customer may supply an emission factor.

11. CarbonTally may have a corresponding factor in its own
    emission-factor database.

12. The current implementation MUST be inspected to determine
    whether customer-supplied factors are currently:
    - validated
    - compared
    - automatically accepted
    - replaced
    - ignored
    - presented for customer review

13. DO NOT assume the current system validates customer-selected
    factors.

14. Customer approval/rejection is a separate business step from
    human extraction/entity approval.

15. Customer communication remains with CarbonTally.

16. Customers do NOT communicate directly with Babui or any other
    Human Data Processing Entity.

17. Final outputs may include:
    - CSV
    - Excel
    - JSON/API
    - CarbonTally dashboard data

18. This diagram describes the TARGET V3 ARCHITECTURE.

The purpose of this audit is to determine how closely the CURRENT
V2.1 implementation already matches this architecture and the
MINIMUM changes required to reach it.

DO NOT redesign the architecture.

DO NOT create duplicate processing engines.

DO NOT implement changes during this phase.
============================================================
6B. V3 OPERATIONAL CONTROL LAYER
============================================================

The V3 architecture is NOT limited to document extraction and
carbon calculation.

CarbonTally must also operate as a controlled multi-entity
processing management platform.

The audit MUST explicitly cover:

                    CARBONTALLY CONTROL PLANE
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
     CONFIGURATION       ISSUE MANAGEMENT      RBAC/POLICY
          │                   │                   │
          ▼                   ▼                   ▼
    WORKFLOW RULES       ESCALATION           ACCESS CONTROL
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                     PROCESSING OPERATIONS
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
     ASSIGNMENT             QC/QA              SLA/KPI
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                         AUDIT TRAIL


SYSTEM CONFIGURATION MUST BE AUDITED FOR:

- system-wide settings
- workflow settings
- auto-assignment
- reassignment
- capacity
- SLA
- escalation
- QC sampling
- validation rules
- notification rules
- feature flags
- processing limits
- upload limits
- AI thresholds
- factor-matching thresholds
- security settings

Configuration must have an appropriate hierarchy:

SYSTEM
  ↓
CARBONTALLY
  ↓
DATA PROCESSING ENTITY
  ↓
SUPERVISOR / TEAM
  ↓
WORKER

Lower-level settings must never override higher-level security,
data-isolation, mandatory SLA, QC, or platform policies.

The audit MUST determine:

- where each configuration currently lives
- whether it is hard-coded or configurable
- its scope
- who can change it
- whether changes are audited
- whether existing configuration infrastructure can be extended
- whether a new configuration structure is actually necessary


ISSUE MANAGEMENT MUST BE AUDITED AS A FIRST-CLASS V3 DOMAIN.

Issues may originate at:

- worker level
- validator level
- supervisor level
- entity manager level
- CarbonTally operations
- customer service
- CarbonTally administration
- security/technical operations

Issues must support controlled escalation.

Example:

WORKER
  ↓
SUPERVISOR
  ↓
ENTITY MANAGER
  ↓
CARBONTALLY OPERATIONS
  ↓
CARBONTALLY ADMIN / MANAGEMENT

However, escalation must be ISSUE-TYPE dependent.

For example:

Data quality issue
    → Supervisor

Processing capacity issue
    → Entity Manager

Customer clarification
    → CarbonTally Customer Service

Contract/SLA problem
    → CarbonTally Operations

Platform problem
    → Technical/Operations

Security incident
    → Security/Admin

The audit MUST determine whether existing issue, task,
communication, notification, workflow, or escalation structures
can support this.

DO NOT create a new issue-management system if an existing system
can be extended.

DO NOT create a new configuration system if an existing system
can be extended.


============================================================
7. CUSTOMER MANUAL DATA ENTRY
============================================================

CarbonTally already supports manual data entry.

Customers may be able to select an emission factor from a
CarbonTally dropdown.

THIS MUST BE AUDITED, NOT ASSUMED.

Trace the actual implementation:

Frontend
 ↓
API
 ↓
Backend
 ↓
Database
 ↓
Calculation
 ↓
Audit/lineage

Determine exactly:

1. Can customers select factors?
2. Where do dropdown factors come from?
3. Does CarbonTally validate the selected factor?
4. Is the selected factor stored?
5. Is factor source stored?
6. Is factor version/year stored?
7. Is the selection automatically accepted?
8. Does CarbonTally replace it?
9. Is there discrepancy checking?
10. Is there an audit trail?
11. Can the customer change it?
12. Does changing it trigger recalculation?

DO NOT change behavior.

Report CURRENT behavior exactly.

============================================================
8. CUSTOMER CSV / EXCEL
============================================================

Customers may upload CSV/Excel.

The file may contain:

- activity data
- quantity
- unit
- date
- supplier
- emission factor
- other carbon-related fields

Determine exactly what happens when an emission factor is supplied
by the customer.

Determine whether CarbonTally:

- accepts it
- validates it
- compares it
- maps it
- replaces it
- ignores it
- requests customer review

Do not guess.

============================================================
9. AI EXTRACTION
============================================================

AI-extracted data enters the same downstream processing system.

PDF
 ↓
AI extraction
 ↓
Structured raw data
 ↓
CarbonTally processing

Do NOT create a separate AI calculation system.

============================================================
10. HUMAN EXTRACTION
============================================================

Human-extracted data also enters the same downstream processing
system.

PDF
 ↓
Human extraction
 ↓
Entity validation/approval
 ↓
Structured raw data
 ↓
CarbonTally processing
 ↓
Validation
 ↓
Factor Matching
 ↓
Calculation
 ↓
CO2e

============================================================
11. 500-DOCUMENT MULTI-ENTITY EXAMPLE
============================================================

The system must conceptually support:

Customer uploads:

500 documents

CarbonTally may allocate:

100 → CarbonTally internal staff
100 → Entity A
100 → Entity B
100 → Entity C
100 → Entity D

OR any other distribution.

Allocation must be capable of operating at the appropriate
document/job level.

Determine whether current architecture supports:

- batch assignment
- document assignment
- entity assignment
- worker assignment
- reassignment

Do not implement.

============================================================
12. TWO OPERATIONAL SYSTEMS WITHIN ONE PLATFORM
============================================================

This is a critical V3 requirement.

CARBONTALLY has its own operational management.

Each external Human Data Processing Entity has its own operational
management.

Example:

CARBONTALLY
 |
 +-- Internal processing
 |
 +-- Entity A
 |     +-- Manager
 |     +-- Supervisors
 |     +-- Workers
 |     +-- Validators
 |
 +-- Entity B
 |     +-- Manager
 |     +-- Supervisors
 |     +-- Workers
 |     +-- Validators
 |
 +-- Entity C
       +-- Manager
       +-- Supervisors
       +-- Workers
       +-- Validators

Each external entity should have its own:

- workforce
- assignments
- workload
- validation
- approval
- operational dashboard
- issue management
- internal escalation

CarbonTally must have:

- cross-entity visibility
- workload visibility
- performance visibility
- SLA/KPI visibility
- quality visibility
- assignment visibility
- issue escalation
- entity lifecycle management

External entities must NOT see each other's data.

============================================================
13. HUMAN PROCESSING ENTITY ROLES
============================================================

Determine how current RBAC can support:

External Entity:

- Manager
- Supervisor
- Worker/Extractor
- Validator/QC

CarbonTally:

- internal processing staff
- customer service
- operations
- management
- administrator
- technical/security roles where applicable

Customers and consultants already exist.

Do NOT redesign consultant architecture unless required by V3.

Do NOT duplicate the existing staff/RBAC system if it can be extended.

============================================================
14. ENTITY RESPONSIBILITY
============================================================

Human Data Processing Entities may:

- receive assigned documents
- assign internal work
- perform extraction
- perform manual data entry
- validate extracted data
- perform QC
- approve completed processing
- manage their own workload
- manage their own staff
- raise internal issues
- communicate internally with CarbonTally through controlled channels

They must NOT:

- access unrelated customer data
- access other processing entities
- change CarbonTally factor-provider infrastructure
- change CarbonTally calculation logic
- directly contact customers
- access CarbonTally administration unless explicitly authorized

============================================================
15. WORKER FAILURE / REASSIGNMENT
============================================================

Example:

Worker A receives:

100 documents

Worker A completes:

30

Worker A becomes unavailable.

Remaining:

70

The system should eventually support:

70
 ↓
reassignment
 ↓
another authorized worker/entity

The 30 completed documents must retain historical attribution.

Audit whether existing:

- assignment
- workload
- queue
- review
- history
- audit

already support this.

============================================================
16. VALIDATION AND APPROVAL LAYERS
============================================================

Distinguish:

1. Human extraction
2. Entity validation
3. Entity approval
4. CarbonTally processing/validation
5. Customer review/approval where applicable

Do NOT assume these are the same approval.

Determine which layers already exist.

============================================================
17. CUSTOMER COMMUNICATION
============================================================

THIS IS A HARD BUSINESS RULE.

Customers NEVER directly communicate with:

- Babui workers
- Babui supervisors
- Babui managers
- other processing entity workers
- other processing entity supervisors
- other processing entity managers

The communication architecture is:

CUSTOMER
   ↓
CARBONTALLY CUSTOMER SERVICE
   ↓
CARBONTALLY INTERNAL OPERATIONS
   ↓
RELEVANT DATA PROCESSING ENTITY
   ↓
ENTITY MANAGER / SUPERVISOR
   ↓
WORKER / VALIDATOR

Reverse path:

WORKER / VALIDATOR
   ↓
ENTITY SUPERVISOR / MANAGER
   ↓
CARBONTALLY INTERNAL OPERATIONS
   ↓
CARBONTALLY CUSTOMER SERVICE
   ↓
CUSTOMER

The customer should normally see only CarbonTally-facing communication.

Customers should NOT automatically see:

- worker identity
- contractor identity
- contractor workload
- contractor KPI
- contractor SLA
- contractor warnings
- contractor remediation
- contractor internal notes
- internal assignment details

Inspect the existing communication/realtime implementation.

============================================================
18. ISSUE MANAGEMENT
============================================================

V3 must include a hierarchical Issue Management capability.

Potential flow:

Worker
 ↓
Supervisor
 ↓
Entity Manager
 ↓
CarbonTally Operations
 ↓
CarbonTally Admin/Management

But escalation may vary by issue type.

Examples:

Data quality issue
 → Supervisor

Document inaccessible
 → Supervisor → Manager

Customer clarification
 → Entity Manager → CarbonTally Customer Service

Platform issue
 → CarbonTally Technical/Operations

Security incident
 → CarbonTally Security/Admin

Audit whether existing issue/task/communication systems already
support this.

Potential issue attributes:

- issue ID
- issue type
- severity
- priority
- status
- owner
- assignee
- customer context
- entity context
- batch/document context
- SLA
- escalation level
- notes
- resolution
- reopening
- audit history

Do not create all of these automatically.

Determine what already exists.

============================================================
19. SYSTEM CONFIGURATION
============================================================

Audit existing configuration architecture.

Potential system-wide configuration includes:

- auto-assignment
- assignment strategy
- reassignment rules
- SLA
- escalation thresholds
- QC sampling
- validation thresholds
- worker capacity
- entity capacity
- notification rules
- processing limits
- upload limits
- supported file types
- AI extraction thresholds
- factor matching thresholds
- retry behavior
- feature flags
- security settings
- session settings
- audit settings

Do NOT create a giant settings system merely because these concepts
exist.

First determine what already exists.

============================================================
20. CONFIGURATION HIERARCHY
============================================================

Audit whether configuration can conceptually operate at:

SYSTEM
 ↓
CARBONTALLY
 ↓
DATA PROCESSING ENTITY
 ↓
SUPERVISOR/TEAM
 ↓
WORKER

Lower-level settings MUST NOT override:

- security
- data isolation
- system policies
- mandatory SLA
- mandatory QC
- compliance controls

Determine which settings are:

- system-wide
- entity-specific
- operational
- user-specific

============================================================
21. AUTO-ASSIGNMENT
============================================================

Audit whether the existing system supports or can support:

- manual assignment
- round robin
- least loaded
- capacity-based
- skill-based
- priority-based
- SLA-aware
- hybrid assignment

Do not implement.

Determine the smallest change required.

============================================================
22. QUALITY CONTROL
============================================================

Audit:

- worker validation
- supervisor review
- QC
- sampling
- correction
- rejection
- rework
- escalation

Potential metrics:

- extraction accuracy
- correction rate
- QC failure rate
- validation pass rate
- turnaround time

Do not assume all are currently available.

============================================================
23. SLA / KPI / PERFORMANCE
============================================================

CarbonTally must eventually be able to monitor external entities.

Potential metrics:

- volume completed
- turnaround time
- backlog
- error rate
- correction rate
- QC failure
- SLA compliance
- capacity
- reassignment
- availability

Entity lifecycle may include:

ONBOARDING
 ↓
ACTIVE
 ↓
WARNING
 ↓
REMEDIATION
 ↓
SUSPENDED
 ↓
ACTIVE

or:

SUSPENDED
 ↓
TERMINATED

Audit existing structures first.

============================================================
24. ENTITY OFFBOARDING
============================================================

A processing entity contract may be terminated.

Audit whether the system can eventually support:

Stop new assignments
 ↓
Freeze access
 ↓
Identify incomplete work
 ↓
Reassign outstanding work
 ↓
Complete/close work
 ↓
Revoke staff access
 ↓
Preserve history
 ↓
Complete data/contract offboarding

Do not implement.

============================================================
25. DATA LINEAGE / PROVENANCE
============================================================

Audit whether CarbonTally can trace:

Original document
 ↓
Extraction method
 ↓
Extracted value
 ↓
Validation
 ↓
Factor selected
 ↓
Factor source
 ↓
Factor version/year
 ↓
Calculation
 ↓
CO2e result

Potential acquisition methods:

- CSV_UPLOAD
- EXCEL_UPLOAD
- AI_EXTRACTION
- HUMAN_EXTRACTION
- MANUAL_ENTRY
- API

Do NOT automatically add fields.

Determine whether existing structures already provide lineage.

============================================================
26. VERSIONING / REPROCESSING
============================================================

Audit what happens when:

- customer corrects data
- document is reprocessed
- extraction is corrected
- factor changes
- customer changes selected factor
- recalculation occurs

Determine whether historical results can be preserved.

Do not implement.

============================================================
27. DATA RETENTION / DELETION
============================================================

Audit:

- customer cancellation
- document retention
- extracted data retention
- calculated data retention
- Storage deletion
- account closure
- export before deletion
- derived-data deletion
- backup implications

Do NOT invent legal retention periods.

Clearly separate:

CURRENT IMPLEMENTATION
from
BUSINESS POLICY DECISION REQUIRED.

============================================================
28. SECURITY / DATA ISOLATION
============================================================

Audit isolation at:

1. Customer organization
2. Consultant
3. CarbonTally internal staff
4. Human Data Processing Entity
5. Entity staff
6. Worker assignment
7. Document
8. Storage object
9. API
10. Realtime communication

Specifically determine whether:

Customer A
   X
Customer B

Entity A
   X
Entity B

Worker A
   X
Unassigned document

External Entity
   X
CarbonTally administration

Customer
   X
External worker

are enforced through:

- Supabase RLS
- Storage policies
- backend authorization
- RBAC
- API authorization
- signed URLs
- Realtime authorization

DO NOT modify anything.

============================================================
29. SECURITY INCIDENT MANAGEMENT
============================================================

Distinguish:

OPERATIONAL ISSUE
from
SECURITY INCIDENT.

Audit whether there is an existing mechanism for:

- unauthorized access
- suspicious document access
- account compromise
- excessive permissions
- Storage exposure
- API abuse
- security escalation

Do not build a SIEM.

Determine the minimum architecture required.

============================================================
30. AUDIT TRAIL
============================================================

Audit whether the system records:

- assignment changes
- approvals
- validation
- factor changes
- calculation changes
- issue changes
- escalation
- RBAC changes
- entity status changes
- system settings changes
- worker changes
- customer approvals

Where applicable identify:

- who
- when
- old value
- new value
- reason

============================================================
31. JOB / BATCH LIFECYCLE
============================================================

Audit lifecycle states for:

- upload
- queue
- planning
- assignment
- processing
- partial completion
- validation
- review
- approval
- completion
- failure
- cancellation
- on-hold
- reopening

Do not assume these exact states exist.

Determine current state model.

============================================================
32. CAPACITY / BUSINESS CONTINUITY
============================================================

Audit:

- worker capacity
- supervisor capacity
- entity capacity
- CarbonTally internal capacity
- entity unavailable
- worker unavailable
- queue overflow
- reassignment
- failover

Example:

Entity A unavailable
 ↓
stop new assignments
 ↓
CarbonTally internal capacity
 ↓
Entity B
 ↓
Entity C

Determine what exists.

============================================================
33. API / INTEGRATION
============================================================

Audit:

- API authentication
- API keys/tokens
- organization isolation
- entity isolation
- rate limits
- idempotency
- batch upload
- asynchronous jobs
- job status
- webhooks
- exports
- API versioning
- error handling

Do not implement.

============================================================
34. OBSERVABILITY
============================================================

Audit current capabilities for:

- API failures
- processing failures
- queue backlog
- AI failures
- extraction failures
- calculation failures
- Storage failures
- email failures
- notification failures
- webhook failures
- latency

Distinguish:

APPLICATION FUNCTIONALITY
from
INFRASTRUCTURE MONITORING.

============================================================
35. BACKUP / DISASTER RECOVERY
============================================================

Audit existing infrastructure responsibilities for:

- database backup
- Storage backup
- recovery
- RPO
- RTO
- restoration testing
- accidental deletion recovery

Do not invent capabilities.

Clearly identify what is provided by infrastructure versus CarbonTally
application code.

============================================================
36. SUBSCRIPTION / USAGE
============================================================

Audit existing support for:

- customer subscription
- usage
- document volume
- processing volume
- credits
- limits
- cancellation
- retention

Do not redesign billing unless required by current architecture.

============================================================
37. DUPLICATION CHECK
============================================================

For EVERY proposed V3 component ask:

1. Does an equivalent table already exist?
2. Does an equivalent module already exist?
3. Does an equivalent service already exist?
4. Does an equivalent queue already exist?
5. Does an equivalent assignment system already exist?
6. Does an equivalent staff/RBAC system already exist?
7. Does an equivalent review/approval system already exist?
8. Does an equivalent issue system already exist?
9. Does an equivalent configuration system already exist?

DEFAULT:

EXTEND EXISTING

rather than:

CREATE NEW.

Only propose new architecture where existing structures genuinely
cannot represent the requirement.

============================================================
38. DATABASE IMPACT MATRIX
============================================================

Create:

| V3 Requirement | Existing Table(s) | Current Support | Minimum Change | RLS Impact | Storage Impact | Risk |
|---|---|---|---|---|---|---|

Classify:

NO CHANGE
EXTEND EXISTING
NEW TABLE
NEW RELATIONSHIP
RLS CHANGE
STORAGE CHANGE
UNKNOWN

Do NOT write SQL.

============================================================
39. BACKEND IMPACT MATRIX
============================================================

Create:

| V3 Requirement | Existing Module | Current Support | Action | Risk | Evidence |
|---|---|---|---|---|---|

Actions:

KEEP
EXTEND
NEW
DEPRECATE
NO CHANGE
INVESTIGATE

============================================================
40. RBAC MATRIX
============================================================

Create a current/V3 comparison for:

- CarbonTally management
- CarbonTally operations
- CarbonTally customer service
- CarbonTally internal processors
- Data Processing Entity manager
- Entity supervisor
- Entity worker/extractor
- Entity validator/QC
- Customer
- Consultant
- System administrator
- other existing roles discovered in code

For each identify:

- visibility
- create
- edit
- approve
- assign
- escalate
- communicate
- prohibited access

Do not invent roles that do not have evidence.

============================================================
41. COMMUNICATION MATRIX
============================================================

Create:

| Sender | Recipient | Allowed? | Existing Mechanism | V3 Change |
|---|---|---|---|---|

Must explicitly cover:

Customer
 → CarbonTally Customer Service

Customer
 → external entity

Customer
 → external worker

CarbonTally Customer Service
 → CarbonTally Operations

CarbonTally Operations
 → Entity Manager

Entity Manager
 → Supervisor

Supervisor
 → Worker

Worker
 → Customer

Entity
 → CarbonTally

============================================================
42. SYSTEM SETTINGS MATRIX
============================================================

Create:

| Setting | Current Location | Scope | Who Can Change | Audited? | V3 Action |
|---|---|---|---|---|---|

Cover where applicable:

- auto-assignment
- reassignment
- SLA
- escalation
- QC
- notification
- capacity
- feature flags
- file limits
- AI thresholds
- factor matching thresholds
- security settings
- workflow settings

============================================================
43. ISSUE MANAGEMENT MATRIX
============================================================

Create:

| Issue Type | Current System | Escalation Path | SLA | Customer Visible? | V3 Action |
|---|---|---|---|---|---|

============================================================
44. DATA FLOW MATRIX
============================================================

Create:

| Input Method | Extraction | Validation | Factor Matching | Calculation | Customer Review |
|---|---|---|---|---|---|

Include:

- CSV/Excel
- AI extraction
- human extraction
- manual entry
- API if already implemented

============================================================
45. REQUIRED REPORT STRUCTURE
============================================================

Create:

docs/audit/CarbonTally_V3_Impact_Analysis.md

with exactly these major sections:

# CarbonTally V3 Impact Analysis

## 1. Executive Summary

## 2. Current V2.1 Architecture

## 3. Canonical V3 Architecture

## 4. Existing Internal Manual Processing

## 5. External Human Data Processing Entity Model

## 6. 500-Document Multi-Entity Allocation

## 7. Processing Assignment and Reassignment

## 8. Validation and Approval Layers

## 9. Customer Manual Factor Selection — Current Behavior

## 10. CSV/Excel Factor Handling — Current Behavior

## 11. AI Extraction Flow

## 12. Human Extraction Flow

## 13. Common CarbonTally Processing Pipeline

## 14. Data Lineage and Provenance

## 15. Job and Batch Lifecycle

## 16. Issue Management

## 17. Escalation Architecture

## 18. System Configuration

## 19. Auto-Assignment and Workflow Configuration

## 20. Quality Control

## 21. SLA/KPI/Performance

## 22. Entity Lifecycle and Offboarding

## 23. Customer Communication Architecture

## 24. Internal Entity Communication

## 25. Cross-Entity CarbonTally Management

## 26. RBAC Analysis

## 27. RLS Analysis

## 28. Storage Security Analysis

## 29. Security Incident Management

## 30. Audit Trail

## 31. Versioning and Reprocessing

## 32. Data Retention and Deletion

## 33. Capacity and Business Continuity

## 34. API and Integration

## 35. Observability

## 36. Backup and Disaster Recovery

## 37. Subscription and Usage

## 38. Database Impact Matrix

## 39. Backend Impact Matrix

## 40. RBAC Matrix

## 41. Communication Matrix

## 42. System Settings Matrix

## 43. Issue Management Matrix

## 44. Data Flow Matrix

## 45. Existing Components to KEEP

## 46. Existing Components to EXTEND

## 47. New Components Actually Required

## 48. Components That MUST NOT Be Created

## 49. Duplicate Architecture Risks

## 50. Minimum V3 Database Change Set

## 51. Minimum V3 Backend Change Set

## 52. Minimum V3 RBAC/RLS Change Set

## 53. Minimum V3 API Change Set

## 54. Unknowns / Decisions Required

## 55. Recommended Implementation Order

## 56. Final Recommendation

============================================================
46. FINAL SUMMARY TABLE
============================================================

At the end provide:

| Domain | Current State | V3 Requirement | Action |
|---|---|---|---|
| Customers | | | |
| Consultants | | | |
| CSV/Excel | | | |
| AI Extraction | | | |
| Human Extraction | | | |
| Internal Processing | | | |
| External Processing Entities | | | |
| Jobs/Batches | | | |
| Assignment | | | |
| Reassignment | | | |
| Validation | | | |
| Approval | | | |
| QC | | | |
| Factor Providers | | | |
| Factor Matching | | | |
| Calculation | | | |
| Data Lineage | | | |
| Issue Management | | | |
| Escalation | | | |
| SLA | | | |
| KPI | | | |
| Performance | | | |
| Communication | | | |
| Notifications | | | |
| System Settings | | | |
| Auto Assignment | | | |
| RBAC | | | |
| RLS | | | |
| Storage | | | |
| Audit | | | |
| Security | | | |
| Retention | | | |
| Versioning | | | |
| API | | | |
| Usage/Billing | | | |
| Observability | | | |
| Backup/DR | | | |

============================================================
47. MINIMUM-CHANGE PRINCIPLE
============================================================

Throughout this assessment:

DO NOT redesign the platform unnecessarily.

Prefer:

EXISTING
   ↓
EXTEND

over:

EXISTING
   ↓
REPLACE

and prefer:

EXISTING
   ↓
REUSE

over:

CREATE NEW.

Do not propose a new table/module unless you can explain why an
existing structure cannot support the requirement.

============================================================
48. WHAT MUST NOT CHANGE WITHOUT EVIDENCE
============================================================

Do not redesign or replace:

- existing factor-provider architecture
- emission-factor database
- factor matching engine
- calculation engine
- existing extraction engines
- existing working manual-processing workflow
- existing consultant functionality
- existing customer architecture

unless the audit discovers an actual V3 compatibility problem.

============================================================
49. FINAL QUESTION
============================================================

The report MUST end by answering:

"Can CarbonTally V3 be implemented incrementally on top of the
current V2.1 database/backend architecture without a major rewrite?"

Answer:

YES / NO / PARTIALLY

Then explain exactly why, using evidence from:

- schema
- migrations
- backend
- API
- RBAC
- RLS
- Storage
- frontend where relevant

============================================================
50. STRICT STOP CONDITION
============================================================

After creating:

docs/audit/CarbonTally_V3_Impact_Analysis.md

STOP.

Do NOT:

- modify source code
- modify database
- create migrations
- modify RLS
- modify Storage
- modify APIs
- modify frontend
- install dependencies
- refactor
- delete files
- rename files
- commit
- push

ONLY produce the READ-ONLY analysis report.

============================================================
END OF TASK
============================================================