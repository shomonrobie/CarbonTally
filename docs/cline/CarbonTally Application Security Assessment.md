CarbonTally Internal Application Security Assessment v1.0
Master rules for every phase

Paste this block at the beginning of every Cline phase:

CARBONTALLY INTERNAL APPLICATION SECURITY ASSESSMENT v1.0

MODE: READ-ONLY SECURITY ASSESSMENT

You are performing an internal application security assessment of CarbonTally.

THIS IS AN ANALYSIS-ONLY TASK.

ABSOLUTELY DO NOT:
- modify source code
- modify database schema
- create migrations
- modify migrations
- modify RLS policies
- modify Storage policies
- modify Supabase configuration
- modify Vercel configuration
- modify Render configuration
- modify Resend configuration
- modify environment variables
- install packages
- upgrade packages
- downgrade packages
- deploy
- restart services
- create users
- modify users
- modify permissions
- modify database records
- upload files to production
- delete files
- rotate secrets
- expose secrets
- perform destructive penetration testing
- perform denial-of-service testing
- perform load testing
- access or exfiltrate another customer's real data

You MAY:
- read source code
- read database migrations
- read database schemas
- read configuration
- inspect RLS policies
- inspect Storage policies
- inspect API routes
- inspect authentication logic
- inspect RBAC logic
- inspect tests
- inspect dependencies
- run SAFE read-only/static security scanners
- analyze local code
- identify vulnerabilities
- document evidence
- recommend remediation

DO NOT FIX ANYTHING.

If you discover a vulnerability:
1. document it
2. provide evidence
3. explain impact
4. recommend remediation
5. do not implement the remediation

Never assume architecture. Inspect the actual repository.

Never claim something is secure merely because a managed provider is used.

Never claim a vulnerability without evidence.

Clearly distinguish:
- CONFIRMED
- LIKELY
- POSSIBLE
- NOT VERIFIED

Do not expose secrets in reports. Mask them.

All findings must reference the actual:
- file
- function/class
- database table
- policy
- endpoint
- configuration
where possible.

The assessment is for CarbonTally's application layer, not penetration testing of Supabase, Vercel, Render or Resend infrastructure.
Phase 0 — Repository Reconnaissance

Goal: Understand what you actually have before testing anything.

Cline prompt
PHASE 0 — CARBONTALLY SECURITY RECONNAISSANCE

Apply the master READ-ONLY rules.

Do not perform vulnerability testing yet.

First map the actual CarbonTally repository.

Identify:

1. Frontend
2. Backend
3. API
4. Supabase integration
5. PostgreSQL migrations
6. RLS policies
7. Storage configuration
8. Authentication
9. RBAC
10. Organization/tenant model
11. Consultant model
12. Internal CarbonTally staff model
13. Background workers
14. Document processing
15. CSV processing
16. Excel processing
17. PDF/OCR processing
18. Emission-factor mapping
19. Calculation pipeline
20. Validation workflow
21. Customer approval workflow
22. Realtime
23. Notifications
24. Resend integration
25. Vercel configuration
26. Render configuration
27. Environment configuration
28. API keys/secrets handling
29. Tests
30. Dependency manifests

Create:

CARBONTALLY_SECURITY_PHASE0_RECON.md

Include:

# Executive Summary

# Actual Architecture

# Repository Structure

# Technology Stack

# Authentication Flow

# Authorization Flow

# Organization/Tenant Model

# Consultant Model

# Internal Staff Model

# Data Processing Flow

# Document Flow

# API Flow

# Background Worker Flow

# Supabase Components

# External Services

# Security-Critical Files

# Security-Critical Database Objects

# Unknowns / Missing Information

# Initial Threat Surface

DO NOT modify anything.

At the end provide:

- files inspected
- database objects inspected
- areas requiring deeper assessment
- areas that could not be verified

STOP after completing the report.
Phase 1 — Authentication & RBAC

This is intentionally separate from RLS.

Cline prompt
PHASE 1 — AUTHENTICATION AND RBAC SECURITY

Apply the master READ-ONLY rules.

Use Phase 0 reconnaissance findings.

Assess ONLY:

