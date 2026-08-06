ARCHITECTURE_DECISIONS.md
CarbonTally Architecture Decision Records (ADRs)
Version: v1.0.0
Last Updated: 31/09/2026
Status: ✅ APPROVED - FROZEN

Overview
This document records all major architectural decisions made during the design of CarbonTally v1.0. Each ADR captures the context, decision, consequences, and alternatives considered.

Purpose: To maintain architectural coherence as the platform evolves and to provide clear rationale for future developers and AI assistants.

ADR-001: No Separate Consultants Table
Status: ✅ Accepted

Date: Current Date

Category: Identity & Access

Context
CarbonTally needs to support multiple user types: platform staff, organization members, and consultants. Consultants are users who need access to multiple client organizations simultaneously.

The question arose whether consultants should be modeled as a separate entity type or as users with special access patterns.

Decision
Do NOT create a separate consultants table.

Consultants are modeled as regular users with:

Multiple entries in organization_access (one per client organization)

access_type = 'consultant' in organization_access

workspace_access to the client workspace

Standard role assignments (same roles as organization members)

Consequences
Positive:

Single user model for all personas

No data duplication between users and consultants

Users can seamlessly transition between roles (e.g., consultant → organization admin)

Simpler permission model

Unified authentication and session management

Reduced maintenance overhead

Negative:

Slightly more complex queries to identify consultants (need to count organization_access entries)

Alternatives Considered
Alternative 1: Separate consultants table with its own fields

Rejected due to data duplication and role inflexibility

Alternative 2: consultants as a view on users

Rejected because it adds complexity without benefit

Example
sql
-- John is a consultant. He has:
INSERT INTO users (id, email, first_name, last_name) 
VALUES ('123', 'john@consultancy.com', 'John', 'Smith');

-- Access to multiple organizations
INSERT INTO organization_access (user_id, organization_id, workspace_id, role_id, access_type)
VALUES 
  ('123', 'abc-org', 'client-workspace', 'consultant-role', 'consultant'),
  ('123', 'xyz-org', 'client-workspace', 'consultant-role', 'consultant'),
  ('123', 'green-org', 'client-workspace', 'consultant-role', 'consultant');

-- Find all consultants
SELECT u.*, COUNT(oa.organization_id) as org_count
FROM users u
JOIN organization_access oa ON oa.user_id = u.id
WHERE oa.access_type = 'consultant'
GROUP BY u.id
HAVING COUNT(oa.organization_id) > 1;
ADR-002: Consultants Use Organization Access, Not Ownership
Status: ✅ Accepted

Date: Current Date

Category: Identity & Access, Organization Management

Context
When consultants work with client organizations, they need access to client data. The question is whether consultants should "own" the organizations they work with or simply have access to them.

Decision
Consultants do NOT own organizations.

Consultants are granted organization_access with access_type = 'consultant'. They never appear as the creator/owner of an organization.

Ownership remains with:

The organization itself (self-owned)

Platform staff (for platform-created organizations)

The primary contact/user who created the organization

Consequences
Positive:

Clear ownership model - organizations always have a single owner

Consultants can be easily added/removed without affecting ownership

Data ownership remains with the organization, not temporary consultants

Audit logs clearly distinguish between owners and consultants

Negative:

Need to track which access entries are "consultant" vs "member" vs "owner"

Alternatives Considered
Alternative 1: Consultants own organizations they create/join

Rejected because consultants shouldn't own client data

Alternative 2: Add is_owner boolean to organization_access

Rejected because it mixes ownership with access - ownership is a special case of access

Implementation
sql
-- Organization access types
access_type VARCHAR -- 'owner', 'member', 'consultant', 'platform'

-- Owner access (organization creator)
INSERT INTO organization_access (user_id, organization_id, access_type)
VALUES ('456', 'abc-org', 'owner');

-- Consultant access (no ownership)
INSERT INTO organization_access (user_id, organization_id, access_type)
VALUES ('123', 'abc-org', 'consultant');
ADR-003: Every Upload is a Document
Status: ✅ Accepted

