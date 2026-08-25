# CarbonTally Blog CMS — Product & Architecture Decisions

**Status:** RATIFIED  
**Date:** 2026-08-23  
**Purpose:** Permanent reference for the CarbonTally Blog CMS  
**Development model:** Standalone development → later CarbonTally integration

---

## 1. Purpose

CarbonTally will have a professional public Blog and an internal Blog Management Dashboard.

The Blog is a content-management subsystem.

It is not part of the carbon-processing engine.

Its purpose is to:

- educate customers
- establish CarbonTally expertise
- support SEO
- explain carbon data management
- explain emission factors
- explain evidence traceability
- explain document processing
- publish research and technical content
- publish industry content
- publish customer/consultant case studies
- support CarbonTally's B2B positioning

---

# 2. Product Positioning

CarbonTally's blog should reinforce the company's positioning as:

> A carbon data management and carbon data processing platform.

The content should focus on:

- messy carbon data
- data processing
- extraction
- mapping
- emission factors
- calculations
- validation
- evidence
- provenance
- manual data processing
- human-in-the-loop processing
- carbon data infrastructure

The Blog should not reposition CarbonTally as primarily a carbon-reporting software product.

---

# 3. Technology Stack

The Blog CMS uses the CarbonTally technology ecosystem.

### Frontend

React + JavaScript + JSX.

No TypeScript.

No `.ts`.

No `.tsx`.

### Authentication

Supabase Auth.

### Database

Supabase PostgreSQL.

### Storage

Supabase Storage.

### Email

Resend.

### Frontend hosting

Vercel.

### Backend/API hosting

Render.

---

# 4. Database Strategy

The Blog will eventually live in the SAME production Supabase/PostgreSQL database as CarbonTally.

A separate production database is not required.

The Blog tables will be isolated through:

- `blog_` table naming
- separate RLS policies
- separate storage bucket
- separate APIs
- separate frontend routes
- clear domain boundaries

The Blog must not modify CarbonTally operational data unnecessarily.

---

# 5. Blog Tables

Initial schema:

- `blog_authors`
- `blog_categories`
- `blog_tags`
- `blog_posts`
- `blog_post_categories`
- `blog_post_tags`
- `blog_post_revisions`
- `blog_media`
- `blog_comments`
- `blog_subscribers`

No `blog_users` table.

---

# 6. Authentication Decision

The Blog will NOT have its own user/authentication system.

Supabase Auth is the authentication authority.

When integrated into CarbonTally:

CarbonTally Supabase Auth
→ authenticated identity
→ CarbonTally authorization
→ Blog capability authorization

A separate Blog password database must never be introduced.

---

# 7. Author Model

`blog_authors` represents content authorship, not authentication.

An author can be:

- CarbonTally employee
- consultant
- customer
- invited industry expert
- organization
- AI/content identity

`blog_authors.user_id` is therefore nullable.

Examples:

### Internal author

Supabase user
→ CarbonTally user
→ blog author

### Consultant author

Supabase user
→ consultant
→ blog author

### Customer author

Supabase user
→ customer
→ blog author

### External guest author

No CarbonTally user
→ blog author with `user_id = NULL`

---

# 8. Blog Permission Model

A CarbonTally actor role does NOT automatically grant Blog permissions.

Blog permissions are explicit capabilities:

- `blog_author`
- `blog_writer`
- `blog_editor`
- `blog_publisher`
- `blog_admin`

This prevents accidental publishing authority.

---

# 9. Actor Permissions

## CarbonTally Platform Staff

May be granted:

- writer
- editor
- publisher
- admin

depending on their responsibility.

## Consultants

May be explicitly invited as Blog writers.

They do not automatically receive Blog access.

## Customers

May be explicitly invited as guest writers.

They do not automatically receive Blog access.

## Processing Entity Staff

No Blog access by default.

They may be explicitly invited as guest writers if CarbonTally chooses.

---

# 10. Publishing Control

Only:

- `blog_publisher`
- `blog_admin`

can publish directly.

`blog_writer` can:

- create drafts
- edit permitted drafts
- submit for review

but cannot publish directly.

This provides editorial control.

---

# 11. Editorial Workflow

Recommended workflow:

Draft
→ Review
→ Scheduled
→ Published
→ Archived

A writer can submit content for review.

An editor can review and modify it.

A publisher/admin controls publication.

---

# 12. Revision Policy

Blog posts maintain revision history.

Restoring an old revision must create a new revision.

Historical revisions must never be silently destroyed.

---

# 13. Storage

Blog media uses a dedicated Supabase Storage bucket:

`blog-media`

It must remain separate from CarbonTally customer document/evidence storage.

Customer documents are private and organization-scoped.

Blog media is public website content and can use appropriate public/CDN delivery.

---

# 14. Email

Blog email uses Resend.

Potential functions:

- newsletter confirmation
- newsletter delivery
- unsubscribe
- comment notifications
- editorial notifications

No custom SMTP infrastructure.

---

# 15. Public Blog

Planned routes include:

`/blog`

`/blog/:slug`

`/blog/category/:slug`

`/blog/tag/:slug`

`/blog/author/:slug`

Only published content is publicly visible.