1. Authentication
2. User sessions
3. Login/logout
4. Password/reset flows
5. Invitations
6. Organization membership
7. Organization access
8. RBAC
9. Role changes
10. Privilege escalation

Inspect actual implementation.

Determine:

AUTHENTICATION

- What authenticates users?
- Where are sessions validated?
- Are protected backend routes actually authenticated?
- Are frontend checks incorrectly relied upon?
- Can unauthenticated requests reach protected functionality?
- What happens after logout?
- What happens after access is revoked?
- Are stale sessions possible?

RBAC

Inventory every actual role.

For each role determine:

ROLE
→ permitted operations
→ permitted resources
→ permitted organizations

Check:

- junior consultant
- senior consultant
- consultant/admin
- CarbonTally extractor
- CarbonTally validator
- CarbonTally administrator
- customer/user roles
- any other implemented roles

Look for:

- privilege escalation
- role manipulation
- self-assignment of roles
- frontend-only authorization
- missing backend authorization
- stale authorization
- organization switching vulnerabilities

Create:

CARBONTALLY_SECURITY_PHASE1_AUTH_RBAC.md

Include:

# Executive Summary

# Authentication Architecture

# Session Security

# Invitation/Access Flow

# RBAC Inventory

# Authorization Flow

# Findings

# Evidence

# Severity

# Remediation Recommendations

# Verification Requirements

Do not modify anything.

STOP after completing the report.
Phase 2 — Organization Isolation / RLS

This is the most important phase for CarbonTally.

Cline prompt
PHASE 2 — MULTI-TENANT ORGANIZATION ISOLATION AND SUPABASE RLS

Apply the master READ-ONLY rules.

This is a CRITICAL security assessment.

The primary security requirement is:

ORGANIZATION A MUST NEVER ACCESS ORGANIZATION B DATA.

Inspect the actual database schema and all relevant migrations/policies.

Inventory every table.

Classify each as:

A. Global/reference data
B. Organization-owned data
C. User-owned data
D. Internal/platform data
E. Processing/job data
F. Unknown

For every organization-owned table determine:

- organization_id
- ownership relationship
- foreign keys
- RLS enabled?
- SELECT policy
- INSERT policy
- UPDATE policy
- DELETE policy
- WITH CHECK
- USING
- related-table access
- views
- functions
- triggers

Pay special attention to:

organization_access

or whatever actual equivalent exists.

Determine whether organization authorization is consistently derived from authenticated identity rather than client-supplied organization IDs.

Look for:

- missing RLS
- incorrect RLS
- permissive policies
- missing WITH CHECK
- unsafe OR conditions
- NULL organization IDs
- client-supplied organization IDs
- cross-tenant joins
- insecure views
- SECURITY DEFINER functions
- privileged functions
- policy bypasses
- inconsistent organization ownership

Produce a table:

| Table | Ownership | Org Boundary | RLS | SELECT | INSERT | UPDATE | DELETE | Risk | Evidence |

Then create:

CARBONTALLY_SECURITY_PHASE2_TENANT_RLS.md

Include a dedicated:

# Organization Isolation Verdict

Answer:

1. Can Organization A read Organization B?
2. Can A insert into B?
3. Can A update B?
4. Can A delete B?
5. Can A access B through views?
6. Can A access B through RPC/functions?
7. Can A manipulate organization_id?
8. Can consultants access unintended organizations?
9. Can internal staff access unintended organizations?
10. Can privileged service-role operations bypass isolation?

For each answer use:

CONFIRMED SAFE
CONFIRMED VULNERABLE
NOT VERIFIED

Do not guess.

Do not modify anything.

STOP after completing the report.
Phase 3 — Supabase Storage & Realtime
Cline prompt
PHASE 3 — SUPABASE STORAGE AND REALTIME SECURITY

Apply the master READ-ONLY rules.

Assess:

A. Supabase Storage
B. Realtime

STORAGE

Inventory:

- buckets
- public/private status
- storage.objects policies
- upload policies
- SELECT policies
- UPDATE policies
- DELETE policies
- signed URL generation
- document paths
- organization ownership

Determine whether:

