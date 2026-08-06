🤖 AI Prompt to Finish Remaining Modules
Standard Module Template
Copy and paste this prompt for each missing module, replacing [MODULE_NAME] with the specific module:

text
Based on the CarbonTally database schema and following the exact same standards and design patterns we used for previous modules (Dashboard, Documents, Upload Data, Reports Center, Emissions Reports, Manual Data Entry, Team Management, Roles & Permissions, Organization Metadata, Validation Queue, and Settings), please create a comprehensive interactive [MODULE_NAME] page with mock data.

## Design Requirements:
1. **Theme System**: Use the same 9-theme system (Forest, Emerald, Teal, Navy, Slate, Warm Grey, Purple, Rose, Carbon) with CSS variables and localStorage persistence
2. **shadcn/ui Components**: Use consistent components (btn, card, badge, avatar, input, select, tabs, switch, progress bar, modal)
3. **Layout**: Left sidebar navigation with the same structure, top header with search and theme toggle
4. **Responsive**: Full responsive design for desktop, tablet, and mobile
5. **Mock Data**: Include realistic mock data based on the actual database schema tables
6. **Interactivity**: Full CRUD operations (Create, Read, Update, Delete) with mock data
7. **Toast Notifications**: Use the same toast system for user feedback
8. **Schema Integration**: Map every feature to the actual database schema columns

## Database Schema Tables for [MODULE_NAME]:
[List the specific tables from the schema that this module uses]

## Key Features to Include:
[List the specific features based on the tables]

## Mock Data Requirements:
[Describe what mock data should look like]

## Interactions:
- [List specific user interactions]
- [List keyboard shortcuts]
- [List modal dialogs needed]

Please follow the exact same code structure, styling, and component patterns as all previous modules. Include comprehensive mock data that reflects real-world usage.
Example Prompts for Each Missing Module
1. Extracted Data Management Module
text
Based on the CarbonTally database schema and following the exact same standards and design patterns we used for previous modules, please create a comprehensive interactive Extracted Data Management page with mock data.

## Database Schema Tables:
- `draft_entries`: id, file_id, organization_id, user_id, data (jsonb), progress, sections_completed, last_updated
- `customer_documents`: id, organization_id, organization_member_id, asset_id, file_name, file_url, file_type, upload_date, status, manual_review_queue_id, metadata
- `upload_batches`: id, organization_id, batch_name, total_files, processed_files, status, created_by_user_id, metadata

## Key Features:
1. **Data Browser**: Browse all extracted data with filtering by status, type, and date
2. **Data Editor**: View and edit extracted data with field validation
3. **Progress Tracking**: Visual progress bars for extraction completion
4. **Document Preview**: Preview source documents alongside extracted data
5. **Batch Management**: Group data by upload batch
6. **Validation Status**: Track validation status of each record
7. **Export**: Export extracted data to CSV/Excel
8. **Search**: Full-text search across all extracted data

## Mock Data:
- 15-20 draft entries with varying progress (0-100%)
- Mix of data types (fuel, utility, scope3, document)
- Different statuses (draft, in-progress, completed, validated)
- Associated customer documents with preview URLs

Please follow the exact same code structure, styling, and component patterns as all previous modules.
2. Compliance Dashboard Module
text
Based on the CarbonTally database schema and following the exact same standards and design patterns we used for previous modules, please create a comprehensive interactive Compliance Dashboard page with mock data.

## Database Schema Tables:
- `organizations`: secr_enabled, esrs_enabled, issb_enabled, reporting_standard, financial_year_end
- `activity_categories`: activity_type, esrs_e1_category, issb_category, ghg_protocol_scope
- `emissions_logs`: calculated_kg_co2e, start_date, metadata

