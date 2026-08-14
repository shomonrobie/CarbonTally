# CarbonTally UI/UX Design Principles & Guidelines v1.0
## Controlled Document Processing Workspace
## Babui Remote Workers / Freelancers / Contractual Data Operators

IMPORTANT:
This is a UI/UX DESIGN task.

DO NOT IMPLEMENT CODE YET.

Do not modify:
- database schema
- migrations
- RLS
- authentication
- backend
- API
- Supabase policies
- Storage policies
- existing business logic

The goal is to produce the UI/UX architecture, user flows, screen specifications, interaction rules, and design principles for CarbonTally's controlled manual data-processing workforce.

============================================================
1. PRODUCT CONTEXT
============================================================

CarbonTally is a carbon-data processing platform.

Customers may submit:

- PDF
- images
- CSV
- XLSX
- other supported business documents

CarbonTally processes these documents through:

UPLOAD
    ↓
EXTRACTION
    ↓
NORMALIZATION
    ↓
EMISSION FACTOR MAPPING
    ↓
SCOPE 1 / 2 / 3 MAPPING
    ↓
VALIDATION
    ↓
CUSTOMER REVIEW
    ↓
APPROVAL
    ↓
STRUCTURED CARBON DATA

Some processing may be automatic.

Some documents/data require human processing.

Human processing will be performed by Babui Limited Bangladesh using:

- employees
- remote workers
- freelancers
- contractual data-processing operators
- validators
- QA personnel

These workers may work from home.

They must NOT receive unrestricted access to CarbonTally customer data.

============================================================
2. CORE SECURITY/UX PRINCIPLE
============================================================

The UI must follow:

LEAST PRIVILEGE
+
NEED TO KNOW
+
ASSIGNED WORK ONLY
+
CONTROLLED DOCUMENT VIEWING
+
NO UNNECESSARY DOWNLOAD
+
AUDITABILITY
+
CLEAR USER RESPONSIBILITY

The UI must never encourage workers to download customer documents.

The operator should process documents inside CarbonTally.

The desired mental model is:

CUSTOMER DOCUMENT
       ↓
PRIVATE STORAGE
       ↓
ASSIGNED PROCESSING JOB
       ↓
AUTHORIZED OPERATOR
       ↓
SECURE DOCUMENT VIEWER
       ↓
EXTRACTION FORM
       ↓
VALIDATION
       ↓
STRUCTURED DATA

NOT:

CUSTOMER DOCUMENT
       ↓
DOWNLOAD TO LAPTOP
       ↓
EDIT LOCALLY
       ↓
UPLOAD AGAIN

============================================================
3. PRIMARY OPERATOR EXPERIENCE
============================================================

The operator's experience should feel like a secure work queue.

The operator should primarily see:

MY WORK

rather than:

ALL CUSTOMER DATA

Example:

+----------------------------------------------------+
| CarbonTally                    Operator             |
+----------------------------------------------------+
| My Queue | In Progress | Validation | Completed    |
+----------------------------------------------------+
|                                                    |
| Job #CT-10482                                      |
| Client: [limited display]                          |
| Document: Supplier Invoice - May 2026.pdf          |
| Status: Ready for Extraction                       |
| Priority: Normal                                   |
|                                                    |
| [ START PROCESSING ]                               |
|                                                    |
+----------------------------------------------------+

The operator should NOT have a global customer database browser.

============================================================
4. ROLE-BASED UI
============================================================

The UI must change according to the user's actual role.

Potential internal roles:

DATA EXTRACTOR
DATA VALIDATOR
QA REVIEWER
SUPERVISOR
OPERATIONS MANAGER
ADMIN

Do not assume these roles already exist exactly as written.

Use the actual backend/RBAC model once implemented.

The design must support role-based visibility.

Example:

DATA EXTRACTOR:
- assigned jobs
- document viewer
- extraction form
- save draft
- submit extraction
- request clarification
- processing instructions

DATA VALIDATOR:
- assigned validation jobs
- source document viewer
- extracted data
- compare source vs extracted
- approve/reject/request correction

QA:
- review completed processing
- sample audits
- exception handling
- quality metrics

SUPERVISOR:
- work allocation
- queues
- worker performance
- QA
- exceptions