Date: Current Date

Category: Document Management

Context
CarbonTally receives various file types:

PDF invoices and utility bills

CSV/Excel emissions data

Images of physical documents

Email attachments

Scanned documents

API-uploaded data

Each file type has different processing requirements and lifecycle stages.

Decision
ALL uploaded files are modeled as documents, regardless of type or source.

The documents table captures:

Core file metadata (name, size, mime_type, storage_path)

Status and version

Processing pipeline tracking

Review and approval workflow

Links to organization, supplier, and other entities

Consequences
Positive:

Single document lifecycle model

Consistent tracking and auditing

Easy to add new document types

Unified search and retrieval

Clear version history

Consistent review/approval workflow

Negative:

Some fields may be irrelevant for certain document types (e.g., supplier_id for non-supplier documents)

Need to handle nullable foreign keys

Document Lifecycle
text
Uploaded → Processing → Processed → Reviewed → Approved → Archived
  ↓           ↓            ↓          ↓          ↓          ↓
 Upload    OCR/AI      Data       Human     Final     Long-term
  Queue    Extraction  Mapping    Review    Sign-off  Storage
Example
sql
-- A utility bill from a supplier
INSERT INTO documents (
    id, organization_id, supplier_id, 
    name, file_name, file_size, 
    mime_type, storage_path, status
) VALUES (
    'doc-123', 'abc-org', 'supplier-456',
    'Electricity Bill - Jan 2026', 'electricity_jan2026.pdf', 245000,
    'application/pdf', 'uploads/abc-org/electricity_jan2026.pdf', 'uploaded'
);

-- An emissions data CSV
INSERT INTO documents (
    id, organization_id,
    name, file_name, file_size,
    mime_type, storage_path, status
) VALUES (
    'doc-456', 'abc-org',
    'Scope 2 Emissions Q1 2026', 'scope2_q1_2026.csv', 15000,
    'text/csv', 'uploads/abc-org/scope2_q1_2026.csv', 'uploaded'
);
ADR-004: Workspaces Are Role-Based, Not Separate Applications
Status: ✅ Accepted

Date: Current Date

Category: Workspace Architecture

Context
CarbonTally has three distinct user experiences:

Platform Staff (admin, analytics, validation)

Organization Members (dashboard, documents, suppliers)

Consultants (similar to Organization Members, but with org switching)

The question is whether these should be separate applications or role-based views of the same application.

Decision
Workspaces determine UI context. All users use the same application codebase.

Workspace Types:

Platform Workspace (platform): Admin tools, analytics, validation queue

Client Workspace (client): Dashboard, documents, suppliers, reports

Data Access is controlled by organization_access, not by workspace.

Consequences
Positive:

Single codebase - less maintenance

Consistent user experience

Users can have access to both workspaces

No context switching between applications

Easier to add new workspaces in the future

Negative:

Need conditional UI rendering based on workspace

Some components may need workspace-aware logic

Workspace Access Patterns
User Type	Workspace	Organization Access
Platform Staff	platform	All organizations (platform view)
Organization Admin	client	Single organization (own org)
Consultant	client	Multiple organizations (client orgs)
Implementation
sql
-- Workspace definitions
INSERT INTO workspaces (id, name, code, description) VALUES
    ('ws-1', 'Platform Workspace', 'platform', 'Internal platform staff'),
    ('ws-2', 'Client Workspace', 'client', 'Organization dashboard');

-- Access control
organization_access.user_id = current_user
organization_access.organization_id = filtered_by_org
workspace_access.workspace_id = determines_ui
ADR-005: Supplier Portal Deferred to Future Release
Status: ✅ Accepted

Date: Current Date

Category: Supplier Management

Context
CarbonTally v1.0 requires supplier management capabilities, including tracking supplier information, contacts, and emissions data.

The question is whether suppliers themselves should be able to log in and manage their data in v1.0.

