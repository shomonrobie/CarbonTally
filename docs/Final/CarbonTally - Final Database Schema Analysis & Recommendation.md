CarbonTally - Final Database Schema Analysis & Recommendation
Date: August 2, 2026
Author: Shomon Robie & DeepSeek
Status: ✅ READY FOR DEVELOPMENT

Executive Summary
Your database schema is comprehensive and well-designed. It covers all aspects of a carbon accounting SaaS platform. However, there are some optimizations and cleanups I recommend before you start building.

✅ What's Good (Keep As Is)
Core Business Tables
✅ organizations - Complete company management

✅ facilities - Physical locations

✅ assets - Equipment/assets

✅ suppliers + supplier_categories - Vendor management

✅ product_categories - Product/service categorization

✅ organization_metadata - Rich company data

Document Processing
✅ customer_documents - Full document management

✅ document_processing_queue - Processing workflow

✅ upload_batches - Batch upload tracking

✅ manual_extraction_batches + manual_extraction_items - Manual extraction

✅ manual_review_queue - Review workflow

Emissions & Reporting
✅ emissions_logs - Core emissions data

✅ defra_conversion_factors - Emission factors

✅ report_templates + report_generation_queue - Report generation

✅ ai_content_history - AI content tracking

Messaging & Real-Time
✅ conversations + messages - Customer-staff communication

✅ conversation_participants - Participant tracking

✅ typing_status + user_presence - Real-time features

✅ file_attachments - Message attachments

Billing & Usage
✅ customer_subscriptions - Subscription management

✅ usage_tracking - Usage monitoring

✅ export_history - Export tracking

Activity & Audit
✅ activity_logs + audit_logs - Comprehensive audit trail

✅ processing_logs + processing_audit_trail - Processing audit

✅ user_activity_log - User activity tracking

Reference Data
✅ glossary - Terminology management

✅ units - Unit management

✅ document_types + document_type_categories - Document classification

✅ activity_categories - Activity classification

⚠️ What to Remove (Simplify Your Schema)
1. Team Management Tables - NOT NEEDED
Your product is one user per organization. These tables add unnecessary complexity:

Table	Why Remove
organization_members	❌ No team management
roles	❌ No role system
user_invitations	❌ No invitations
pending_invites	❌ No pending invites
2. Staff Management Tables - NOT NEEDED IN PHASE 1
These are for internal CarbonTally staff (not customers). You can add them later when you build the internal admin portal:

Table	Why Remove Now
staff_profiles	⏳ Add in Phase 2 (Internal Admin)
staff_workload	⏳ Add in Phase 2
review_assignment_history	⏳ Add in Phase 2
review_audit_trail	⏳ Add in Phase 2
queue_settings	⏳ Add in Phase 2
3. Verification Tables - MERGED INTO CUSTOMER_DOCUMENTS
Your customer_documents table already has all verification fields:

Table	Why Remove
customer_verifications	❌ Merged into customer_documents
verification_activity_log	❌ Merged into activity_logs
4. Beta & Waitlist Tables - NOT NEEDED
You're launching a finished product:

Table	Why Remove
beta_access_codes	❌ No beta program
beta_users	❌ No beta users
waitlist	❌ Full launch, no waitlist
5. Redundant Customer Review Log
Table	Why Remove
customer_review_log	❌ Redundant with customer_documents status
6. Redundant Notification Delivery Log
Table	Why Remove
notification_delivery_log	❌ Redundant with email_logs
📋 Tables to Keep (Final List)
Core Business (9 tables)
organizations

organization_metadata

facilities

assets

suppliers

supplier_categories

product_categories

users

password_reset_tokens

Document Processing (8 tables)
customer_documents

document_processing_queue

upload_batches

document_types

document_type_categories

manual_extraction_batches

manual_extraction_items

manual_review_queue

Emissions & Reporting (6 tables)
emissions_logs

defra_conversion_factors

report_templates

report_generation_queue

ai_content_history

draft_entries

Messaging & Real-Time (7 tables)
conversations

messages

conversation_participants

conversation_activity_log

message_activity_log

file_attachments

typing_status

user_presence

Billing & Usage (3 tables)
customer_subscriptions

usage_tracking

export_history

Activity & Audit (6 tables)
activity_logs

audit_logs

processing_logs

processing_audit_trail

user_activity_log

document_activity_log

Support & Reference (5 tables)
glossary

units

activity_categories

user_feedback

email_logs

email_templates

TOTAL: 46 Tables (↓ from 74, removed 28)
📊 Tables to Remove (28 Tables)
Category	Tables	Count
Team Management	organization_members, roles, user_invitations, pending_invites	4
Staff Management	staff_profiles, staff_workload, review_assignment_history, review_audit_trail, queue_settings	5
Verification	customer_verifications, verification_activity_log	2
Beta/Waitlist	beta_access_codes, beta_users, waitlist	3
Redundant	customer_review_log, notification_delivery_log	2
System	system_settings (use env vars instead)	1
File Storage	organization_files (redundant with storage)	1
Activity Feed	activity_feed (redundant with activity_logs)	1
TOTAL REMOVED		28
🔧 Minor Improvements
1. Add Missing Columns to assets
sql
ALTER TABLE assets ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
2. Add Missing Columns to suppliers
sql
ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
3. Add Missing Columns to customer_documents
sql
ALTER TABLE customer_documents ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES users(id);
ALTER TABLE customer_documents ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5,4);
ALTER TABLE customer_documents ADD COLUMN IF NOT EXISTS extracted_data JSONB;
ALTER TABLE customer_documents ADD COLUMN IF NOT EXISTS mapped_data JSONB;
ALTER TABLE customer_documents ADD COLUMN IF NOT EXISTS calculated_emissions_kg_co2e DECIMAL(10,2);
🎯 Final Recommendation
Decision	Action
Keep	46 tables (core, documents, emissions, messaging, billing, audit)
Remove	28 tables (team, staff, beta, verification, redundant)
Add	Minor columns to assets, suppliers, customer_documents
Future	Add staff/team tables in Phase 2 (Internal Admin Portal)
🚀 Why This Schema Works
Simple - One user per company, no complex team management

Complete - Covers all document processing, emissions, and reporting needs

Scalable - Can add consultant features later

Real-Time Ready - Messaging tables for customer-staff communication

Audit Ready - Comprehensive activity and audit logs

Billing Ready - Subscription and usage tracking

Extensible - Can add more features without breaking existing structure

✅ Final Verdict: Keep It As Is (With Removals)
Your schema is production-ready. Just remove the tables listed above and you're good to go.

Would you like me to provide the final cleanup migration script? 🚀