## Key Features:
1. **Compliance Overview**: Summary cards for all compliance standards (SECR, CSRD, ISSB, GHG Protocol, TCFD)
2. **Status Tracking**: Track compliance status (compliant, in-progress, not-started, overdue)
3. **Progress Bars**: Visual progress for each compliance standard
4. **Deadline Calendar**: Upcoming compliance deadlines
5. **Gap Analysis**: Identify compliance gaps with recommendations
6. **Regulatory Calendar**: Annual compliance calendar
7. **Audit Trail**: Link to audit logs for compliance evidence
8. **Export**: Generate compliance reports

## Mock Data:
- SECR: compliant, progress 100%, next due: 2026-06-30
- CSRD: in-progress, progress 65%, next due: 2026-12-31
- ISSB S1: compliant, progress 100%, next due: 2026-03-31
- ISSB S2: in-progress, progress 70%, next due: 2026-06-30
- GHG Protocol: compliant, progress 100%
- TCFD: in-progress, progress 55%, next due: 2026-09-30

Please follow the exact same code structure, styling, and component patterns as all previous modules.
3. Notification Center Module
text
Based on the CarbonTally database schema and following the exact same standards and design patterns we used for previous modules, please create a comprehensive interactive Notification Center page with mock data.

## Database Schema Tables:
- `notifications`: id, user_id, organization_id, type, title, message, link, is_read, read_at, priority, sent_via, email_sent, push_sent, is_dismissed, metadata
- `notification_delivery_log`: id, notification_id, user_id, channel, status, error_message, sent_at, delivered_at, opened_at
- `email_logs`: id, email, type, status, error_message, metadata

## Key Features:
1. **Notification Inbox**: All notifications with read/unread status
2. **Filtering**: Filter by type, priority, read status
3. **Bulk Actions**: Mark all as read, dismiss all
4. **Delivery Tracking**: Track email and push notification delivery
5. **Priority Levels**: High, Medium, Low with color coding
6. **Notification Settings**: Configure which notifications to receive
7. **Email Logs**: History of all sent emails
8. **Channels**: Email, Push, In-app notification channels

## Mock Data:
- 20-25 notifications with various types (report_ready, validation_needed, approval_required, deadline_approaching, team_update)
- Mixed read/unread status
- Different priorities (high, medium, low)
- Email logs with delivery status

Please follow the exact same code structure, styling, and component patterns as all previous modules.
4. Activity Feed Module
text
Based on the CarbonTally database schema and following the exact same standards and design patterns we used for previous modules, please create a comprehensive interactive Activity Feed page with mock data.

## Database Schema Tables:
- `activity_feed`: id, organization_id, user_id, event_type, event_data, is_read, created_at
- `activity_logs`: id, user_id, organization_id, action, resource_type, resource_id, details, ip_address, user_agent, metadata
- `user_activity_log`: id, user_id, action, details, ip_address, user_agent, created_at
- `document_activity_log`: id, file_id, organization_id, user_id, action, details, ip_address, user_agent, created_at

## Key Features:
1. **Real-time Timeline**: Chronological activity feed with timestamps
2. **Filters**: Filter by user, action type, resource type, date range
3. **User Tracking**: Track individual user activities
4. **Resource Tracking**: Track document, emission, and other resource activities
5. **Insights**: Activity summaries and patterns
6. **Export**: Export activity logs for auditing
7. **Search**: Full-text search across all activities
8. **Read/Unread**: Mark activities as read

## Mock Data:
- 30-40 activities across different types (document_upload, emission_added, report_generated, user_login, team_member_added, document_approved)
- Different users performing actions
- Various dates and times
- Associated resources with links

Please follow the exact same code structure, styling, and component patterns as all previous modules.
5. Messaging/Chat Module
text
Based on the CarbonTally database schema and following the exact same standards and design patterns we used for previous modules, please create a comprehensive interactive Messaging/Chat page with mock data.