Decision
Supplier portal functionality is deferred to a future release (v2.0 or later).

v1.0 includes:

suppliers table (core supplier management)

supplier_contacts, supplier_addresses, supplier_categories

supplier_emissions, supplier_spend, supplier_documents

Supplier data entry by organization admins and consultants

v2.0 will add:

supplier_portal_users table

Supplier login functionality

Supplier self-service data management

Supplier emissions submission

Consequences
Positive:

v1.0 is simpler and faster to deliver

Can design supplier portal with real user feedback

Supplier data collection is handled manually, reducing integration complexity

Lower initial security surface area

Negative:

Suppliers cannot self-manage their data in v1.0

Organization admins/consultants need to enter supplier data

No direct supplier verification in v1.0

Implementation
sql
-- v1.0 supplier tables
suppliers, supplier_contacts, supplier_addresses, 
supplier_categories, supplier_documents, supplier_emissions, supplier_spend

-- v2.0 future addition
supplier_portal_users (currently NOT in schema)
ADR-006: PostgreSQL Sufficient for v1.0 Reporting
Status: ✅ Accepted

Date: Current Date

Category: Reporting & Analytics

Context
CarbonTally needs reporting capabilities for emissions data, compliance reporting (SECR, ESRS, ISSB), and custom reports.

The question is whether to build a data warehouse/OLAP structure or use PostgreSQL for reporting.

Decision
Use PostgreSQL for v1.0 reporting.

Leverage PostgreSQL views, materialized views, and query optimization

Apply appropriate indexing for reporting queries

Use aggregations and window functions for complex reporting

Consider data warehouse at >10,000 organizations or >10M emissions logs

Consequences
Positive:

Lower initial complexity

Operational simplicity (one database)

Direct access to current data

Faster time-to-market

No ETL pipelines needed

Negative:

May become slow at very large scale

Limited OLAP features

Historical data may need archiving

Implementation Strategy
Create useful views for common reporting patterns

Add indexes for reporting queries

Use pg_cron or similar for pre-aggregation if needed

Monitor performance and scale up (vertically) before considering warehouse

Trigger Conditions for Data Warehouse
10,000 active organizations

10M emission calculation records

Query performance degrades below acceptable levels

Complex multi-dimensional analysis required

ADR-007: Common Base Fields for All Core Tables
Status: ✅ Accepted

Date: Current Date

Category: Data Modeling

Context
As CarbonTally grows, maintaining consistency across tables becomes critical for maintainability, auditing, and developer productivity.

The question is whether to standardize on a common field pattern.

Decision
All core tables implement a standard set of base fields:

sql
-- Common base fields (in every core table)
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
organization_id UUID REFERENCES organizations(id)  -- NULL for global entities
created_by UUID REFERENCES users(id)
updated_by UUID REFERENCES users(id)
created_at TIMESTAMPTZ DEFAULT NOW()
updated_at TIMESTAMPTZ DEFAULT NOW()
deleted_at TIMESTAMPTZ NULL  -- Soft delete
metadata JSONB  -- Future extensibility
status VARCHAR DEFAULT 'active'
Consequences
Positive:

Consistent querying patterns

Built-in audit trail (created_by, updated_by)

Soft delete capability

Future-proofing with metadata JSONB

Easy to generate/maintain code

Consistent indexing strategy

Negative:

More columns than strictly necessary for some tables

Slight overhead for tables that don't need all fields

Tables That Follow This Pattern
✅ All Domain tables:

organizations, facilities, departments, teams

suppliers, supplier_contacts, supplier_addresses

documents, document_versions, document_reviews

reports, report_templates

messages, conversations, notifications

tasks, support_tickets

Exception: Tables that are inherently tied to another table (e.g., document_processing only exists with a document_id).

ADR-008: Client Workspace is the Default Workspace
Status: ✅ Accepted

Date: Current Date

Category: Workspace Architecture

