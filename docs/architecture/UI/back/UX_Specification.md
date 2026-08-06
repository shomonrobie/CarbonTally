# CarbonTally Customer Portal UI/UX Specification
## Version 2.0
### Optimized User Experience for Mid-Market Companies (50–500 Employees)

---

# Design Philosophy

CarbonTally should feel like:

> **Dropbox + Stripe + Linear + Notion + Figma**

NOT

> Enterprise ERP software.

The platform should require almost no training.

Every screen should answer three questions:

1. What should I do?
2. What is happening?
3. What should I do next?

---

# User Roles

## Company Owner

Permissions

- Everything
- Billing
- Team Management
- Reports
- Approvals
- Company Settings

---

## Sustainability Manager

Permissions

- Upload data
- Review AI mapping
- Approve extracted data
- Generate reports
- Manage reporting periods

---

## Finance Manager

Permissions

- Upload invoices
- Upload CSV
- View calculations
- Download reports

---

## Procurement Officer

Permissions

- Upload supplier invoices
- Upload purchasing data
- Edit extracted information

---

## Operations Manager

Permissions

- Upload fuel logs
- Upload transport data
- Upload utility bills

---

## Data Entry Staff

Permissions

- Manual data entry
- Edit own records
- Upload documents

---

## Read Only

Permissions

- Dashboard
- Reports
- Audit logs

---

# Dashboard

Should resemble modern SaaS dashboards.

------------------------------------------------

TOP HEADER

------------------------------------------------

CarbonTally Logo

Workspace

Reporting Period

Global Search

Notifications

User Avatar

------------------------------------------------

LEFT SIDEBAR

------------------------------------------------

🏠 Dashboard

📁 Documents

📤 Upload Data

📊 Reports

📈 Emissions

📝 Manual Entry

✅ Validation Queue

📂 Extracted Data

👥 Team

⚙ Settings

❓ Help

---

# Dashboard Layout

------------------------------------------------

Top Statistics

------------------------------------------------

Total Emissions

Scope 1

Scope 2

Scope 3

Pending Validation

Documents Processing

Approval Required

Last Upload

------------------------------------------------

Second Row

------------------------------------------------

Recent Activity Timeline

Processing Queue

Notifications

Upcoming Deadlines

------------------------------------------------

Third Row

------------------------------------------------

Carbon Trend Chart

Top Emission Categories

Recent Uploads

Recent Reports

---

# Upload Center

This becomes the main page.

Large centered upload area.

------------------------------------------------

Upload Data

------------------------------------------------

Choose how you want to submit data

[ Upload CSV ]

[ Upload Excel ]

[ Upload PDF ]

[ Upload Images ]

[ Manual Entry ]

[ Request Managed Service ]

---

After selecting upload

Wizard opens.

Step 1

Upload

↓

Step 2

Preview

↓

Step 3

AI Processing

↓

Step 4

Review

↓

Step 5

Calculate

↓

Step 6

Report

---

# CSV Upload UI

Very similar to Airtable.

Top

Upload Status

Progress Bar

Rows Detected

Columns Detected

Estimated Processing Time

---

Center

Spreadsheet Preview

Rows

Columns

Filtering

Sorting

Search

---

Bottom

Buttons

Cancel

Continue

---

# AI Mapping Screen

Very important screen.

Layout

------------------------------------------------

LEFT

------------------------------------------------

Imported Data

Spreadsheet

------------------------------------------------

RIGHT

------------------------------------------------

Suggested Mapping

Confidence %

Emission Factor

Reason

Status

Accept

Reject

Edit

---

Green

95-100%

Auto Approved

Yellow

70-95%

Review

Red

Below 70%

Needs User Attention

---

Bulk Actions

Accept All

Reject All

Auto Correct

Search Factor

---

# PDF Review Screen

This is your killer feature.

Split Screen

------------------------------------------------

LEFT 45%

------------------------------------------------

PDF Viewer

Zoom

Rotate

Search

Highlight

Thumbnail Pages

---

RIGHT 55%

------------------------------------------------

Editable Table

Supplier

Date

Description

Amount

Unit

Activity

Emission Factor

Confidence

---

Every row has

Edit

Delete

Approve