## Database Schema Tables:
- `conversations`: id, organization_id, staff_id, customer_id, subject, status, last_message_at, created_by, is_urgent, priority
- `messages`: id, conversation_id, sender_id, receiver_id, organization_id, content, is_read, sent_at, delivered_at, read_at, read_by, read_count, attachments, has_attachments
- `conversation_participants`: id, conversation_id, user_id, joined_at, last_read_at, is_active
- `typing_status`: id, user_id, conversation_id, is_typing, started_at
- `user_presence`: id, user_id, status, last_seen_at, current_channel
- `file_attachments`: id, message_id, conversation_id, organization_id, file_name, file_url, file_size, file_type

## Key Features:
1. **Team Chat**: Real-time team messaging
2. **Direct Messages**: 1-on-1 conversations
3. **Channel Management**: Create, join, leave channels
4. **Online Status**: User presence with online/offline indicators
5. **Typing Indicator**: Real-time typing status
6. **Message History**: Full conversation history with scroll
7. **Read Receipts**: Track who has read messages
8. **File Attachments**: Upload and share files
9. **Unread Count**: Badge count for unread messages
10. **Priority Messages**: Urgent/high priority flagging

## Mock Data:
- 5-8 conversations with different participants
- 20-30 messages per conversation
- Mixed read/unread status
- Different user statuses (online, offline, away)
- File attachments with various formats

Please follow the exact same code structure, styling, and component patterns as all previous modules.
📋 Module Creation Checklist
Use this checklist for each new module:

✅ Pre-Development
□ Identify all database tables needed
□ Map columns to UI features
□ Define mock data structure
□ Plan interactions and workflows
□ Design UI layout based on existing patterns
✅ Development
□ Theme system integration (9 themes)
□ shadcn/ui component usage
□ Left sidebar navigation
□ Top header with search and theme toggle
□ Responsive design
□ Mock data creation
□ CRUD operations
□ Toast notifications
□ Modal dialogs
□ Keyboard shortcuts
✅ Quality Assurance
□ All features working
□ Responsive at all breakpoints
□ Theme switching works
□ Mock data realistic
□ No console errors
□ User interactions smooth
🎯 Next Steps
Start with Priority 1 Modules:

Extracted Data Management

Compliance Dashboard

Notification Center

Activity Feed

Then Priority 2:

Messaging/Chat

Audit Logs

Batch Management

User Profile

Feedback & Support

Finally Priority 3:

Export History

Facility Management

Integration Management

Use the prompts above to generate each module with the same standards as our conversation.

📊 Module Dependency Graph
text
                        ┌─────────────────────┐
                        │   Organization       │
                        │   Metadata          │
                        └─────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌───▼────┐ ┌─────▼─────┐
              │  Settings │ │ Team   │ │  Roles &  │
              └───────────┘ │        │ │Permiss.   │
                            └────────┘ └───────────┘
                    │            │            │
                    └────────────┼────────────┘
                                 │
                        ┌────────▼────────┐
                        │   Upload Data   │
                        └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   Validation    │
                        │   Queue         │
                        └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   Extracted     │
                        │   Data          │
                        └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   Emissions     │
                        │   Reports       │
                        └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   Compliance    │
                        │   Dashboard     │
                        └─────────────────┘
📈 Progress Summary
Priority	Total Modules	Completed	Missing	Completion %
Critical	2	2	0	100%
High	4	0	4	0%
Medium	5	0	5	0%
Low	3	0	3	0%
Total	14	2	12	14%
Overall Progress: 14% Complete (2 out of 14 modules)

This analysis provides a complete roadmap for finishing the CarbonTally dashboard. Each missing module can be created using the provided AI prompt template with the same standards and patterns as all previous modules.