Context
Users in CarbonTally may have access to multiple workspaces. The primary workspace for organization members and consultants is the client workspace.

The question is how to handle workspace selection and defaults.

Decision
Client Workspace is the default workspace for all non-platform users.

Platform staff explicitly choose Platform Workspace via workspace_access

All other users default to Client Workspace

Users with access to both workspaces can switch

Workspace context is stored in the session or token

Consequences
Positive:

Most users see the client workspace by default (their primary interface)

Clean separation of platform and client concerns

Consistent user experience

Negative:

Platform staff must explicitly switch to Platform Workspace

Need to handle workspace switching in the UI

Workspace Selection Flow
text
User Login
    ↓
Check workspace_access
    ↓
┌─────────────────────┬─────────────────────┐
│ Multiple Workspaces │ Single Workspace    │
│   Show switcher     │   Auto-select       │
│   in navigation     │   Enter workspace   │
└─────────────────────┴─────────────────────┘
ADR-009: Organization Access is the Single Source of Truth for Tenancy
Status: ✅ Accepted

Date: Current Date

Category: Multi-tenant Architecture

Context
CarbonTally is a multi-tenant SaaS platform. Data isolation must be enforced across all tables.

The question is how to reliably determine which organizations a user can access.

Decision
organization_access is the single source of truth for tenant membership.

All RLS policies use organization_access to determine data visibility.

No other tables are used to determine organization membership:

organization_members is a view or legacy compatibility table

user_roles does not imply organization access

workspace_access does not imply organization access

Consequences
Positive:

Single source of truth - no conflicting data

Consistent enforcement across all tables

Easy to audit access

Easy to add/remove organization access

Negative:

All authorization queries must join to organization_access

Need to maintain this table carefully

Implementation
sql
-- RLS policy example
CREATE POLICY "Users can view their own organization's suppliers"
ON suppliers
FOR SELECT
USING (
    organization_id IN (
        SELECT organization_id 
        FROM organization_access 
        WHERE user_id = auth.uid() 
        AND is_active = true
    )
);
ADR-010: Feature Flags Enable Gradual Rollouts
Status: ✅ Accepted

Date: Current Date

Category: Platform Administration

Context
As CarbonTally evolves, new features need to be tested and rolled out gradually. Beta features should be invisible to most users.

Decision
Implement a feature flag system in Domain 9 (Platform Administration).