ADMIN:
- controlled administrative functionality

IMPORTANT:

Never rely on visual hiding alone as a security control.

The backend must enforce authorization.

The UI is only the presentation layer of the permission model.

============================================================
5. DOCUMENT VIEWER PRINCIPLES
============================================================

The document viewer is a security-sensitive component.

Operators should NOT see a conventional:

DOWNLOAD PDF

button.

Avoid:

- Download
- Save As
- Open Original
- Copy URL
- Public Link
- Share

unless explicitly authorized for the user's role.

The preferred interaction is:

+----------------------------------------------------------+
| Document: Supplier Invoice                               |
+-----------------------------+----------------------------+
|                             |                            |
|                             | Extracted Data             |
|       PDF VIEWER            |                            |
|                             | Supplier: _________        |
|       Page 1 of 4           | Date: _________            |
|                             | Amount: _________          |
|                             | Unit: _________            |
|                             |                            |
|                             | [Save Draft]               |
|                             | [Submit]                   |
|                             |                            |
+-----------------------------+----------------------------+

The operator should be able to read the document while entering structured information.

============================================================
6. SIDE-BY-SIDE EXTRACTION
============================================================

For manual extraction, prefer:

LEFT:
SOURCE DOCUMENT

RIGHT:
STRUCTURED DATA FORM

This minimizes the need for operators to switch applications.

Example:

+---------------------------+-----------------------------+
| SOURCE                    | EXTRACTION                  |
+---------------------------+-----------------------------+
|                           | Supplier                    |
|                           | [________________]          |
|                           |                             |
| PDF PAGE                  | Invoice Date                |
|                           | [________________]          |
|                           |                             |
|                           | Description                 |
|                           | [________________]          |
|                           |                             |
|                           | Quantity                    |
|                           | [________________]          |
|                           |                             |
|                           | Unit                        |
|                           | [________________]          |
|                           |                             |
|                           | Amount                      |
|                           | [________________]          |
+---------------------------+-----------------------------+

The operator should not need to download the source document.

============================================================
7. CONTROLLED DOCUMENT ACCESS
============================================================

The UX should communicate that documents are being accessed securely.

Example status:

SECURE DOCUMENT VIEW

Assigned to:
Operator #184

Access:
Processing Job #CT-10482

Session:
Active

Do not expose unnecessary technical information.

Do not expose:
- Supabase URLs
- storage paths
- signed URLs
- database IDs unless operationally necessary
- API tokens
- infrastructure information

============================================================
8. DOCUMENT WATERMARKING
============================================================

Where appropriate, the viewer should support a visible watermark.

Example:

CONFIDENTIAL
CarbonTally Processing
Operator #184
Job #CT-10482

The watermark should be subtle enough not to interfere with extraction.

Possible placement:
- page overlay
- viewer overlay
- repeated light watermark

The goal is:

DETERRENCE
+
TRACEABILITY

Do not claim watermarking prevents copying.

============================================================
9. NO LOCAL-DATA WORKFLOW
============================================================

The UX must discourage:

- downloading documents
- saving locally
- emailing documents
- uploading to personal cloud storage
- copying customer data into external applications
- using WhatsApp or personal messaging
- printing

The preferred workflow is:

VIEW
→
EXTRACT
→
SAVE
→
SUBMIT

not:

DOWNLOAD
→
PROCESS LOCALLY
→
UPLOAD

============================================================
10. JOB ASSIGNMENT UX
============================================================

Operators should receive explicit assignments.

Example:

MY QUEUE

---------------------------------------------------
READY
---------------------------------------------------
#CT-10031
Invoice — 4 pages
Estimated effort: 8 min
[START]

#CT-10044
Energy statement — 7 pages
Estimated effort: 15 min
[START]

---------------------------------------------------
IN PROGRESS
---------------------------------------------------
#CT-10022
3 of 5 pages reviewed
[CONTINUE]

---------------------------------------------------
SUBMITTED
---------------------------------------------------
#CT-10011
Awaiting validation
---------------------------------------------------

Do not expose the entire customer document repository.

============================================================
11. JOB LOCKING
============================================================

The UX should clearly indicate when a document is being processed by another operator.