---

# 16. Admin Blog

Planned routes include:

`/admin/blog`

`/admin/blog/posts`

`/admin/blog/posts/new`

`/admin/blog/posts/:id`

`/admin/blog/categories`

`/admin/blog/tags`

`/admin/blog/authors`

`/admin/blog/media`

`/admin/blog/comments`

`/admin/blog/subscribers`

---

# 17. Content Areas

The CMS must support content relating to:

### Carbon Data

- carbon data management
- data quality
- normalization
- data pipelines

### Emission Factors

- DEFRA
- emission-factor selection
- units
- versions

### Evidence & Traceability

- source documents
- invoice-level emissions
- line-level emissions
- provenance
- audit evidence

### Data Processing

- PDF extraction
- invoice extraction
- Excel
- CSV
- JSON
- manual extraction
- human + automated processing

### Carbon Infrastructure

- APIs
- carbon data processing
- carbon platforms
- data providers

### Industry

- manufacturing
- retail
- logistics
- hospitality
- healthcare
- other industries

These are content categories, not hard-coded application behavior.

---

# 18. Security

Blog security must include:

- Supabase Auth
- RLS
- capability-based authorization
- private subscriber data
- protected revisions
- protected administration
- sanitized article content
- safe media upload
- comment moderation
- rate limiting where appropriate

Public users must never access:

- drafts
- revisions
- subscriber lists
- administrative APIs
- moderation tools

---

# 19. Integration Strategy

The Blog is initially developed in a separate repository.

Standalone development:

Qwen Blog CMS
→ local Supabase
→ local testing

Later:

Blog schema
→ reviewed
→ migrated into existing CarbonTally Supabase

Then:

Blog frontend/API
→ integrated into CarbonTally deployment

The standalone project must NOT modify CarbonTally during development.

---

# 20. Integration Constraint

The final integrated architecture should be:

```text
CarbonTally
│
├── Existing V3 application
│
├── Customer / Consultant / Operations / Entity domains
│
├── Carbon processing
│
├── Evidence & provenance
│
└── Blog CMS
      │
      ├── blog_posts
      ├── blog_authors
      ├── blog_categories
      ├── blog_tags
      ├── blog_revisions
      ├── blog_media
      ├── blog_comments
      └── blog_subscribers
```
No generic tenancy architecture is required.

# 21. Why Same Database

The Blog remains in the same Supabase database because:

it reduces operational complexity
one backup system is sufficient
one Supabase environment is easier to manage
Supabase Auth can be shared
Supabase Storage can be shared while using separate buckets
integration is simpler
operating cost is lower

The Blog remains logically separated despite sharing the database.

# 22. Why No Blog User Table

A separate blog_users table would duplicate authentication.

Supabase Auth already provides identity.

CarbonTally already has user/actor authorization.

The Blog only needs:

authenticated identity
Blog capability
optional blog_author profile

Therefore:

Authentication belongs to Supabase Auth.
Authorship belongs to blog_authors.
Blog permissions belong to Blog capabilities.

# 23. Guest Authors

Guest authors are supported.

A guest author can have:

blog_authors.user_id = NULL

They cannot access the CMS unless they are explicitly provided an authenticated CarbonTally account.

This allows public authorship without creating fake application users.

# 24. Marketing Strategy

The Blog should support CarbonTally's broader B2B strategy.

Potential audiences include:

companies managing carbon data
sustainability teams
consultants
carbon accounting platforms
carbon reporting providers
sustainability software companies
data-processing partners
industry professionals

The Blog should help explain why CarbonTally can operate as a data-processing infrastructure layer for other carbon platforms.

# 25. Future Integration Possibilities

Potential future features:

consultant-authored articles
customer case studies
industry expert guest posts
CarbonTally research
downloadable resources
gated content
newsletter campaigns
knowledge base
API documentation
service-specific landing pages

These are future capabilities and should not complicate the initial CMS.

# 26. Explicitly Not Required

The initial Blog CMS does NOT require:

separate production database
separate authentication system
TypeScript
custom SMTP
generic multi-tenancy
CarbonTally organization tenancy
carbon calculations
emission factors
document processing
customer data processing
processing-entity workflows

# 27. Final Architectural Principle

The CarbonTally Blog is an independent content domain inside the same platform infrastructure.

Its architecture is:

Supabase Auth → explicit Blog capabilities → Blog authorship → Blog content

not:

Blog → separate users → separate authentication → separate database

# 28. Current Status

Decision: RATIFIED

Standalone development: Approved

Production integration: NOT YET

Authentication: Supabase Auth

Database: Existing CarbonTally Supabase database after integration

Storage: Supabase Storage, dedicated blog-media bucket

Email: Resend

Frontend: React + JavaScript + JSX

Frontend hosting: Vercel

Backend: Render-compatible

Blog user table: NOT required

Blog capabilities: Required

Customer/consultant/entity automatic Blog access: NO

Explicit invitation/capability: YES

Direct publishing: Restricted to publisher/admin

Final principle

Anyone may be an author; not everyone is a publisher.

CarbonTally can eventually allow employees, consultants, customers, and invited experts to contribute content while retaining centralized editorial and publishing control.
      