Complete Database Schema Analysis - All Missing Modules
✅ Tables Already Implemented in Dashboard
Table	Module	Status
organizations	Organization Profile	✅ Implemented
organization_members	Team Management	✅ Implemented
facilities	Facilities (partial in Assets)	⚠️ Partial
assets	Assets (partial)	⚠️ Partial
emissions_logs	Emissions Reports	✅ Implemented
defra_conversion_factors	Emissions Reports	✅ Implemented
upload_batches	Upload Data	✅ Implemented
organization_files	Documents	✅ Implemented
manual_review_queue	-	❌ Missing
staff_profiles	Team Management	✅ Implemented
roles	Roles & Permissions	✅ Implemented
user_invitations	Team Management	✅ Implemented
pending_invites	Team Management	✅ Implemented
notifications	-	❌ Missing
messages	-	❌ Missing
conversations	-	❌ Missing
activity_feed	-	❌ Missing
audit_logs	-	❌ Missing
glossary	-	❌ Missing
user_feedback	-	❌ Missing
export_history	-	❌ Missing
email_logs	-	❌ Missing
draft_entries	-	❌ Missing
customer_documents	Documents	⚠️ Partial
❌ COMPLETE LIST OF MISSING MODULES
1. 🏢 Organization Metadata Module (NEW - Not Previously Listed)
Tables: organization_metadata

Feature	Description	Schema Columns
Employee Metrics	Track employee data	total_employees, full_time_employees, part_time_employees, contract_employees, average_employees
Financial Metrics	Track financial data	annual_revenue, ebitda, total_assets
Facility Metrics	Track facility data	total_facilities, total_floor_area_sqft, occupied_floor_area_sqft
Sustainability Metrics	Track ESG data	renewable_energy_percentage, carbon_offset_percentage, energy_intensity
Reporting Info	Reporting details	reporting_standard, fiscal_year_start, fiscal_year_end
Contact Info	Sustainability contacts	sustainability_officer_name, sustainability_officer_email
Classification	Industry codes	industry_sector, naics_code, sic_code
Custom Metrics	Custom fields	custom_metrics (JSONB)

//
Database Schema Analysis - Missing Modules
Based on your complete database schema, here are the modules/features that are NOT yet implemented in your dashboard:

✅ Already Created Modules
Dashboard (Overview)

Documents Management

Upload Data (Single & Batch)

Reports Center

Emissions Reports

Manual Data Entry

Team Management

Roles & Permissions

Settings

❌ Missing Modules to Create
1. 📊 Validation Queue Module
Tables: manual_review_queue, customer_verifications, review_audit_trail, review_assignment_history

Feature	Description	Schema Tables
Queue Dashboard	Overview of pending reviews	manual_review_queue
Document Review	Review extracted data	manual_review_queue, customer_documents
Verification Status	Track verification progress	customer_verifications
Assignment Management	Assign reviewers	review_assignment_history
Audit Trail	Review history	review_audit_trail
SLA Monitoring	Track SLA compliance	manual_review_queue.sla_deadline
Priority Management	Set and manage priorities	manual_review_queue.priority_score
Escalation	Handle escalations	manual_review_queue.escalation_level
2. 📂 Extracted Data Module
Tables: draft_entries, customer_documents, emissions_logs

Feature	Description	Schema Tables
Data Browser	Browse extracted data	draft_entries
Data Editor	Edit extracted data	draft_entries
Data Validation	Validate extracted data	draft_entries
Progress Tracking	Track extraction progress	draft_entries.progress
Document Preview	Preview source documents	customer_documents
Batch Management	Manage data batches	upload_batches
3. 📈 Compliance Module
Tables: organizations, activity_categories, emissions_logs

Feature	Description	Schema Tables
Compliance Dashboard	Overview of compliance status	organizations
SECR Compliance	SECR reporting status	organizations.secr_enabled
CSRD/ESRS Compliance	ESRS E1 status	organizations.esrs_enabled
ISSB Compliance	ISSB S1/S2 status	organizations.issb_enabled
GHG Protocol	GHG Protocol compliance	activity_categories
Regulatory Calendar	Upcoming deadlines	organizations.financial_year_end
Gap Analysis	Identify compliance gaps	organizations metadata
4. 🔔 Notification Center Module
Tables: notifications, notification_delivery_log, email_logs