Example:

"This document is currently being processed by another team member."

Do not allow two operators to accidentally overwrite each other's work.

If concurrent work is supported, make it explicit.

============================================================
12. SESSION TIMEOUT
============================================================

Because operators may work remotely, the interface should support session protection.

UX should warn before timeout:

"Your secure processing session will expire soon."

Provide:

[Continue Session]

After timeout:

"Your session has expired. Sign in again to continue."

Unsaved data should be handled safely.

Do not silently discard extraction work.

============================================================
13. AUTO-SAVE
============================================================

Where appropriate:

AUTO-SAVED 12:42:08

The operator should know whether their work is saved.

Use:

Saved
Saving...
Unsaved changes
Save failed

Do not expose sensitive data in notifications or browser alerts.

============================================================
14. MINIMIZE DATA EXPOSURE
============================================================

The operator does not necessarily need to see the customer's entire profile.

Display only the information required for processing.

For example:

GOOD:

Client:
ABC Manufacturing

Document:
Supplier Invoice

Processing type:
Purchased goods

BAD:

Full customer profile
+
Company directors
+
Billing details
+
All historical documents
+
All users
+
All emissions

Use minimum necessary information.

============================================================
15. CUSTOMER IDENTITY PROTECTION
============================================================

Where operationally possible, use limited customer identifiers.

Example:

Client:
ABC Manufacturing

rather than displaying unnecessary:
- addresses
- phone numbers
- email addresses
- contacts
- financial information

unless required to perform the task.

============================================================
16. EXTRACTION FORM UX
============================================================

The extraction form should be optimized for speed AND accuracy.

Use:

- clear field labels
- appropriate input types
- keyboard navigation
- tab order
- validation
- unit selectors
- date pickers
- autocomplete where safe
- confidence indicators
- required/optional indicators
- source highlighting if possible

Example:

Supplier
[ABC Energy Ltd                     ]

Invoice Date
[08/05/2026                         ]

Description
[Electricity consumption            ]

Quantity
[12,450                             ]

Unit
[kWh ▼]

Amount
[£1,852.40                          ]

============================================================
17. SOURCE-TO-FIELD TRACEABILITY
============================================================

Where technically possible, allow an operator to indicate where a value came from.

Example:

Amount:
£1,852.40

Source:
Page 2

or:

[View source location]

This improves QA.

============================================================
18. AI EXTRACTION REVIEW
============================================================

If AI/OCR automatically extracts data, the UI should clearly distinguish:

AI EXTRACTED
HUMAN VERIFIED
HUMAN CORRECTED

Example:

Invoice Date
08/05/2026

AI confidence:
92%

[✓ Confirm]

If confidence is low:

Invoice Date
08/05/2026

AI confidence:
54%

[Review Required]

Never make AI confidence appear more authoritative than it actually is.

============================================================
19. HUMAN-IN-THE-LOOP MODEL
============================================================

The UI should support:

AUTOMATED
     ↓
LOW CONFIDENCE
     ↓
HUMAN REVIEW
     ↓
CORRECTED
     ↓
VALIDATED
     ↓
CUSTOMER APPROVAL

Do not make human operators feel like they are merely correcting "AI mistakes."

They are performing controlled data-quality work.

============================================================
20. VALIDATION WORKSPACE
============================================================

Validator UI should compare:

SOURCE
vs
EXTRACTED DATA

Example:

+----------------------+-------------------------+
| Source Document      | Extracted Data          |
+----------------------+-------------------------+
| Electricity          | Electricity             |
| 12,450 kWh           | 12,450 kWh              |
| £1,852.40            | £1,852.40              |
| May 2026             | May 2026                |
+----------------------+-------------------------+

Validator actions:

[APPROVE]
[CORRECT]
[RETURN TO EXTRACTOR]
[FLAG]

Every decision should be attributable to the authenticated user.

============================================================
21. ERROR HANDLING
============================================================

If something cannot be extracted:

Do NOT encourage operators to guess.

Use:

"Unable to determine value from source."

Actions:

[FLAG FOR REVIEW]
[REQUEST CLARIFICATION]
[SKIP FIELD]

Never encourage fabricated data.