Organization A can obtain Organization B's:
- PDFs
- images
- CSVs
- Excel files
- extracted documents
- generated exports

Look for:

- predictable storage paths
- IDOR
- insecure signed URLs
- missing ownership checks
- public buckets
- weak Storage RLS
- backend download endpoints bypassing Storage policies

REALTIME

Inspect:

- channels
- subscriptions
- messages
- notifications
- chat
- job status
- authorization

Determine whether one organization can subscribe to another organization's:
- messages
- notifications
- processing status
- realtime events

Create:

CARBONTALLY_SECURITY_PHASE3_STORAGE_REALTIME.md

Include:

# Storage Architecture

# Storage Access Model

# Storage Policy Matrix

# Document Isolation

# Signed URL Assessment

# Realtime Architecture

# Realtime Authorization

# Findings

# Remediation

Do not modify anything.

STOP.
Phase 4 — API / Backend / BOLA

This is where Cline should trace every important API path.

Cline prompt
PHASE 4 — API AND BACKEND AUTHORIZATION SECURITY

Apply the master READ-ONLY rules.

Inventory every API endpoint actually implemented.

For each endpoint record:

| Method | Endpoint | Authentication | Role | Organization Check | Resource Ownership | Input Validation | Risk |

Assess especially:

- IDOR
- BOLA
- privilege escalation
- missing authorization
- organization_id manipulation
- resource ID manipulation
- mass assignment
- excessive data exposure
- unsafe query parameters
- injection risks
- SSRF
- path traversal
- unsafe deserialization
- insecure error handling

Trace critical workflows:

DOCUMENT UPLOAD
→ PROCESSING JOB
→ EXTRACTION
→ MAPPING
→ VALIDATION
→ APPROVAL
→ RESULT
→ EXPORT

For each stage verify that tenant context is preserved.

Specifically determine whether:

document.organization_id
        ↓
job.organization_id
        ↓
worker
        ↓
extraction
        ↓
mapping
        ↓
validation
        ↓
result

remains correctly associated.

Pay particular attention to endpoints equivalent to:

POST processing job
GET processing job
GET document
GET extracted data
GET results
GET export
POST approval
POST rejection

Use the actual endpoints.

Create:

CARBONTALLY_SECURITY_PHASE4_API_BACKEND.md

Include:

# API Inventory

# Authorization Model

# Tenant Context Propagation

# BOLA/IDOR Assessment

# Input Validation

# Sensitive Data Exposure

# Findings

# Remediation

Do not modify anything.

STOP.
Phase 5 — File Processing Security

This is particularly important for your platform because PDF/XLSX/CSV/image uploads are central to CarbonTally.

Cline prompt
PHASE 5 — FILE UPLOAD AND DATA PROCESSING SECURITY

Apply the master READ-ONLY rules.

Assess the actual file-processing pipeline.

Supported/expected data may include:

- PDF
- image
- CSV
- XLSX

Inspect:

- upload validation
- MIME validation
- extension validation
- file size limits
- filename handling
- temporary files
- storage
- parsing
- OCR
- extraction
- worker processing
- generated files
- exports

Look for:

- path traversal
- malicious file handling
- parser vulnerabilities
- SSRF
- arbitrary file access
- command execution risks
- resource exhaustion
- decompression bombs
- spreadsheet formula injection
- macro-enabled files
- external references
- unsafe PDF processing
- cross-tenant file processing
- temporary-file leakage
- data leakage through errors/logs

DO NOT upload malicious files to production.

Use static code analysis and safe local inspection only.

Trace:

UPLOAD
 ↓
STORAGE
 ↓
JOB
 ↓
WORKER
 ↓
EXTRACT
 ↓
NORMALIZE
 ↓
MAP
 ↓
VALIDATE
 ↓
SAVE
 ↓
CUSTOMER APPROVAL

Determine whether organization ownership survives every stage.

Create:

CARBONTALLY_SECURITY_PHASE5_FILE_PROCESSING.md

Include:

# File Architecture

# Upload Security

# PDF Security

# Image Security

# CSV Security

# XLSX Security

# Worker Security

# Temporary Data

# Tenant Isolation During Processing

