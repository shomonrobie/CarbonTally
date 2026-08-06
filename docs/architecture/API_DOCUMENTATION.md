Complete New Endpoints List
1. Customer Documents (Enhanced) - routes/customer_documents.py
python
# Current endpoints (already exist)
GET    /api/customer-documents/                              # List all customer documents
GET    /api/customer-documents/assets/{asset_id}             # Get documents for specific asset

# ✅ NEW endpoints to add
GET    /api/customer-documents/stats                        # Document statistics
GET    /api/customer-documents/pending                      # Pending customer reviews
GET    /api/customer-documents/assets                       # Documents grouped by asset
GET    /api/customer-documents/{document_id}/extraction     # Get extraction details
POST   /api/customer-documents/{document_id}/verify         # Customer verification
POST   /api/customer-documents/{document_id}/request-review # Request staff review
2. Customer Dashboard - routes/customer_dashboard.py (NEW FILE)
python
GET    /api/customer/dashboard/stats                        # Main dashboard stats
GET    /api/customer/dashboard/documents                    # Document status overview
GET    /api/customer/dashboard/assets                       # Asset performance
GET    /api/customer/dashboard/emissions                    # Emissions overview
GET    /api/customer/dashboard/pending                      # Pending actions
GET    /api/customer/dashboard/activity                     # Recent activity
GET    /api/customer/dashboard/notifications                # Unread notifications
3. Admin Dashboard - routes/admin/dashboard.py (NEW FILE)
python
GET    /api/admin/dashboard/stats                           # Overall stats
GET    /api/admin/dashboard/documents                       # Document overview
GET    /api/admin/dashboard/staff                           # Staff performance
GET    /api/admin/dashboard/organizations                   # Organization health
GET    /api/admin/dashboard/sla                             # SLA compliance
GET    /api/admin/dashboard/system                          # System health
GET    /api/admin/dashboard/queue                           # Queue overview
GET    /api/admin/dashboard/export                          # Export dashboard data
4. Communication - routes/communication.py (NEW FILE)
python
# Messages
POST   /api/communication/messages                          # Send message
GET    /api/communication/messages                          # Get messages
GET    /api/communication/messages/{message_id}             # Get message detail
PUT    /api/communication/messages/{message_id}/read        # Mark as read
DELETE /api/communication/messages/{message_id}             # Delete message

# Conversations
GET    /api/communication/conversations                     # List conversations
GET    /api/communication/conversations/{conversation_id}   # Get conversation
POST   /api/communication/conversations                     # Start conversation
PUT    /api/communication/conversations/{conversation_id}/close  # Close conversation
PUT    /api/communication/conversations/{conversation_id}/archive # Archive conversation

# Notifications
GET    /api/communication/notifications                     # Get notifications
GET    /api/communication/notifications/unread              # Get unread count
PUT    /api/communication/notifications/{notification_id}/read # Mark as read
PUT    /api/communication/notifications/mark-all-read       # Mark all as read
5. Audit Logs - routes/admin/audit_logs.py (NEW FILE)
python
GET    /api/admin/audit-logs                                # Search audit logs
GET    /api/admin/audit-logs/messages                       # Message logs
GET    /api/admin/audit-logs/notifications                  # Notification logs
GET    /api/admin/audit-logs/verifications                  # Verification logs
GET    /api/admin/audit-logs/export                         # Export logs
GET    /api/admin/audit-logs/stats                          # Audit statistics
6. Customer Verifications - routes/customer_verifications.py (NEW FILE)
python
GET    /api/customer/verifications                          # List verifications
GET    /api/customer/verifications/{verification_id}        # Get verification detail
POST   /api/customer/verifications                          # Submit verification
PUT    /api/customer/verifications/{verification_id}/approve # Approve
PUT    /api/customer/verifications/{verification_id}/reject # Reject
PUT    /api/customer/verifications/{verification_id}/revision # Request revision
7. Enhanced Reports - routes/reports.py (Add to existing)
python
GET    /api/reports/customer/summary                        # Customer summary report
GET    /api/reports/admin/staff-performance                 # Staff performance report
GET    /api/reports/admin/organization-comparison           # Organization comparison
GET    /api/reports/emissions/trend                         # Emissions trend report
POST   /api/reports/generate                                # Generate custom report


## API Changes - July 2026

### New Modules
1. **Customer Dashboard** (`/api/customer/dashboard/*`)
   - Customer-facing dashboard endpoints
   - Document status, asset performance, emissions overview

2. **Admin Dashboard** (`/api/admin/dashboard/*`)
   - Admin-facing dashboard endpoints
   - Organization health, staff performance, SLA compliance