============================================================
22. SECURITY-RELEVANT UI STATES
============================================================

Design clear states for:

- Access denied
- Session expired
- Job no longer assigned
- Document unavailable
- Document processing
- Document locked
- Document already completed
- Permission changed
- Account suspended

Example:

ACCESS RESTRICTED

"This document is no longer assigned to your account."

Do not reveal why another user has access.

============================================================
23. AUDITABILITY UX
============================================================

The system should make important actions traceable.

Examples:

Viewed document
Started processing
Saved extraction
Submitted extraction
Returned for correction
Validated
Approved
Rejected

The operator does not need to see the entire audit database.

But the UI should communicate when actions are recorded.

Example:

"Submission recorded."

============================================================
24. PRIVACY-FIRST DESIGN
============================================================

Use data minimization.

Do not display unnecessary personal information.

Do not duplicate customer data across screens.

Avoid persistent browser storage of sensitive customer information.

Do not use sensitive customer data in:
- URLs
- browser titles
- notifications
- analytics events
- client-side logs

============================================================
25. NO CUSTOMER DATA IN FRONTEND LOGGING
============================================================

The UI must not intentionally log:

- PDF contents
- extracted personal data
- customer financial information
- access tokens
- API keys
- signed URLs

Design error states that provide useful troubleshooting without exposing sensitive information.

============================================================
26. REMOTE-WORK UX
============================================================

Operators may have:
- modest internet connections
- small laptop screens
- different screen sizes
- varying technical skills

Design for:

- responsive desktop-first workflow
- low bandwidth where possible
- progressive loading
- clear loading states
- recoverable errors
- keyboard-first operation
- minimal unnecessary animations
- efficient page navigation

The operator should be able to process documents efficiently without sacrificing security.

============================================================
27. MOBILE
============================================================

Mobile should NOT be the primary operator environment.

Manual PDF extraction is primarily a desktop/laptop workflow.

Mobile may support:
- account management
- queue overview
- notifications
- supervisor monitoring

but not necessarily the complete extraction experience.

============================================================
28. ACCESSIBILITY
============================================================

Follow accessible UI principles.

Include:
- keyboard navigation
- visible focus
- sufficient contrast
- meaningful labels
- screen-reader-friendly controls
- accessible error messages
- no color-only status indicators

============================================================
29. UI SHOULD NOT CREATE SECURITY BYPASS INCENTIVES
============================================================

This is critical.

If the secure workflow is inconvenient, operators may attempt workarounds.

Therefore:

SECURE
must also be
FAST
CLEAR
EASY

For example:

Bad:

Open PDF
→ wait
→ open separate form
→ manually switch windows
→ copy values
→ return
→ save

Better:

PDF
+
Extraction form
+
Keyboard navigation
+
Auto-save
+
Source reference

inside one workspace.

============================================================
30. OPERATOR DASHBOARD
============================================================

Design a simple operator dashboard.

Recommended:

--------------------------------------------------
MY WORK
--------------------------------------------------

Ready for processing       12
In progress                 2
Needs correction            3
Submitted                   8

--------------------------------------------------
TODAY
--------------------------------------------------

Documents processed        17
Fields extracted           243
Returned for correction     2

--------------------------------------------------
CURRENT JOB
--------------------------------------------------

#CT-10482
Supplier Invoice
4 pages

[CONTINUE]

Do not turn this into a general customer analytics dashboard.

============================================================
31. SUPERVISOR DASHBOARD
============================================================

Supervisor may see:

- queue
- assignments
- workload
- processing status
- QA status
- exceptions
- turnaround time
- correction rate
- productivity metrics

But only according to their authorized scope.

Do not expose customer documents unnecessarily.

============================================================
32. SECURITY BOUNDARY
============================================================

Clearly distinguish:

CUSTOMER WORKSPACE

from:

CARBONTALLY OPERATIONS WORKSPACE

from:

BABUI PROCESSING WORKSPACE

The operator should never feel like they are a customer administrator.

Conceptually:

CUSTOMER
    ↓
Customer Workspace

CARBONTALLY STAFF
    ↓
Operations Workspace

BABUI OPERATOR
    ↓
Processing Workspace

Each has different navigation and permissions.