sql
feature_flags (
    id UUID PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    code VARCHAR UNIQUE NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT FALSE,
    enabled_for_organizations UUID[],  -- Specific orgs
    enabled_for_users UUID[],          -- Specific users
    rollout_percentage INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
Consequences
Positive:

Safe feature rollouts

Beta testing with specific users/organizations

A/B testing capability

Hot enable/disable features without deployment

Canary releases

Negative:

Additional complexity

Need to check flags in code

Feature flag debt (flags that never get removed)

Usage Example
typescript
// Check if feature is enabled
const isFeatureEnabled = async (userId: string, featureCode: string) => {
    const feature = await getFeatureFlag(featureCode);
    if (!feature.is_enabled) return false;
    
    // Check user-specific enablement
    if (feature.enabled_for_users.includes(userId)) return true;
    
    // Check percentage rollout
    if (hash(userId) % 100 < feature.rollout_percentage) return true;
    
    return false;
};
ADR-011: Audit Logging is Non-Negotiable
Status: ✅ Accepted

Date: Current Date

Category: Security & Compliance

Context
CarbonTally handles sensitive carbon emissions data that may be subject to regulatory requirements (SECR, ESRS, etc.). Audit trails are necessary for compliance.

Decision
Every state-changing operation must be logged in audit_logs.

audit_logs captures:

Who performed the action (user_id, organization_id)

What was changed (action_type, resource_type, resource_id)

Before/after values (old_data, new_data, changes)

When (created_at)

Where (ip_address, user_agent)

Why (description, metadata)

Consequences
Positive:

Full audit trail for compliance

Ability to reconstruct any change

Security incident investigation

User accountability

Negative:

Additional storage overhead

Write performance impact

Need to audit the audit logs

Implementation
sql
-- Every state-changing operation
INSERT INTO audit_logs (
    user_id, organization_id,
    action_type, resource_type, resource_id,
    old_data, new_data, changes,
    ip_address, user_agent, description
) VALUES (
    current_user,
    current_org,
    'UPDATE',
    'document',
    document_id,
    old_document_data,
    new_document_data,
    jsonb_build_object('status', old_status, 'new_status', new_status),
    current_ip,
    current_user_agent,
    'Document status changed from ' || old_status || ' to ' || new_status
);
ADR-012: Soft Delete Instead of Hard Delete
Status: ✅ Accepted

Date: Current Date

Category: Data Management

Context
Data in CarbonTally has compliance and audit implications. Deleting data permanently may be problematic for regulatory requirements.

Decision
Use soft delete (deleted_at timestamp) instead of hard delete.

All core tables include a deleted_at timestamp field. Records with deleted_at IS NOT NULL are considered deleted.

Consequences
Positive:

Data can be recovered if accidentally deleted

Audit trail of deletions

Compliance with data retention requirements

Graceful cleanup (can permanently delete after retention period)

Negative:

Additional storage overhead

Need to filter out deleted records in queries

Potential for data leakage if not filtered properly

Implementation
sql
-- Soft delete
UPDATE documents SET deleted_at = NOW() WHERE id = 'doc-123';

-- Query that excludes deleted records
SELECT * FROM documents WHERE deleted_at IS NULL;

-- RLS policy with soft delete
CREATE POLICY "Users can view their own documents"
ON documents
FOR SELECT
USING (
    organization_id IN (SELECT organization_id FROM organization_access WHERE user_id = auth.uid())
    AND deleted_at IS NULL
);
ADR-013: No Data Warehouse in v1.0
Status: ✅ Accepted

Date: Current Date

Category: Reporting & Analytics

Context
See ADR-006 for the full context. This ADR specifically confirms that data warehouse/OLAP is NOT in scope for v1.0.

Decision
Do NOT implement a data warehouse in v1.0.

Scope
Feature	v1.0	v2.0+
PostgreSQL reporting views	✅	✅
Pre-aggregated tables	❌	✅
Data warehouse	❌	✅
OLAP cubes	❌	✅
ETL pipelines	❌	✅
Justification
v1.0 needs to launch quickly

PostgreSQL can handle expected initial scale

Simpler architecture means faster iteration

Can add warehouse when business need is proven

ADR-014: Organization Access is the Core Permission Table
Status: ✅ Accepted

Date: Current Date

Category: Identity & Access

Context
Permissions in CarbonTally are complex:

Users have roles (platform, organization, consultant)

Roles have permissions

Permissions apply within workspaces

Organization access determines data visibility

Decision
organization_access is the core table that ties everything together.

text
User
  ↓
user_roles (What roles does this user have?)
  ↓
role_permissions (What can these roles do?)
  ↓
workspace_access (In which workspace?)
  ↓
organization_access (With which organizations?)
  ↓
Data Access (Actual data)
Consequences
Positive:

Single table for access control

Clear permission hierarchy

Easy to audit

Flexible role assignments

Negative:

More complex initial setup

Need to understand the full permission model

Permission Hierarchy Diagram
text
┌─────────────────────────────────────────────────────────────┐
│                       PERMISSIONS                           │
│                 (Atomic actions)                           │
│  documents.view, emissions.create, suppliers.update         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    PERMISSION GROUPS                        │
│              (Logical collections)                         │
│  Document Management, Supplier Management, Reporting        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         ROLES                               │
│          (Named permission sets)                           │
│  Organization Admin, Sustainability Manager, Consultant    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     USER ROLES                              │
│           (What roles does a user have)                    │
│  user_id = '123' + role_id = 'consultant'                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    WORKSPACE ACCESS                         │
│           (In which workspace?)                            │
│  user_id = '123' + workspace_id = 'client'                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  ORGANIZATION ACCESS                        │
│        (With which organizations?)                         │
│  user_id = '123' + org_id = 'ABC' (consultant)             │
│  user_id = '123' + org_id = 'XYZ' (consultant)             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       DATA ACCESS                           │
│              (Actual data filtering)                       │
│  WHERE organization_id IN (user's organization_access)     │
└─────────────────────────────────────────────────────────────┘
ADR-015: No Separate Departments for v1.0 (Optional)
Status: ✅ Accepted (Optional)

Date: Current Date

Category: Organization Management

Context
CarbonTally v1.0 includes facilities as organizational units. The question is whether departments and teams are needed in v1.0.

Decision
Include departments and teams tables, but mark as optional/inactive in v1.0.

Tables exist in the schema

UI for departments/teams is hidden or minimal in v1.0

Full implementation deferred to v1.1 or v2.0

Consequences
Positive:

Schema is ready for future expansion

No migration needed when departments are enabled

Can seed basic departments if needed

Negative:

Additional tables in the schema that aren't used in v1.0

Implementation
sql
-- Tables exist in schema
departments, teams

-- v1.0: minimal UI, optional features
-- v1.1+: full department/team management
ADR-016: Billing & Subscription Deferred to v2.0
Status: ✅ Accepted

Date: Current Date

Category: Billing & Subscription

Context
CarbonTally needs a billing and subscription model, but it's not required for initial launch.

Decision
Billing & Subscription tables are designed but not implemented in v1.0.

Tables exist in the schema (Domain 10) for future reference

No subscription enforcement in v1.0

Manual billing process for initial customers

Subscription implementation deferred to v2.0

Consequences
Positive:

v1.0 launches faster

Can build billing based on real customer feedback

No payment provider integration needed initially

Negative:

Manual billing is inefficient

No automated subscription management

Need to migrate to subscription system later

ADR-017: Role-Based Access Control (RBAC) Over Attribute-Based Access Control (ABAC)
Status: ✅ Accepted

Date: Current Date

Category: Identity & Access

Context
CarbonTally needs to control access to resources. Two main approaches: Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC).

Decision
Use RBAC (Role-Based Access Control) for CarbonTally v1.0.

Why RBAC?
Simplicity: Easier to understand and implement

Predictability: Users know what a role gives them

Performance: Faster than ABAC (no attribute evaluation)

Industry standard: Well understood by teams

Sufficient: CarbonTally's needs are role-based

Why Not ABAC?
Complexity: ABAC requires evaluating dynamic attributes

Performance: Slower than RBAC (more computation)

Overkill: CarbonTally doesn't need attribute-level granularity yet

Unknown attributes: We don't know what attributes might matter

Migration Path
text
v1.0: RBAC (roles + permissions)
    ↓
v1.5: Hybrid (RBAC + limited ABAC for special cases)
    ↓
v2.0+: Full ABAC if needed
ADR-018: Consultant Workspace is a Capability, Not a Workspace
Status: ✅ Accepted

Date: Current Date

Category: Workspace Architecture

Context
The original design had three workspaces: Platform, Consultant, and Organization.

The refined design has two workspaces: Platform and Client.

Decision
Consultant access is a CAPABILITY, not a separate workspace.

Consultants use the Client Workspace but with:

Multiple organization_access entries

Organization switcher in the UI

Same UI as organization members

Consequences
Positive:

Single client workspace codebase

Consultants see exactly what org members see

No duplicate UI development

Consistent user experience

Negative:

Need to conditionally show organization switcher

Need to handle "workspace with multiple orgs" state

Implementation
sql
-- Consultants are identified by:
-- 1. Multiple organization_access entries
-- 2. access_type = 'consultant'
-- 3. workspace_access to 'client' workspace

-- UI logic
if (user.organization_access.length > 1) {
    showOrganizationSwitcher();
} else {
    // Single organization, no switcher needed
}
ADR-019: Metadata JSONB for Future Extensibility
Status: ✅ Accepted

Date: Current Date

Category: Data Modeling

Context
CarbonTally's requirements will evolve. New fields will be needed without schema migrations.

Decision
All core tables include a metadata JSONB field.

Consequences
Positive:

Add new fields without schema changes

Store custom/client-specific data

Future-proof the schema

Reduce migration frequency

Negative:

JSONB fields are less performant than typed columns

No schema validation (can store anything)

Need to document what's in metadata

Usage Guidelines
Use typed columns for fields that are:

Always required

Used in queries (WHERE, JOIN, ORDER BY)

Used in indexes

Business-critical

Use metadata JSONB for fields that are:

Optional

Rarely queried

Client-specific

Experimental

Likely to change

Example
sql
-- Typed columns (always needed, always queried)
name VARCHAR NOT NULL,
email VARCHAR NOT NULL,
created_at TIMESTAMPTZ DEFAULT NOW()

-- Metadata (optional, rarely queried)
metadata JSONB DEFAULT '{}'::jsonb
-- Example: { "preferred_contact_method": "email", "internal_notes": "Important client" }
ADR-020: Migration Strategy - Evolve, Don't Rewrite
Status: ✅ Accepted

Date: Current Date

Category: Migration Strategy

Context
CarbonTally has an existing database schema. The Phase 1 audit identified areas for improvement.

Decision
Evolve the schema progressively. Do NOT rewrite from scratch.

Strategy
Phase 2A: Add new tables (Identity & Access layer)

Phase 2B: Migrate existing data to new structure

Phase 2C: Deprecate old tables

Phase 2D: Remove deprecated tables (post-migration)

Key Principles
Backward compatibility: Old code continues to work during migration

Data preservation: No data loss

Incremental: Small steps, not one big migration

Rollback capability: Can revert if issues arise

Migration Order
text
1. Create new tables (Identity & Access)
2. Copy user/role data to new tables
3. Update application to use new tables
4. Create organization_access table
5. Migrate organization memberships
6. Update RLS policies to use organization_access
7. Remove old tables (organization_members, etc.)
ADR Summary Table
ADR	Decision	Status
ADR-001	No separate consultants table	✅ Accepted
ADR-002	Consultants use organization access, not ownership	✅ Accepted
ADR-003	Every upload is a document	✅ Accepted
ADR-004	Workspaces are role-based, not separate applications	✅ Accepted
ADR-005	Supplier portal deferred to future release	✅ Accepted
ADR-006	PostgreSQL sufficient for v1.0 reporting	✅ Accepted
ADR-007	Common base fields for all core tables	✅ Accepted
ADR-008	Client Workspace is the default workspace	✅ Accepted
ADR-009	Organization Access is the single source of truth for tenancy	✅ Accepted
ADR-010	Feature flags enable gradual rollouts	✅ Accepted
ADR-011	Audit logging is non-negotiable	✅ Accepted
ADR-012	Soft delete instead of hard delete	✅ Accepted
ADR-013	No data warehouse in v1.0	✅ Accepted
ADR-014	Organization Access is the core permission table	✅ Accepted
ADR-015	No separate departments for v1.0 (optional)	✅ Accepted
ADR-016	Billing & subscription deferred to v2.0	✅ Accepted
ADR-017	RBAC over ABAC	✅ Accepted
ADR-018	Consultant workspace is a capability, not a workspace	✅ Accepted
ADR-019	Metadata JSONB for future extensibility	✅ Accepted
ADR-020	Migration strategy - evolve, don't rewrite	✅ Accepted
Version History
Version	Date	Changes	Author
1.0.0	31/09/2026	Initial creation of all ADRs	Chief Database Architect
Document Control: This document is the source of truth for architectural decisions. Any changes must be reviewed and approved before implementation.

Next Review: After Phase 2 implementation, or when significant new requirements emerge.