Reject

Comment

---

If user edits

Difference highlighted.

Audit log created automatically.

---

# Managed Service Workflow

Customer uploads documents.

Status appears like parcel tracking.

Uploaded

↓

Assigned

↓

AI Extraction

↓

Operator Review

↓

Senior Validation

↓

Ready for Customer

↓

Customer Review

↓

Approved

↓

Carbon Calculated

Each stage has

Date

Time

Assigned Person

Completion %

---

# Validation Queue

Looks like Gmail inbox.

Rows

Document

Status

Confidence

Assigned Staff

Waiting Days

Priority

Buttons

Open

Approve

Reject

Comment

---

# Customer Review Screen

Large comparison interface.

------------------------------------------------

LEFT

------------------------------------------------

Original Document

---

RIGHT

------------------------------------------------

Extracted Data

---

BOTTOM

Approve

Reject

Request Changes

Comment

Download CSV

Calculate Carbon

---

# Manual Data Entry

Tabbed interface.

Tabs

Fuel

Electricity

Water

Waste

Transport

Flights

Hotels

Purchases

Other

Every tab

Looks like a clean accounting form.

---

# Carbon Dashboard

Beautiful charts.

Cards

Total Carbon

Monthly

Yearly

YTD

Scope 1

Scope 2

Scope 3

---

Charts

Monthly Trend

Emission Categories

Top Suppliers

Top Facilities

Top Departments

Carbon by Country

---

# Reports

Cards

Generate Report

↓

Choose

Reporting Period

↓

Choose

Report Type

↓

Generate

↓

Preview

↓

Download

Report Types

Management

DEFRA

CSRD

ESRS

Scope Summary

Audit Pack

CSV

---

# Notifications

Bell Icon

Grouped

Uploads

Validation

Reports

Team

System

---

# Search

Global Search

Search

Supplier

Invoice

Emission Factor

User

Document

Report

---

# Team Management

Cards

Users

Departments

Permissions

Invitations

Activity

---

# Settings

Company

Users

Emission Factors

Notifications

Security

Billing

Integrations

---

# Mobile UX

Dashboard

Upload

Notifications

Approvals

Reports

Everything else desktop only.

---

# UX Principles

## Never show empty pages

Always show

Example

Tutorial

Upload Button

---

## Maximum 3 clicks

Every major action

≤3 clicks

---

## Autosave Everything

Never lose data.

---

## Undo

Available everywhere.

---

## Keyboard Shortcuts

Power users.

---

## Bulk Actions

Never edit row by row.

---

## Progress Indicators

Every upload

Every calculation

Every extraction

Every report

---

## Confidence Indicators

Green

High confidence

Yellow

Needs review

Red

Manual intervention

---

## Human-Centered AI

Never hide AI decisions.

Always show

Why mapped

Confidence

Source

Factor

Editable

---

# Recommended Technology

Frontend

- React
- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Table
- React Hook Form
- Zustand
- React Query

UI Components

- Resizable split panes
- Virtualized data tables
- Drag-and-drop uploads
- Inline editing
- Keyboard navigation
- Command palette (Ctrl/Cmd + K)
- Toast notifications
- Timeline components
- Advanced filters
- Audit history drawer

---

# Overall User Journey

Login

↓

Dashboard

↓

Upload Data

↓

AI Extraction

↓

Review & Correct

↓

Approve

↓

Calculate Emissions

↓

Review Results

↓

Generate Reports

↓

Download Audit-Ready Outputs

Additional recommendation

I would add three major UX features that would make CarbonTally stand out from most competitors:

Unified Inbox – one queue showing all items requiring attention (new uploads, low-confidence mappings, managed-service reviews, approvals, failed imports, and completed reports) instead of forcing users to visit multiple pages.
Command Palette (Ctrl/Cmd + K) – similar to Linear or Notion, allowing users to instantly search for documents, suppliers, reports, emission factors, team members, or actions from anywhere in the application.
Workspace Home – each reporting period (e.g., FY2026) becomes a workspace displaying upload progress, percentage of emissions calculated, pending approvals, document completeness, and report readiness. This gives customers a clear sense of progress toward completing their carbon reporting rather than just a collection of uploaded files