3. **Communication** (`/api/communication/*`)
   - Messages and conversations
   - Notifications management

4. **Customer Verifications** (`/api/customer/verifications/*`)
   - Customer verification workflow
   - Document approval/rejection

5. **Audit Logs** (`/api/admin/audit-logs/*`)
   - Unified audit log access
   - Activity monitoring

### Enhanced Modules
1. **Customer Documents** (`/api/customer-documents/*`)
   - Added statistics, pending reviews, verification endpoints

2. **Reports** (`/api/reports/*`)
   - Added customer summary, staff performance, trend reports


# 🌿 CarbonTally API Documentation

*Generated on D:\carbon_ledger*

## 📊 Summary

**Total Endpoints:** 137

## 📑 Table of Contents

- [🏢 Organization Management](#🏢-organization-management) (15 endpoints)
- [👥 Team & Members](#👥-team-&-members) (9 endpoints)
- [📊 Analytics & Reports](#📊-analytics-&-reports) (10 endpoints)
- [📁 Documents & Files](#📁-documents-&-files) (12 endpoints)
- [⚙️ Admin & Staff](#⚙️-admin-&-staff) (28 endpoints)
- [📝 Reviews & Assignments](#📝-reviews-&-assignments) (14 endpoints)
- [📋 Reference Data](#📋-reference-data) (5 endpoints)
- [👤 User Management](#👤-user-management) (5 endpoints)
- [🔔 Notifications](#🔔-notifications) (4 endpoints)
- [📈 Emissions](#📈-emissions) (3 endpoints)
- [📚 Glossary](#📚-glossary) (8 endpoints)
- [📤 Upload](#📤-upload) (6 endpoints)
- [📝 Drafts](#📝-drafts) (5 endpoints)
- [📊 Reports](#📊-reports) (5 endpoints)
- [📋 Logs](#📋-logs) (6 endpoints)
- [✉️ Waitlist](#✉️-waitlist) (2 endpoints)


## 🏢 Organization Management

### 📁 `organizations\assets.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/` | `get_assets()` |   |
| `🟡 POST` | `/` | `create_asset()` |   |
| `🟢 GET` | `/facilities` | `get_facilities()` |   |
| `🟡 POST` | `/facilities` | `create_facility()` |   |
| `🔴 DELETE` | `/facilities/{facility_id}` | `delete_facility()` |   |
| `🔴 DELETE` | `/{asset_id}` | `delete_asset()` |   |

### 📁 `organizations\management.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/` | `get_all_organizations()` |   |
| `🟡 POST` | `/` | `create_organization()` |   |
| `🟢 GET` | `/` | `get_all_organizations()` |   |
| `🟢 GET` | `/{org_id}` | `get_organization()` |   |
| `🔵 PUT` | `/{org_id}` | `update_organization()` |   |
| `🔴 DELETE` | `/{org_id}` | `delete_organization()` |   |
| `🟢 GET` | `/{org_id}/metadata` | `get_organization_metadata()` |   |
| `🔵 PUT` | `/{org_id}/metadata` | `update_organization_metadata()` |   |
| `🟢 GET` | `/{org_id}/stats` | `get_organization_stats_endpoint()` |   |


## 👥 Team & Members

### 📁 `organizations\members.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/` | `get_organization_members()` |   |
| `🟡 POST` | `/invite` | `invite_organization_member()` |   |
| `🔵 PUT` | `/{member_id}` | `update_organization_member()` |   |
| `🔴 DELETE` | `/{member_id}` | `remove_organization_member()` |   |
| `🟡 POST` | `/{member_id}/resend-invite` | `resend_invitation()` |   |

### 📁 `organizations\team.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟡 POST` | `/{org_id}/invite` | `invite_team_member()` |   |
| `🟢 GET` | `/{org_id}/members` | `get_team_members()` |   |
| `🔵 PATCH` | `/{org_id}/members/{member_id}` | `update_member_role()` |   |
| `🔴 DELETE` | `/{org_id}/members/{member_id}` | `remove_member()` |   |


## 📊 Analytics & Reports

### 📁 `organizations\analytics.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/asset-performance` | `get_asset_performance()` |   |
| `🟢 GET` | `/emissions-trend` | `get_emissions_trend()` |   |
| `🟢 GET` | `/scope-comparison` | `get_scope_comparison()` |   |
| `🟢 GET` | `/summary` | `get_analytics_summary()` |   |

### 📁 `organizations\dashboard.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/activity` | `get_organization_activity()` |   |
| `🟢 GET` | `/summary` | `get_dashboard_summary()` |   |

### 📁 `organizations\data.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/assets` | `get_organization_assets()` |   |
| `🟢 GET` | `/defra-factors` | `get_defra_factors()` |   |
| `🟢 GET` | `/emissions` | `get_organization_emissions()` |   |
| `🟢 GET` | `/emissions/export` | `export_emissions_csv()` |   |


## 📁 Documents & Files

### 📁 `documents.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/` | `get_documents()` |   |
| `🟡 POST` | `/admin/{file_id}/status` | `update_document_status()` |   |
| `🟢 GET` | `/stats` | `get_document_stats()` |   |
| `🟡 POST` | `/{file_id}/review` | `customer_review_document()` |   |
| `🟢 GET` | `/{file_id}/status` | `get_document_status()` |   |

### 📁 `organizations\files.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/` | `get_organization_files()` |   |
| `🟡 POST` | `/bulk-upload` | `bulk_upload_files()` |   |
| `🟢 GET` | `/stats` | `get_file_stats()` |   |
| `🟡 POST` | `/upload` | `upload_file()` |   |
| `🔴 DELETE` | `/{file_id}` | `delete_file()` |   |
| `🟢 GET` | `/{file_id}/download` | `download_file()` |   |
| `🟢 GET` | `/{file_id}/url` | `get_file_download_url_endpoint()` |   |


## ⚙️ Admin & Staff

### 📁 `admin\defra.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/activities` | `get_defra_activities()` |   |
| `🟢 GET` | `/factors` | `get_defra_factors()` |   |
| `🟡 POST` | `/factors` | `create_defra_factor()` |   |
| `🟡 POST` | `/factors/bulk` | `create_defra_factors_bulk()` |   |
| `🟢 GET` | `/factors/{factor_id}` | `get_defra_factor()` |   |
| `🔵 PUT` | `/factors/{factor_id}` | `update_defra_factor()` |   |
| `🔴 DELETE` | `/factors/{factor_id}` | `delete_defra_factor()` |   |
| `🟢 GET` | `/validate` | `validate_defra_factor()` |   |
| `🟢 GET` | `/years` | `get_defra_years()` |   |

### 📁 `admin\extraction.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟡 POST` | `/approve` | `approve_extraction()` |   |
| `🟡 POST` | `/batch/approve` | `approve_pdf_batch()` |   |
| `🟡 POST` | `/manual-review-note` | `add_manual_review_note()` |   |
| `🟢 GET` | `/reviews/pending` | `get_pending_reviews()` |   |

### 📁 `admin\permissions.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/roles` | `list_roles()` |   |
| `🟡 POST` | `/roles` | `create_role()` |   |
| `🟢 GET` | `/roles` | `get_roles()` |   |
| `🟢 GET` | `/roles/{role_id}` | `get_role()` |   |
| `🔵 PUT` | `/roles/{role_id}` | `update_role()` |   |
| `🔴 DELETE` | `/roles/{role_id}` | `delete_role()` |   |
| `🟢 GET` | `/roles/{role_id}` | `get_role()` |   |
| `🔵 PUT` | `/roles/{role_id}` | `update_role_permissions()` |   |

### 📁 `admin\staff.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/` | `get_all_staff()` |   |
| `🟡 POST` | `/` | `create_staff_member()` |   |
| `🟢 GET` | `/` | `get_all_staff()` |   |
| `🟢 GET` | `/{staff_id}` | `get_staff_member()` |   |
| `🔵 PUT` | `/{staff_id}` | `update_staff_member()` |   |
| `🔴 DELETE` | `/{staff_id}` | `delete_staff_member()` |   |
| `🔵 PUT` | `/{staff_id}/role` | `update_staff_role()` |   |


## 📝 Reviews & Assignments

### 📁 `admin\assignments.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/available` | `get_available_reviews()` |   |
| `🟡 POST` | `/batch/{batch_id}/assign` | `assign_batch()` |   |
| `🟢 GET` | `/staff` | `get_staff_list()` |   |
| `🟢 GET` | `/stats` | `get_assignment_stats()` |   |
| `🟡 POST` | `/{review_id}/assign` | `assign_review()` |   |

### 📁 `admin\reviews.py`

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/my-queue` | `get_my_review_queue()` |   |
| `🟡 POST` | `/my-queue/{review_id}/start` | `start_review()` |   |
| `🟢 GET` | `/queue` | `get_review_queue()` |   |
| `🟢 GET` | `/staff/workload` | `get_staff_workloads()` |   |
| `🟢 GET` | `/{review_id}` | `get_review_details()` |   |
| `🟡 POST` | `/{review_id}/assign` | `assign_review()` |   |
| `🟡 POST` | `/{review_id}/complete` | `complete_review()` |   |
| `🟡 POST` | `/{review_id}/reject` | `reject_review()` |   |
| `🟡 POST` | `/{review_id}/start` | `start_review()` |   |


## 📋 Reference Data

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/assets` | `get_assets_list()` |   |
| `🟢 GET` | `/categories` | `get_categories()` |   |
| `🟢 GET` | `/facilities` | `get_facilities_list()` |   |
| `🟢 GET` | `/fuel-types` | `get_fuel_types()` |   |
| `🟢 GET` | `/units` | `get_units()` |   |


## 👤 User Management

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟡 POST` | `/change-password` | `change_password()` |   |
| `🟡 POST` | `/password-reset` | `request_password_reset()` |   |
| `🟡 POST` | `/password-reset/confirm` | `confirm_password_reset()` |   |
| `🟢 GET` | `/profile` | `get_user_profile()` |   |
| `🔵 PUT` | `/profile` | `update_user_profile()` |   |


## 🔔 Notifications

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟡 POST` | `/batch/completion` | `notify_batch_completion()` |   |
| `🟡 POST` | `/customer/manual-extraction` | `notify_customer_manual_extraction()` |   |
| `🟡 POST` | `/staff` | `notify_staff()` |   |
| `🟢 GET` | `/templates` | `get_notification_templates()` |   |


## 📈 Emissions

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟡 POST` | `/emissions` | `create_emission_record()` |   |
| `🟢 GET` | `/emissions` | `get_emissions()` |   |
| `🔴 DELETE` | `/emissions/{record_id}` | `delete_emission_record()` |   |


## 📚 Glossary

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/` | `get_glossary()` |   |
| `🟡 POST` | `/` | `create_glossary_term()` |   |
| `🟢 GET` | `/categories` | `get_glossary_categories()` |   |
| `🟢 GET` | `/search` | `search_glossary()` |   |
| `🟢 GET` | `/{term_id}` | `get_glossary_term()` |   |
| `🔵 PUT` | `/{term_id}` | `update_glossary_term()` |   |
| `🔴 DELETE` | `/{term_id}` | `delete_glossary_term()` |   |
| `🟡 POST` | `/{term_id}/restore` | `restore_glossary_term()` |   |


## 📤 Upload

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟡 POST` | `/repair-pdf` | `repair_pdf()` |   |
| `🟡 POST` | `/test-upload` | `test_upload()` |   |
| `🟡 POST` | `/upload` | `upload_document()` |   |
| `🟡 POST` | `/upload-batch` | `upload_batch()` |   |
| `🟡 POST` | `/upload-csv` | `upload_csv()` |   |
| `🟡 POST` | `/upload-pdf` | `upload_pdf()` |   |


## 📝 Drafts

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟢 GET` | `/` | `get_drafts()` |   |
| `🟡 POST` | `/save` | `save_draft()` |   |
| `🟢 GET` | `/{draft_id}` | `get_draft()` |   |
| `🔴 DELETE` | `/{draft_id}` | `delete_draft()` |   |
| `🟡 POST` | `/{draft_id}/submit` | `submit_draft()` |   |


## 📊 Reports

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟡 POST` | `/admin/import-defra-factors` | `import_defra_factors()` |   |
| `🟢 GET` | `/api/defra-factors/{reporting_year}` | `get_defra_factors_by_year()` |   |
| `🟢 GET` | `/api/defra-mapping` | `get_defra_mapping()` |   |
| `🟡 POST` | `/generate-enhanced-report` | `generate_enhanced_sustainability_report()` |   |
| `🟢 GET` | `/report-status` | `report_service_status()` |   |


## 📋 Logs

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟡 POST` | `/` | `create_log()` |   |
| `🟢 GET` | `/` | `get_logs()` |   |
| `🟢 GET` | `/analytics/errors` | `get_error_logs()` |   |
| `🟢 GET` | `/analytics/stats` | `get_log_stats()` |   |
| `🟢 GET` | `/analytics/users` | `get_user_activity()` |   |
| `🟢 GET` | `/documents/{file_id}` | `get_document_logs()` |   |


## ✉️ Waitlist

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| `🟡 POST` | `/` | `add_to_waitlist()` |   |
| `🟢 GET` | `/` | `get_waitlist()` |   |


---

### 🎨 Legend

- 🟢 **GET** - Retrieve data
- 🟡 **POST** - Create new data
- 🔵 **PUT/PATCH** - Update existing data
- 🔴 **DELETE** - Remove data
- ✅ **Async** - Asynchronous endpoint

### 📝 Notes

- All endpoints are asynchronous (FastAPI)
- Authentication required for all endpoints (except waitlist)
- All responses are in JSON format