# Findings

# Remediation

Do not modify anything.

STOP.
Phase 6 — Secrets, Dependencies & Deployment
Cline prompt
PHASE 6 — SECRETS, DEPENDENCIES AND DEPLOYMENT SECURITY

Apply the master READ-ONLY rules.

Assess:

1. Secrets
2. Dependencies
3. Vercel
4. Render
5. Resend
6. CI/CD
7. Git repository exposure

SECRETS

Search safely for:
- API keys
- tokens
- passwords
- database credentials
- Supabase service role
- Resend keys
- JWT secrets
- private keys

DO NOT PRINT SECRET VALUES.

Mask them.

Determine whether privileged secrets could reach:
- browser
- frontend bundle
- logs
- Git
- error responses
- emails

DEPENDENCIES

Run safe read-only scanners if available.

Inspect:
- package files
- lock files
- Python requirements
- Node dependencies

Report known vulnerabilities.

Do not upgrade anything.

VERCEL

Assess application configuration:
- environment variables
- public variables
- frontend exposure
- server-side secrets
- API routes
- headers
- CORS
- preview environments

RENDER

Assess:
- environment variables
- public services
- worker services
- API services
- internal/public boundaries
- logs
- secrets

RESEND

Assess:
- API key handling
- webhooks
- notification authorization
- customer data exposure

Do NOT test provider infrastructure.

Create:

CARBONTALLY_SECURITY_PHASE6_SECRETS_DEPLOYMENT.md

Include:

# Secrets Assessment

# Dependency Assessment

# Vercel Assessment

# Render Assessment

# Resend Assessment

# CI/CD Assessment

# Git Exposure Assessment

# Findings

# Remediation

Do not modify anything.

STOP.
Phase 7 — Security Headers, Logging & Data Lifecycle
Cline prompt
PHASE 7 — WEB SECURITY, LOGGING AND DATA LIFECYCLE

Apply the master READ-ONLY rules.

Assess:

WEB SECURITY

Inspect:
- HTTPS
- HSTS
- CSP
- X-Frame-Options / frame-ancestors
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy
- CORS
- cookies
- SameSite
- Secure
- cache-control

LOGGING

Determine whether security-sensitive events are logged:

- login
- logout
- role change
- organization access
- document upload
- document download
- processing
- validation
- approval
- rejection
- export
- deletion
- admin actions

Check whether logs leak:
- tokens
- API keys
- passwords
- document contents
- personal data
- customer data

DATA LIFECYCLE

Inspect:
- deletion
- cancellation
- organization suspension
- account deletion
- document deletion
- processing result deletion
- storage cleanup
- orphan records
- API key revocation

Do not make legal conclusions.

Only assess technical implementation.

Create:

CARBONTALLY_SECURITY_PHASE7_WEB_LOGGING_LIFECYCLE.md

Do not modify anything.

STOP.
Phase 8 — Threat Model & Attack-Path Review

This is where Cline brings all previous findings together.

Cline prompt
PHASE 8 — CARBONTALLY THREAT MODEL AND ATTACK PATH ANALYSIS

Apply the master READ-ONLY rules.

Read all previous Phase 0–7 reports.

Build a complete CarbonTally threat model.

Threat actors:

1. Unauthenticated attacker
2. Authenticated customer user
3. Malicious organization member
4. Malicious consultant
5. Compromised consultant
6. CarbonTally data extractor
7. CarbonTally validator
8. CarbonTally administrator
9. Compromised API key
10. Compromised worker
11. Attacker possessing document ID
12. Attacker manipulating organization_id

Analyze attack paths involving:

AUTH
 ↓
USER
 ↓
ORGANIZATION ACCESS
 ↓
ORGANIZATION
 ↓
DOCUMENT
 ↓
PROCESSING JOB
 ↓
EXTRACTED DATA
 ↓
MAPPED DATA
 ↓
EMISSIONS
 ↓
EXPORT/API

Look specifically for chains where multiple individually minor weaknesses become a serious vulnerability.

Examples:

Weak authorization
+
predictable ID
=
cross-tenant access

OR:

Privileged worker
+
unvalidated organization_id
=
cross-tenant processing