============================================================
33. CUSTOMER WORKSPACE
============================================================

Customer may:

- upload
- review extraction
- correct
- approve
- reject
- view emissions trends
- export their own data
- communicate with CarbonTally

Customer should NOT see:
- internal operator identity
- internal queues
- operator productivity
- internal notes
- internal security details

unless explicitly intended.

============================================================
34. INTERNAL PROCESSING WORKSPACE
============================================================

Internal/Babui worker navigation should be minimal:

[My Queue]
[In Progress]
[Validation]
[Completed]
[Help]
[Profile]

Avoid:

[All Customers]
[All Documents]
[All Organizations]

unless the role explicitly requires them.

============================================================
35. VISUAL LANGUAGE
============================================================

The interface should communicate:

TRUST
PRECISION
CONTROL
SECURITY
PROFESSIONALISM
EFFICIENCY

Avoid:
- excessive dashboards
- flashy animations
- unnecessary gradients
- gamification
- confusing badges
- excessive colors

Use status colors consistently.

Examples:

Green = completed/approved
Amber = attention required
Red = blocked/error
Blue/neutral = processing/information

Do not rely on color alone.

============================================================
36. DESIGN SYSTEM
============================================================

Define:

- typography
- spacing
- buttons
- form controls
- status badges
- alerts
- tables
- document viewer
- side panels
- modals
- tooltips
- loading states
- empty states
- error states
- confirmation states

Maintain consistency across:
- Customer Workspace
- Consultant Workspace
- Processing Workspace
- Admin Workspace

============================================================
37. SECURITY COPY
============================================================

Use calm, professional security language.

GOOD:

"Secure document access"

"Your assigned processing job"

"Document access is recorded"

"Your session will expire soon"

"Access restricted"

BAD:

"You are being monitored"

"WARNING: SECURITY VIOLATION"

"ADMIN HAS BEEN ALERTED"

Do not create an unnecessarily hostile operator experience.

============================================================
38. DOWNLOAD PREVENTION UX
============================================================

The UI should NOT display a download button to restricted roles.

Do not display:

[Download PDF]

Instead:

[View Document]

If a restricted operator tries a disallowed action:

"Downloading source documents isn't available for your role."

Do not expose technical implementation details.

If an authorized role has download permission, clearly display the permission and log the action.

============================================================
39. PRINTING / COPY
============================================================

Where technically appropriate:

- discourage printing
- do not provide print controls for restricted roles
- avoid exposing raw document URLs
- avoid unnecessary copy controls

Do not claim these controls can guarantee prevention of screenshots or photographs.

============================================================
40. SCREENSHOT / PHYSICAL-COPY AWARENESS
============================================================

Recognize that browser controls cannot guarantee prevention of:

- screenshots
- screen recording
- photographing the screen
- manual transcription

Therefore use:

ACCESS CONTROL
+
WATERMARK
+
AUDIT LOG
+
TRAINING
+
CONTRACTUAL CONFIDENTIALITY

rather than pretending technical controls are absolute.

============================================================
41. WORKER TRUST MODEL
============================================================

The UI should assume:

"Authorized worker, limited access."

NOT:

"Trusted employee, unlimited access."

Every worker should receive only:

- assigned jobs
- minimum necessary customer information
- minimum necessary document access
- minimum necessary actions

============================================================
42. DESIGN FOR FUTURE SCALE
============================================================

The design must support:

10 operators
→
50 operators
→
200 operators
→
1,000+ operators

without giving workers broader access.

Use:
- queues
- assignments
- workload balancing
- role-based permissions
- job-based access

rather than manual sharing of documents.

============================================================
43. FUTURE API / AUTOMATION
============================================================

Do not design the operator workspace as the only processing mechanism.

CarbonTally may later receive:

API
 ↓
Batch upload
 ↓
Automatic extraction
 ↓
Automatic mapping
 ↓
Human exception queue
 ↓
Validation
 ↓
Result

The UI should support the concept:

AUTOMATION FIRST
HUMAN WHEN NECESSARY

============================================================
44. REQUIRED UI/UX DELIVERABLES
============================================================

Do NOT code the UI.

Create a design specification document:

CARBONTALLY_PROCESSING_WORKSPACE_UI_UX_V1.md