Feature	Description	Schema Tables
Notification Inbox	All notifications	notifications
Notification Settings	Configure notifications	system_settings
Email Logs	Email history	email_logs
Delivery Status	Track notification delivery	notification_delivery_log
Read/Unread	Mark as read/unread	notifications.is_read
Priority Filtering	Filter by priority	notifications.priority
5. 📊 Activity Feed Module
Tables: activity_feed, activity_logs, user_activity_log, document_activity_log

Feature	Description	Schema Tables
Activity Timeline	Real-time activity feed	activity_feed
User Activity	Track user actions	user_activity_log
Document Activity	Document actions	document_activity_log
Audit Trail	System audit	activity_logs
Filters	Filter by action type	activity_feed.event_type
Insights	Activity insights	activity_feed
6. 💬 Messaging/Chat Module
Tables: conversations, messages, conversation_participants, typing_status, user_presence

Feature	Description	Schema Tables
Team Chat	Real-time messaging	conversations, messages
Direct Messages	1-on-1 conversations	conversations
Channel Management	Create/join channels	conversation_participants
Online Status	User presence	user_presence
Typing Indicator	Real-time typing	typing_status
Message History	Message history	messages
Read Receipts	Message read status	messages.is_read
File Attachments	Share files	file_attachments
Unread Count	Unread messages	messages.read_count
7. 📦 Batch Management Module
Tables: upload_batches, organization_files

Feature	Description	Schema Tables
Batch Dashboard	Overview of batches	upload_batches
Batch Status	Track batch progress	upload_batches.status
File Management	Manage batch files	organization_files
Batch Progress	Track completion	upload_batches.processed_files
Batch Metadata	View batch metadata	upload_batches.metadata
8. 🔍 Audit Logs Module
Tables: audit_logs, review_audit_trail, verification_activity_log

Feature	Description	Schema Tables
Audit Dashboard	View all audit logs	audit_logs
User Actions	Track user actions	audit_logs.action_type
Resource Changes	Track resource changes	audit_logs.changes
Review History	Review audit trail	review_audit_trail
Verification Logs	Verification activity	verification_activity_log
Filters	Filter by action/resource	audit_logs.resource_type
9. 📋 Feedback Module
Tables: user_feedback

Feature	Description	Schema Tables
Feedback Dashboard	View all feedback	user_feedback
Submit Feedback	User feedback form	user_feedback
Feedback Status	Track resolution	user_feedback.status
Rating System	Rate features	user_feedback.rating
Severity Levels	Issue severity	user_feedback.severity
Assignment	Assign to staff	user_feedback.assigned_to
10. 📚 Glossary Module
Tables: glossary

Feature	Description	Schema Tables
Glossary Browser	Browse terms	glossary
Term Search	Search glossary	glossary.term
Category Filter	Filter by category	glossary.category
Related Terms	Show related terms	glossary.related_terms
Examples	Term examples	glossary.example
11. 👤 User Profile Module
Tables: staff_profiles, organization_members, user_activity_log

Feature	Description	Schema Tables
Profile Settings	Manage profile	staff_profiles
Activity History	Personal activity	user_activity_log
Performance Stats	Personal metrics	staff_profiles
Preferences	User preferences	staff_profiles.metadata
Account Security	Security settings	staff_profiles
12. 📊 Export History Module
Tables: export_history

Feature	Description	Schema Tables
Export History	View all exports	export_history
Download Reports	Download exported files	export_history.file_url
Export Filters	Filter exports	export_history.filters
Export Status	Track export status	export_history.status
Expiry Management	Manage file expiry	export_history.expires_at
13. 🏭 Facility Management Module
Tables: facilities, assets

Feature	Description	Schema Tables
Facility Dashboard	View all facilities	facilities
Asset Management	Manage assets	assets
Location Tracking	Track locations	facilities.latitude, longitude
Capacity Management	Track capacity	assets.capacity
Metadata Management	Manage metadata	facilities.metadata
14. 📦 Integration Management Module
Tables: system_settings