OR:

Storage path exposure
+
weak signed URL authorization
=
document exposure

Create:

CARBONTALLY_SECURITY_PHASE8_THREAT_MODEL.md

Include:

# Threat Actors

# Assets

# Trust Boundaries

# Attack Surface

# Attack Paths

# Cross-Tenant Attack Paths

# Privilege Escalation Paths

# Document Exposure Paths

# API Attack Paths

# Processing Pipeline Risks

# Highest Risk Scenarios

# Recommended Controls

Do not exploit real customer data.

Do not modify anything.

STOP.
Phase 9 — Final Consolidated Assessment

Only run this after all previous phases are complete.

Cline prompt
PHASE 9 — FINAL CARBONTALLY INTERNAL SECURITY ASSESSMENT

Apply the master READ-ONLY rules.

Read:

Phase 0
Phase 1
Phase 2
Phase 3
Phase 4
Phase 5
Phase 6
Phase 7
Phase 8

Do not redo the entire repository scan unless necessary to resolve a contradiction.

Create the final consolidated report:

CARBONTALLY_SECURITY_ASSESSMENT_V1.md

Structure:

# CarbonTally Internal Application Security Assessment v1.0

## 1. Executive Summary

## 2. Assessment Scope

## 3. Architecture Reviewed

## 4. Technology Stack

## 5. Authentication

## 6. Authorization

## 7. RBAC

## 8. Organization Isolation

## 9. Supabase RLS

## 10. Supabase Storage

## 11. Supabase Realtime

## 12. API Security

## 13. Backend Security

## 14. Background Workers

## 15. File Processing

## 16. Secrets

## 17. Dependencies

## 18. Vercel

## 19. Render

## 20. Resend

## 21. Web Security

## 22. Logging

## 23. Data Lifecycle

## 24. Threat Model

## 25. Findings

## 26. Risk Matrix

## 27. Remediation Roadmap

## 28. External Testing Recommendations

## 29. Privacy/Legal Review Items

## 30. Limitations

## 31. Final Verdict

Create:

CARBONTALLY_SECURITY_FINDINGS_V1.md

Format:

| ID | Severity | Area | Finding | Evidence | Status |
|----|----------|------|---------|----------|--------|

Severity:
CRITICAL
HIGH
MEDIUM
LOW
INFO

Status:
CONFIRMED
LIKELY
POSSIBLE
NOT VERIFIED
INFORMATIONAL

Create:

CARBONTALLY_SECURITY_REMEDIATION_PLAN_V1.md

Priorities:

P0 — Must fix before production
P1 — Fix before meaningful commercial scale
P2 — Fix before enterprise expansion
P3 — Defense in depth

DO NOT IMPLEMENT ANY FIXES.

Create:

CARBONTALLY_PUBLIC_SECURITY_SUMMARY_V1.md

This must be safe for a public website.

Do NOT include:
- vulnerabilities
- attack paths
- secrets
- detailed RLS policies
- internal architecture
- database structure
- customer information

Only include verified security controls.

IMPORTANT:

Do not call this an "independent security audit."

Call it:

"Internal Application Security Assessment"

Final verdict must explicitly answer:

1. Is CarbonTally ready for controlled beta?
2. Is CarbonTally ready for paying customers?
3. Is tenant isolation adequately implemented?
4. Are there CRITICAL findings?
5. Are there HIGH findings?
6. What must be fixed before launch?
7. What can wait?
8. What requires external penetration testing?
9. What requires privacy/legal review?
10. What is provider responsibility?

Use:

GREEN
AMBER
RED

Do not invent numerical scores.

FINAL RULE:

NO CODE OR CONFIGURATION MAY BE MODIFIED.
I would run them exactly this way

Don't give Cline all nine phases in one task.

Use:

Phase 0
   ↓
Review report
   ↓
Phase 1
   ↓
Review report
   ↓
Phase 2  ← MOST IMPORTANT
   ↓
Review report
   ↓
Phase 3
   ↓
Phase 4
   ↓
Phase 5
   ↓
Phase 6
   ↓
Phase 7
   ↓
Phase 8
   ↓
Phase 9