Include:

# 1. Design Goals

# 2. Security Principles

# 3. User Roles

# 4. Permission Model Assumptions

# 5. Information Architecture

# 6. Navigation

# 7. Operator Dashboard

# 8. Job Queue

# 9. Job Detail

# 10. Secure Document Viewer

# 11. Extraction Workspace

# 12. AI Extraction Review

# 13. Validation Workspace

# 14. QA Workspace

# 15. Supervisor Workspace

# 16. Access-Denied States

# 17. Session Expiration

# 18. Auto-save

# 19. Auditability

# 20. Watermarking

# 21. Download/Print Restrictions

# 22. Error Handling

# 23. Accessibility

# 24. Responsive Design

# 25. Security UX Guidelines

# 26. Data Minimization

# 27. Design System

# 28. User Journeys

# 29. Screen Inventory

# 30. Component Inventory

# 31. Future API/Bulk Processing UX

# 32. Open Questions

============================================================
45. REQUIRED USER JOURNEYS
============================================================

Document these journeys:

JOURNEY A
Operator login
→ assigned queue
→ open job
→ view PDF
→ extract data
→ save
→ submit

JOURNEY B
AI extraction
→ low confidence
→ operator review
→ correction
→ submit

JOURNEY C
Validator
→ assigned validation job
→ view source
→ compare data
→ approve

JOURNEY D
Validator
→ find error
→ return to extractor
→ extractor corrects
→ validator rechecks

JOURNEY E
Operator tries to access unassigned document
→ access denied

JOURNEY F
Operator session expires
→ warning
→ save state
→ re-authenticate
→ continue

JOURNEY G
Operator attempts restricted download
→ action unavailable
→ explanation

JOURNEY H
Supervisor assigns job
→ operator receives job
→ operator processes
→ validator receives result

============================================================
46. REQUIRED SECURITY UX RULES
============================================================

Create a table:

| UX Area | Rule | Reason |
|---------|------|--------|

At minimum include:

- document access
- downloads
- printing
- storage URLs
- job assignment
- customer visibility
- RBAC
- session management
- audit trail
- watermark
- data minimization
- copy/paste
- exports
- errors
- notifications
- browser storage

============================================================
47. IMPORTANT ARCHITECTURAL PRINCIPLE
============================================================

The UI must NEVER be the actual security boundary.

The final architecture must be:

Frontend
   ↓
Backend authorization
   ↓
Supabase RLS / Storage policies
   ↓
Database/storage

The frontend should represent permissions.

It must not create permissions.

============================================================
48. FINAL DESIGN PRINCIPLE
============================================================

CarbonTally's processing workspace should make the safest workflow the easiest workflow.

The operator should think:

"I have a job assigned to me.
I can see the source document.
I can enter the required data.
I can save and submit it.
I don't need to download anything."

That is the desired UX.

============================================================
49. FINAL OUTPUT
============================================================

Produce:

CARBONTALLY_PROCESSING_WORKSPACE_UI_UX_V1.md

Also produce:

CARBONTALLY_PROCESSING_SCREEN_INVENTORY_V1.md

CARBONTALLY_PROCESSING_USER_FLOWS_V1.md

CARBONTALLY_PROCESSING_SECURITY_UX_RULES_V1.md

Do not write application code.

Do not modify existing code.

Do not modify database schema.

Do not modify RLS.

Do not modify Supabase.

Do not modify deployment configuration.

This phase is DESIGN ONLY.

After completing the documents, provide a concise terminal summary:

============================================================
CARBONTALLY PROCESSING WORKSPACE UX DESIGN COMPLETE
============================================================

Roles defined:
YES / NO

Operator workflow:
YES / NO

Secure PDF viewer:
YES / NO

Extraction workspace:
YES / NO

Validation workflow:
YES / NO

Supervisor workflow:
YES / NO

Download restriction UX:
YES / NO

Watermark concept:
YES / NO

Auditability:
YES / NO

Data minimization:
YES / NO

Responsive design:
YES / NO

API/batch future workflow:
YES / NO

CODE MODIFIED:
NO

DATABASE MODIFIED:
NO

SECURITY POLICIES MODIFIED:
NO