Feature	Description	Schema Tables
API Management	Manage API keys	system_settings
Integration Status	Track integrations	system_settings.settings_json
Webhooks	Configure webhooks	system_settings.settings_json
Data Sync	Sync status	system_settings
🚀 Recommended Implementation Order
Priority	Module	Reason
1	📊 Validation Queue	Critical for document processing workflow
2	📂 Extracted Data	Essential for data management
3	📈 Compliance	Key for regulatory reporting
4	🔔 Notification Center	User engagement & alerts
5	📊 Activity Feed	Real-time visibility
6	💬 Messaging/Chat	Team collaboration
7	📦 Batch Management	Upload workflow
8	🔍 Audit Logs	Security & compliance
9	📋 Feedback	User experience
10	📚 Glossary	User education
11	👤 User Profile	Personalization
12	📊 Export History	Data management
13	🏭 Facility Management	Asset tracking
14	📦 Integration Management	System extensibility
📊 Schema Relationship Map
text
┌─────────────────────────────────────────────────────────────────┐
│                      ORGANIZATIONS (Core)                       │
└────────────┬────────────────────────────────────┬─────────────┘
             │                                    │
    ┌────────▼────────┐              ┌───────────▼──────────┐
    │   VALIDATION     │              │     TEAM & USERS      │
    │   QUEUE          │              │                       │
    │ • manual_review_ │              │ • organization_members│
    │   queue          │              │ • staff_profiles      │
    │ • customer_      │              │ • roles              │
    │   verifications  │              │ • user_invitations   │
    │ • review_audit_  │              │ • pending_invites    │
    │   trail          │              └───────────────────────┘
    │ • review_        │
    │   assignment_    │              ┌───────────────────────┐
    │   history        │              │     COMMUNICATION     │
    └──────────────────┘              │                       │
             │                        │ • conversations       │
    ┌────────▼────────┐              │ • messages            │
    │   EXTRACTED     │              │ • conversation_       │
    │   DATA          │              │   participants        │
    │ • draft_entries │              │ • typing_status       │
    │ • customer_     │              │ • user_presence       │
    │   documents     │              │ • notifications       │
    └──────────────────┘              └───────────────────────┘
             │                        │
    ┌────────▼────────┐              ┌───────────────────────┐
    │   EMISSIONS     │              │     ACTIVITY          │
    │ • emissions_    │              │ • activity_feed       │
    │   logs          │              │ • activity_logs       │
    │ • defra_        │              │ • user_activity_log   │
    │   conversion_   │              │ • document_activity_  │
    │   factors       │              │   log                 │
    │ • activity_     │              │ • audit_logs          │
    │   categories    │              └───────────────────────┘
    └──────────────────┘
             │
    ┌────────▼────────┐              ┌───────────────────────┐
    │   FACILITIES    │              │     REPORTS           │
    │ • facilities    │              │ • export_history      │
    │ • assets        │              │ • reports (generated) │
    └──────────────────┘              └───────────────────────┘
📊 Module Dependency Graph
text
Validation Queue ──┬──► Extracted Data ──► Emissions Logs
                   │
                   ├──► Customer Documents
                   │
                   └──► Audit Logs

Activity Feed ────┬──► Notifications
                  │
                  ├──► Messaging/Chat
                  │
                  └──► User Profiles

Compliance ───────┬──► Reports
                  │
                  ├──► Emissions
                  │
                  └──► Settings

Batch Management ─► Documents ──► Validation Queue
🎯 Key Metrics by Module
Module	Tables	Key Metrics
Validation Queue	4	Pending reviews, SLA breaches, Escalations
Extracted Data	3	Extraction progress, Validated records
Compliance	3	SECR status, CSRD status, ISSB status
Notification Center	3	Unread count, Delivery rate
Activity Feed	4	Activities per day, Action types
Messaging/Chat	6	Active conversations, Online users
Batch Management	2	Active batches, Success rate
Audit Logs	3	Actions per day, Resource changes
Feedback	1	Open issues, Satisfaction rate
Would you like me to create any of these missing modules next? I can build comprehensive interactive pages with mock data for any of these features.

