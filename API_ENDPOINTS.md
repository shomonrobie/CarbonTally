# CarbonTally API Endpoints

*Generated on D:\carbon_ledger*

## Table of Contents

- [routes\admin\analytics.py](#routesadminanalyticspy)
- [routes\admin\assignments.py](#routesadminassignmentspy)
- [routes\admin\audit.py](#routesadminauditpy)
- [routes\admin\audit_logs.py](#routesadminaudit_logspy)
- [routes\admin\beta.py](#routesadminbetapy)
- [routes\admin\bulk.py](#routesadminbulkpy)
- [routes\admin\dashboard.py](#routesadmindashboardpy)
- [routes\admin\defra.py](#routesadmindefrapy)
- [routes\admin\document-types.py](#routesadmindocument-typespy)
- [routes\admin\email_templates.py](#routesadminemail_templatespy)
- [routes\admin\extraction.py](#routesadminextractionpy)
- [routes\admin\logs.py](#routesadminlogspy)
- [routes\admin\permissions.py](#routesadminpermissionspy)
- [routes\admin\review_history.py](#routesadminreview_historypy)
- [routes\admin\reviews.py](#routesadminreviewspy)
- [routes\admin\settings.py](#routesadminsettingspy)
- [routes\admin\staff.py](#routesadminstaffpy)
- [routes\admin\workload.py](#routesadminworkloadpy)
- [routes\communication.py](#routescommunicationpy)
- [routes\customer_dashboard.py](#routescustomer_dashboardpy)
- [routes\customer_documents.py](#routescustomer_documentspy)
- [routes\customer_verifications.py](#routescustomer_verificationspy)
- [routes\document_activity.py](#routesdocument_activitypy)
- [routes\documents_main.py](#routesdocuments_mainpy)
- [routes\drafts.py](#routesdraftspy)
- [routes\drafts_enhanced.py](#routesdrafts_enhancedpy)
- [routes\emissions.py](#routesemissionspy)
- [routes\feedback.py](#routesfeedbackpy)
- [routes\glossary.py](#routesglossarypy)
- [routes\logs.py](#routeslogspy)
- [routes\notifications.py](#routesnotificationspy)
- [routes\organizations\analytics.py](#routesorganizationsanalyticspy)
- [routes\organizations\assets.py](#routesorganizationsassetspy)
- [routes\organizations\bulk.py](#routesorganizationsbulkpy)
- [routes\organizations\dashboard.py](#routesorganizationsdashboardpy)
- [routes\organizations\data.py](#routesorganizationsdatapy)
- [routes\organizations\exports.py](#routesorganizationsexportspy)
- [routes\organizations\files.py](#routesorganizationsfilespy)
- [routes\organizations\management.py](#routesorganizationsmanagementpy)
- [routes\organizations\members.py](#routesorganizationsmemberspy)
- [routes\organizations\metadata.py](#routesorganizationsmetadatapy)
- [routes\organizations\team.py](#routesorganizationsteampy)
- [routes\reference.py](#routesreferencepy)
- [routes\reports.py](#routesreportspy)
- [routes\upload.py](#routesuploadpy)
- [routes\users.py](#routesuserspy)
- [routes\waitlist.py](#routeswaitlistpy)

## routes\admin\analytics.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/system/health` | `get_system_health()` | ✅ |  |
| `GET` | `/system/performance` | `get_system_performance()` | ✅ |  |
| `GET` | `/system/usage` | `get_system_usage()` | ✅ |  |


## routes\admin\assignments.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/assignment-stats` | `get_assignment_stats()` | ✅ |  |
| `GET` | `/available` | `get_available_reviews()` | ✅ |  |
| `POST` | `/batch/{batch_id}/assign` | `assign_batch()` | ✅ |  |
| `GET` | `/staff` | `get_staff_list()` | ✅ |  |


## routes\admin\audit.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/activity` | `get_activity_logs()` | ✅ |  |
| `GET` | `/activity/export` | `export_activity_logs()` | ✅ |  |
| `GET` | `/activity/search` | `search_activity_logs()` | ✅ |  |
| `GET` | `/activity/{log_id}` | `get_activity_log_detail()` | ✅ |  |


## routes\admin\audit_logs.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `search_audit_logs()` | ✅ |  |
| `GET` | `/actions` | `get_audit_actions()` | ✅ |  |
| `GET` | `/export` | `export_logs()` | ✅ |  |
| `GET` | `/messages` | `get_message_logs()` | ✅ |  |
| `GET` | `/notifications` | `get_notification_logs()` | ✅ |  |
| `GET` | `/organizations` | `get_audit_organizations()` | ✅ |  |
| `GET` | `/stats` | `get_audit_statistics()` | ✅ |  |
| `GET` | `/users` | `get_user_audit_activity()` | ✅ |  |
| `GET` | `/users/export` | `export_user_audit_data()` | ✅ |  |
| `GET` | `/users/summary` | `get_user_audit_summary()` | ✅ |  |
| `GET` | `/users/{user_id}/activities` | `get_user_activity_details()` | ✅ |  |
| `GET` | `/verifications` | `get_verification_logs()` | ✅ |  |


## routes\admin\beta.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/codes` | `get_beta_codes()` | ✅ |  |
| `POST` | `/codes` | `create_beta_code()` | ✅ |  |
| `GET` | `/codes/validate/{code}` | `validate_beta_code()` | ✅ |  |
| `DELETE` | `/codes/{code_id}` | `delete_beta_code()` | ✅ |  |
| `PUT` | `/codes/{code_id}/status` | `update_beta_code_status()` | ✅ |  |
| `GET` | `/users` | `get_beta_users()` | ✅ |  |
| `POST` | `/users` | `create_beta_user()` | ✅ |  |
| `GET` | `/users/stats` | `get_beta_stats()` | ✅ |  |
| `DELETE` | `/users/{user_id}` | `delete_beta_user()` | ✅ |  |
| `PUT` | `/users/{user_id}/access` | `update_beta_user_access()` | ✅ |  |


## routes\admin\bulk.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `DELETE` | `/documents/bulk` | `bulk_delete_documents()` | ✅ |  |
| `POST` | `/documents/status` | `bulk_update_document_status()` | ✅ |  |
| `POST` | `/organizations/status` | `bulk_update_organization_status()` | ✅ |  |


## routes\admin\dashboard.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/alerts` | `get_admin_alerts()` | ✅ |  |
| `GET` | `/alerts/summary` | `get_admin_alert_summary()` | ✅ |  |
| `PUT` | `/alerts/{alert_id}/resolve` | `resolve_admin_alert()` | ✅ |  |
| `GET` | `/document-types` | `get_document_type_dashboard()` | ✅ |  |
| `GET` | `/documents` | `get_document_overview()` | ✅ |  |
| `GET` | `/export` | `export_dashboard_data()` | ✅ |  |
| `GET` | `/organizations` | `get_organization_health()` | ✅ |  |
| `GET` | `/queue` | `get_queue_overview()` | ✅ |  |
| `GET` | `/sla` | `get_sla_compliance()` | ✅ |  |
| `GET` | `/staff` | `get_staff_performance()` | ✅ |  |
| `GET` | `/stats` | `get_overall_stats()` | ✅ |  |
| `GET` | `/system` | `get_system_health()` | ✅ |  |


## routes\admin\defra.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/activities` | `get_defra_activities()` | ✅ |  |
| `GET` | `/factors` | `get_admin_defra_factors()` | ✅ |  |
| `POST` | `/factors` | `create_defra_factor()` | ✅ |  |
| `POST` | `/factors/bulk` | `create_defra_factors_bulk()` | ✅ |  |
| `GET` | `/factors/{factor_id}` | `get_defra_factor()` | ✅ |  |
| `PUT` | `/factors/{factor_id}` | `update_defra_factor()` | ✅ |  |
| `DELETE` | `/factors/{factor_id}` | `delete_defra_factor()` | ✅ |  |
| `GET` | `/validate` | `validate_defra_factor()` | ✅ |  |
| `GET` | `/years` | `get_defra_years()` | ✅ |  |


## routes\admin\document-types.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `get_document_types()` | ✅ |  |
| `POST` | `/` | `create_document_type()` | ✅ |  |
| `POST` | `/bulk-create` | `bulk_create_document_types()` | ✅ |  |
| `PUT` | `/bulk-update` | `bulk_update_document_types()` | ✅ |  |
| `GET` | `/categories` | `get_document_type_categories()` | ✅ |  |
| `GET` | `/extraction-templates` | `get_extraction_templates()` | ✅ |  |
| `POST` | `/extraction-templates` | `create_extraction_template()` | ✅ |  |
| `PUT` | `/extraction-templates/{template_id}` | `update_extraction_template()` | ✅ |  |
| `GET` | `/mapping` | `get_document_type_mappings()` | ✅ |  |
| `PUT` | `/mapping` | `update_document_type_mappings()` | ✅ |  |
| `POST` | `/seed-defaults` | `seed_default_document_types()` | ✅ |  |
| `PUT` | `/{type_id}` | `update_document_type()` | ✅ |  |
| `DELETE` | `/{type_id}` | `delete_document_type()` | ✅ |  |
| `GET` | `/{type_id}` | `get_document_type_by_id()` | ✅ |  |


## routes\admin\email_templates.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `` | `get_email_templates()` | ✅ |  |
| `POST` | `` | `create_email_template()` | ✅ |  |
| `POST` | `/reset-defaults` | `reset_to_default_templates()` | ✅ |  |
| `GET` | `/types` | `get_template_types()` | ✅ |  |
| `GET` | `/{template_id}` | `get_email_template()` | ✅ |  |
| `PUT` | `/{template_id}` | `update_email_template()` | ✅ |  |
| `DELETE` | `/{template_id}` | `delete_email_template()` | ✅ |  |
| `POST` | `/{template_id}/preview` | `preview_email_template()` | ✅ |  |


## routes\admin\extraction.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/approve` | `approve_extraction()` | ✅ |  |
| `POST` | `/batch/approve` | `approve_pdf_batch()` | ✅ |  |
| `POST` | `/manual-review-note` | `add_manual_review_note()` | ✅ |  |
| `GET` | `/reviews/pending` | `get_pending_reviews()` | ✅ |  |


## routes\admin\logs.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/email` | `get_email_logs()` | ✅ |  |
| `GET` | `/email/email/{email_address}` | `get_email_logs_by_email()` | ✅ |  |
| `GET` | `/email/stats` | `get_email_stats()` | ✅ |  |
| `GET` | `/email/{log_id}` | `get_email_log_detail()` | ✅ |  |
| `GET` | `/processing` | `get_processing_logs()` | ✅ |  |
| `GET` | `/processing/file/{file_id}` | `get_processing_logs_by_file()` | ✅ |  |
| `GET` | `/processing/stats` | `get_processing_stats()` | ✅ |  |
| `GET` | `/processing/{log_id}` | `get_processing_log_detail()` | ✅ |  |


## routes\admin\permissions.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/permissions/list` | `list_available_permissions()` | ✅ |  |
| `GET` | `/roles` | `get_roles()` | ✅ |  |
| `POST` | `/roles` | `create_role()` | ✅ |  |
| `GET` | `/roles/{role_id}` | `get_role()` | ✅ |  |
| `PUT` | `/roles/{role_id}` | `update_role()` | ✅ |  |
| `DELETE` | `/roles/{role_id}` | `delete_role()` | ✅ |  |
| `POST` | `/setup-defaults` | `setup_default_roles()` | ✅ |  |


## routes\admin\review_history.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/history` | `get_all_review_history()` | ✅ |  |
| `GET` | `/history/audit` | `get_review_audit_trail()` | ✅ |  |
| `GET` | `/history/audit/export` | `export_review_audit_trail()` | ✅ |  |
| `GET` | `/history/staff/{staff_id}` | `get_staff_assignment_history()` | ✅ |  |
| `GET` | `/{review_id}/history` | `get_review_history()` | ✅ |  |


## routes\admin\reviews.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/my-queue` | `get_my_review_queue()` | ✅ |  |
| `POST` | `/my-queue/{review_id}/start` | `start_review()` | ✅ |  |
| `GET` | `/queue` | `get_review_queue()` | ✅ |  |
| `POST` | `/queue/escalate` | `escalate_review()` | ✅ |  |
| `GET` | `/queue/priority` | `get_priority_queue()` | ✅ |  |
| `POST` | `/queue/reorder` | `reorder_queue()` | ✅ |  |
| `GET` | `/queue/sla-monitor` | `get_sla_monitor()` | ✅ |  |
| `GET` | `/queue/stats/detailed` | `get_detailed_queue_stats()` | ✅ |  |
| `GET` | `/{review_id}` | `get_review_details()` | ✅ |  |
| `POST` | `/{review_id}/assign` | `assign_review()` | ✅ |  |
| `POST` | `/{review_id}/complete` | `complete_review()` | ✅ |  |
| `POST` | `/{review_id}/reject` | `reject_review()` | ✅ |  |


## routes\admin\settings.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/reset` | `reset_settings()` | ✅ |  |
| `GET` | `/settings-history` | `get_settings_history()` | ✅ |  |
| `POST` | `/validate` | `validate_settings()` | ✅ |  |


## routes\admin\staff.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `` | `get_all_staff()` | ✅ |  |
| `POST` | `/` | `create_staff_member()` | ✅ |  |
| `GET` | `/activity` | `get_staff_activity()` | ✅ |  |
| `GET` | `/me` | `get_my_staff_profile()` | ✅ |  |
| `GET` | `/performance` | `get_staff_performance()` | ✅ |  |
| `GET` | `/performance/compare` | `compare_staff_performance()` | ✅ |  |
| `GET` | `/performance/dashboard` | `get_staff_performance_dashboard()` | ✅ |  |
| `GET` | `/performance/export` | `export_staff_performance()` | ✅ |  |
| `GET` | `/performance/export` | `export_staff_performance()` | ✅ |  |
| `GET` | `/{staff_id}` | `get_staff_member()` | ✅ |  |
| `PUT` | `/{staff_id}` | `update_staff_member()` | ✅ |  |
| `DELETE` | `/{staff_id}` | `delete_staff_member()` | ✅ |  |
| `GET` | `/{staff_id}/activity-log` | `get_staff_activity_log()` | ✅ |  |
| `GET` | `/{staff_id}/performance-history` | `get_staff_performance_history()` | ✅ |  |
| `POST` | `/{staff_id}/reset-password` | `reset_staff_password()` | ✅ |  |
| `PUT` | `/{staff_id}/role` | `update_staff_role()` | ✅ |  |


## routes\admin\workload.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/forecast` | `get_workload_forecast()` | ✅ |  |
| `GET` | `/forecast/export` | `export_workload_forecast()` | ✅ |  |
| `GET` | `/forecast/scenarios` | `get_workload_scenarios()` | ✅ |  |
| `GET` | `/forecast/summary` | `get_workload_forecast_summary()` | ✅ |  |
| `POST` | `/queue/reassign` | `reassign_review()` | ✅ |  |
| `GET` | `/queue/settings` | `get_queue_settings()` | ✅ |  |
| `PUT` | `/queue/settings` | `update_queue_settings()` | ✅ |  |
| `GET` | `/queue/stats` | `get_queue_stats()` | ✅ |  |
| `GET` | `/staff/workload` | `get_staff_workload_endpoint()` | ✅ |  |
| `GET` | `/staff/workload/{staff_id}` | `get_staff_workload_detail()` | ✅ |  |


## routes\communication.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/conversations` | `get_conversations()` | ✅ |  |
| `POST` | `/conversations` | `start_conversation()` | ✅ |  |
| `GET` | `/conversations/{conversation_id}` | `get_conversation()` | ✅ |  |
| `PUT` | `/conversations/{conversation_id}/archive` | `archive_conversation()` | ✅ |  |
| `PUT` | `/conversations/{conversation_id}/close` | `close_conversation()` | ✅ |  |
| `GET` | `/conversations/{conversation_id}/participants` | `get_conversation_participants()` | ✅ |  |
| `PUT` | `/conversations/{conversation_id}/participants` | `update_conversation_participants()` | ✅ |  |
| `POST` | `/messages` | `send_message()` | ✅ |  |
| `GET` | `/messages` | `get_messages()` | ✅ |  |
| `GET` | `/messages/search` | `search_messages()` | ✅ |  |
| `GET` | `/messages/{message_id}` | `get_message_detail()` | ✅ |  |
| `DELETE` | `/messages/{message_id}` | `delete_message()` | ✅ |  |
| `POST` | `/messages/{message_id}/attachments` | `add_message_attachment()` | ✅ |  |
| `GET` | `/messages/{message_id}/attachments` | `get_message_attachments()` | ✅ |  |
| `PUT` | `/messages/{message_id}/read` | `mark_message_read()` | ✅ |  |
| `GET` | `/messages/{message_id}/replies` | `get_message_replies()` | ✅ |  |
| `POST` | `/messages/{message_id}/reply` | `reply_to_message()` | ✅ |  |
| `GET` | `/notifications` | `get_notifications()` | ✅ |  |
| `PUT` | `/notifications/mark-all-read` | `mark_all_notifications_read()` | ✅ |  |
| `GET` | `/notifications/unread` | `get_unread_notification_count()` | ✅ |  |
| `PUT` | `/notifications/{notification_id}/read` | `mark_notification_read()` | ✅ |  |
| `GET` | `/unread/messages` | `get_unread_message_count()` | ✅ |  |


## routes\customer_dashboard.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/activity` | `get_recent_activity()` | ✅ |  |
| `GET` | `/alerts` | `get_dashboard_alerts()` | ✅ |  |
| `DELETE` | `/alerts/clear-all` | `clear_all_alerts()` | ✅ |  |
| `GET` | `/alerts/summary` | `get_alert_summary()` | ✅ |  |
| `PUT` | `/alerts/{alert_id}/dismiss` | `dismiss_alert()` | ✅ |  |
| `GET` | `/assets` | `get_asset_performance()` | ✅ |  |
| `GET` | `/documents` | `get_document_status_overview()` | ✅ |  |
| `GET` | `/emissions` | `get_emissions_overview()` | ✅ |  |
| `GET` | `/notifications` | `get_notifications()` | ✅ |  |
| `GET` | `/pending` | `get_pending_actions()` | ✅ |  |
| `GET` | `/stats` | `get_dashboard_stats()` | ✅ |  |
| `GET` | `/trends` | `get_dashboard_trends()` | ✅ |  |


## routes\customer_documents.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `get_customer_documents()` | ✅ |  |
| `GET` | `/assets` | `get_documents_by_asset()` | ✅ |  |
| `GET` | `/assets/{asset_id}` | `get_documents_for_asset()` | ✅ |  |
| `GET` | `/customer_document_stats` | `get_document_statistics()` | ✅ |  |
| `GET` | `/pending` | `get_pending_documents()` | ✅ |  |
| `POST` | `/staff/organize/{document_id}` | `organize_document_for_customer()` | ✅ |  |
| `GET` | `/stats/detailed` | `get_detailed_document_stats()` | ✅ |  |
| `GET` | `/{document_id}` | `get_customer_document()` | ✅ |  |
| `GET` | `/{document_id}/download` | `download_document()` | ✅ |  |
| `GET` | `/{document_id}/extraction` | `get_extraction_details()` | ✅ |  |
| `GET` | `/{document_id}/history` | `get_document_history()` | ✅ |  |
| `GET` | `/{document_id}/notes` | `get_document_notes()` | ✅ |  |
| `POST` | `/{document_id}/notes` | `add_document_note()` | ✅ |  |
| `POST` | `/{document_id}/request-review` | `request_staff_review()` | ✅ |  |
| `POST` | `/{document_id}/verify` | `verify_document()` | ✅ |  |
| `GET` | `/{document_id}/versions` | `get_document_versions()` | ✅ |  |
| `POST` | `/{document_id}/versions` | `create_document_version()` | ✅ |  |


## routes\customer_verifications.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `list_verifications()` | ✅ |  |
| `POST` | `/` | `submit_verification()` | ✅ |  |
| `POST` | `/bulk` | `bulk_submit_verifications()` | ✅ |  |
| `POST` | `/bulk/approve` | `bulk_approve_verifications()` | ✅ |  |
| `GET` | `/stats` | `get_verification_stats()` | ✅ |  |
| `GET` | `/stats/detailed` | `get_detailed_verification_stats()` | ✅ |  |
| `GET` | `/statuses` | `get_verification_statuses()` | ✅ |  |
| `GET` | `/timeline` | `get_verification_timeline()` | ✅ |  |
| `GET` | `/{verification_id}` | `get_verification_detail()` | ✅ |  |
| `PUT` | `/{verification_id}/approve` | `approve_verification()` | ✅ |  |
| `GET` | `/{verification_id}/history` | `get_verification_history()` | ✅ |  |
| `PUT` | `/{verification_id}/reject` | `reject_verification()` | ✅ |  |
| `PUT` | `/{verification_id}/revision` | `request_revision()` | ✅ |  |


## routes\document_activity.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/admin/reviews/customer` | `get_customer_reviews_admin()` | ✅ |  |
| `GET` | `/organizations/{org_id}/documents/activity` | `get_organization_document_activity()` | ✅ |  |
| `GET` | `/{file_id}/activity` | `get_document_activity()` | ✅ |  |
| `GET` | `/{file_id}/activity/export` | `export_document_activity()` | ✅ |  |
| `POST` | `/{file_id}/review/response` | `respond_to_review()` | ✅ |  |
| `GET` | `/{file_id}/reviews` | `get_document_reviews()` | ✅ |  |


## routes\documents_main.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `get_documents()` | ✅ |  |
| `POST` | `/admin/{file_id}/status` | `update_document_status()` | ✅ |  |
| `GET` | `/stats` | `get_document_stats()` | ✅ |  |
| `POST` | `/{file_id}/review` | `customer_review_document()` | ✅ |  |
| `GET` | `/{file_id}/status` | `get_document_status()` | ✅ |  |


## routes\drafts.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `get_drafts()` | ✅ |  |
| `POST` | `/save` | `save_draft()` | ✅ |  |
| `GET` | `/{draft_id}` | `get_draft()` | ✅ |  |
| `DELETE` | `/{draft_id}` | `delete_draft()` | ✅ |  |
| `POST` | `/{draft_id}/submit` | `submit_draft()` | ✅ |  |


## routes\drafts_enhanced.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/{draft_id}/progress` | `get_draft_progress()` | ✅ |  |
| `POST` | `/{draft_id}/publish` | `publish_draft()` | ✅ |  |
| `GET` | `/{draft_id}/sections` | `get_draft_sections()` | ✅ |  |
| `POST` | `/{draft_id}/sections/{section_id}` | `update_draft_section()` | ✅ |  |
| `DELETE` | `/{draft_id}/sections/{section_id}` | `delete_draft_section()` | ✅ |  |
| `POST` | `/{draft_id}/validate` | `validate_draft()` | ✅ |  |


## routes\emissions.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/bulk/approve` | `bulk_approve_emissions()` | ✅ |  |
| `POST` | `/bulk/reject` | `bulk_reject_emissions()` | ✅ |  |
| `GET` | `/by-asset` | `get_emissions_by_asset()` | ✅ |  |
| `GET` | `/by-document-type` | `get_emissions_by_document_type()` | ✅ |  |
| `POST` | `/emissions` | `create_emission_record()` | ✅ |  |
| `GET` | `/emissions` | `get_emissions()` | ✅ |  |
| `POST` | `/emissions/bulk` | `bulk_create_emissions()` | ✅ |  |
| `GET` | `/emissions/export` | `export_emissions()` | ✅ |  |
| `GET` | `/emissions/stats` | `get_emission_stats()` | ✅ |  |
| `POST` | `/emissions/verify` | `verify_emissions()` | ✅ |  |
| `DELETE` | `/emissions/{record_id}` | `delete_emission_record()` | ✅ |  |
| `PUT` | `/emissions/{record_id}` | `update_emission_record()` | ✅ |  |
| `GET` | `/stats/summary` | `get_emissions_summary()` | ✅ |  |
| `GET` | `/verification-pending` | `get_pending_emissions_verifications()` | ✅ |  |
| `GET` | `/{record_id}/verification-history` | `get_emissions_verification_history()` | ✅ |  |


## routes\feedback.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `` | `submit_feedback()` | ✅ |  |
| `GET` | `` | `get_user_feedback()` | ✅ |  |
| `GET` | `/{feedback_id}` | `get_feedback_detail()` | ✅ |  |
| `PUT` | `/{feedback_id}` | `update_feedback_status()` | ✅ |  |


## routes\glossary.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `get_glossary()` | ✅ |  |
| `POST` | `/` | `create_glossary_term()` | ✅ |  |
| `GET` | `/categories` | `get_glossary_categories()` | ✅ |  |
| `GET` | `/search` | `search_glossary()` | ✅ |  |
| `GET` | `/{term_id}` | `get_glossary_term()` | ✅ |  |
| `PUT` | `/{term_id}` | `update_glossary_term()` | ✅ |  |
| `DELETE` | `/{term_id}` | `delete_glossary_term()` | ✅ |  |
| `POST` | `/{term_id}/restore` | `restore_glossary_term()` | ✅ |  |


## routes\logs.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/` | `create_log()` | ✅ |  |
| `GET` | `/` | `get_logs()` | ✅ |  |
| `GET` | `/analytics/errors` | `get_error_logs()` | ✅ |  |
| `GET` | `/analytics/stats` | `get_log_stats()` | ✅ |  |
| `GET` | `/analytics/users` | `get_user_activity()` | ✅ |  |
| `GET` | `/documents/{file_id}` | `get_document_logs()` | ✅ |  |


## routes\notifications.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/batch/completion` | `notify_batch_completion()` | ✅ |  |
| `POST` | `/customer/manual-extraction` | `notify_customer_manual_extraction()` | ✅ |  |
| `POST` | `/staff` | `notify_staff()` | ✅ |  |
| `GET` | `/templates` | `get_notification_templates()` | ✅ |  |


## routes\organizations\analytics.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/asset-performance` | `get_asset_performance()` | ✅ |  |
| `GET` | `/emissions-trend` | `get_emissions_trend()` | ✅ |  |
| `GET` | `/scope-comparison` | `get_scope_comparison()` | ✅ |  |
| `GET` | `/summary` | `get_analytics_summary()` | ✅ |  |


## routes\organizations\assets.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/{org_id}/assets` | `get_assets()` | ✅ |  |
| `POST` | `/{org_id}/assets` | `create_asset()` | ✅ |  |
| `POST` | `/{org_id}/assets/bulk/update` | `bulk_update_assets()` | ✅ |  |
| `GET` | `/{org_id}/assets/stats` | `get_asset_stats_endpoint()` | ✅ |  |
| `PUT` | `/{org_id}/assets/{asset_id}` | `update_asset()` | ✅ |  |
| `PATCH` | `/{org_id}/assets/{asset_id}` | `patch_asset()` | ✅ |  |
| `DELETE` | `/{org_id}/assets/{asset_id}` | `delete_asset()` | ✅ |  |
| `GET` | `/{org_id}/facilities` | `get_facilities()` | ✅ |  |
| `POST` | `/{org_id}/facilities` | `create_facility()` | ✅ |  |
| `GET` | `/{org_id}/facilities/stats` | `get_facility_stats_endpoint()` | ✅ |  |
| `PUT` | `/{org_id}/facilities/{facility_id}` | `update_facility()` | ✅ |  |
| `PATCH` | `/{org_id}/facilities/{facility_id}` | `patch_facility()` | ✅ |  |
| `DELETE` | `/{org_id}/facilities/{facility_id}` | `delete_facility()` | ✅ |  |
| `POST` | `/{org_id}/facilities/{facility_id}/status` | `update_facility_status()` | ✅ |  |


## routes\organizations\bulk.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/{org_id}/assets/bulk/create` | `bulk_create_assets()` | ✅ |  |
| `POST` | `/{org_id}/members/bulk/invite` | `bulk_invite_members()` | ✅ |  |


## routes\organizations\dashboard.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/dashboard-summary` | `get_dashboard_summary()` | ✅ |  |
| `GET` | `/organization-activity` | `get_organization_activity()` | ✅ |  |


## routes\organizations\data.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/organizations/{org_id}/assets ` | `get_organization_assets()` | ✅ |  |
| `GET` | `/{org_id}/defra-factors` | `get_organization_defra_factors()` | ✅ |  |
| `GET` | `/{org_id}/emissions-data` | `get_organization_emissions()` | ✅ |  |
| `GET` | `/{org_id}/emissions/export-csv` | `export_emissions_csv()` | ✅ |  |


## routes\organizations\exports.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `` | `get_exports()` | ✅ |  |
| `POST` | `/exports/emissions` | `export_emissions_data()` | ✅ |  |
| `DELETE` | `/{export_id}` | `delete_export()` | ✅ |  |
| `GET` | `/{export_id}/download` | `download_export()` | ✅ |  |


## routes\organizations\files.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `get_organization_files()` | ✅ |  |
| `POST` | `/api/organizations/{org_id}/files/upload` | `upload_file()` | ✅ |  |
| `POST` | `/bulk-upload` | `bulk_upload_files()` | ✅ |  |
| `GET` | `/organizations/{org_id}/files/stats` | `get_file_stats()` | ✅ |  |
| `DELETE` | `/{file_id}` | `delete_file()` | ✅ |  |
| `GET` | `/{file_id}/download` | `download_file()` | ✅ |  |
| `GET` | `/{file_id}/url` | `get_file_download_url_endpoint()` | ✅ |  |
| `GET` | `/{org_id}/files/archived` | `get_archived_files()` | ✅ |  |
| `POST` | `/{org_id}/files/{file_id}/archive` | `archive_file()` | ✅ |  |
| `POST` | `/{org_id}/files/{file_id}/comments` | `add_file_comment()` | ✅ |  |
| `GET` | `/{org_id}/files/{file_id}/comments` | `get_file_comments()` | ✅ |  |
| `PUT` | `/{org_id}/files/{file_id}/comments/{comment_id}` | `update_file_comment()` | ✅ |  |
| `DELETE` | `/{org_id}/files/{file_id}/comments/{comment_id}` | `delete_file_comment()` | ✅ |  |
| `DELETE` | `/{org_id}/files/{file_id}/permanent` | `permanent_delete_file()` | ✅ |  |
| `POST` | `/{org_id}/files/{file_id}/restore` | `restore_file()` | ✅ |  |
| `GET` | `/{org_id}/files/{file_id}/versions` | `get_file_versions()` | ✅ |  |
| `POST` | `/{org_id}/files/{file_id}/versions` | `create_file_version()` | ✅ |  |
| `GET` | `/{org_id}/files/{file_id}/versions/{version_id}` | `get_file_version_detail()` | ✅ |  |


## routes\organizations\management.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/` | `create_organization()` | ✅ |  |
| `GET` | `/{org_id}` | `get_organization()` | ✅ |  |
| `PUT` | `/{org_id}` | `update_organization()` | ✅ |  |
| `DELETE` | `/{org_id}` | `delete_organization()` | ✅ |  |
| `GET` | `/{org_id}/metadata` | `get_organization_metadata()` | ✅ |  |
| `PUT` | `/{org_id}/metadata` | `update_organization_metadata()` | ✅ |  |
| `GET` | `/{org_id}/stats` | `get_organization_stats_endpoint()` | ✅ |  |


## routes\organizations\members.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `get_organization_members()` | ✅ |  |
| `POST` | `/invite` | `invite_organization_member()` | ✅ |  |
| `PUT` | `/{member_id}` | `update_organization_member()` | ✅ |  |
| `DELETE` | `/{member_id}` | `remove_organization_member()` | ✅ |  |
| `POST` | `/{member_id}/resend-invite` | `resend_invitation()` | ✅ |  |
| `POST` | `/{org_id}/members/bulk/remove` | `bulk_remove_members()` | ✅ |  |
| `POST` | `/{org_id}/members/bulk/update` | `bulk_update_members()` | ✅ |  |
| `GET` | `/{org_id}/members/roles` | `get_member_roles()` | ✅ |  |
| `GET` | `/{org_id}/members/stats` | `get_member_stats()` | ✅ |  |


## routes\organizations\metadata.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/{org_id}/metadata/all` | `get_all_metadata()` | ✅ |  |
| `GET` | `/{org_id}/metadata/contacts` | `get_contact_metadata()` | ✅ |  |
| `PUT` | `/{org_id}/metadata/contacts` | `update_contact_metadata()` | ✅ |  |
| `GET` | `/{org_id}/metadata/custom-metrics` | `get_custom_metrics()` | ✅ |  |
| `PUT` | `/{org_id}/metadata/custom-metrics` | `update_custom_metrics()` | ✅ |  |
| `GET` | `/{org_id}/metadata/employees` | `get_employee_metadata()` | ✅ |  |
| `PUT` | `/{org_id}/metadata/employees` | `update_employee_metadata()` | ✅ |  |
| `GET` | `/{org_id}/metadata/financials` | `get_financial_metadata()` | ✅ |  |
| `PUT` | `/{org_id}/metadata/financials` | `update_financial_metadata()` | ✅ |  |
| `GET` | `/{org_id}/metadata/industry` | `get_industry_metadata()` | ✅ |  |
| `PUT` | `/{org_id}/metadata/industry` | `update_industry_metadata()` | ✅ |  |
| `GET` | `/{org_id}/metadata/required-fields` | `get_required_metadata_fields()` | ✅ |  |
| `GET` | `/{org_id}/metadata/sustainability` | `get_sustainability_metadata()` | ✅ |  |
| `PUT` | `/{org_id}/metadata/sustainability` | `update_sustainability_metadata()` | ✅ |  |
| `POST` | `/{org_id}/metadata/validate` | `validate_metadata()` | ✅ |  |


## routes\organizations\team.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/{org_id}/invite` | `invite_team_member()` | ✅ |  |
| `GET` | `/{org_id}/members` | `get_team_members()` | ✅ |  |
| `PATCH` | `/{org_id}/members/{member_id}` | `update_member_role()` | ✅ |  |
| `DELETE` | `/{org_id}/members/{member_id}` | `remove_member()` | ✅ |  |


## routes\reference.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/asset-types` | `get_asset_types()` | ✅ |  |
| `GET` | `/assets` | `get_assets_list()` | ✅ |  |
| `GET` | `/categories` | `get_reference_categories()` | ✅ |  |
| `GET` | `/facilities` | `get_facilities_list()` | ✅ |  |
| `GET` | `/facility-types` | `get_facility_types()` | ✅ |  |
| `GET` | `/fuel-types` | `get_fuel_types()` | ✅ |  |
| `GET` | `/units` | `get_units()` | ✅ |  |


## routes\reports.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/admin/import-defra-factors` | `import_defra_factors()` | ✅ |  |
| `GET` | `/admin/organization-comparison` | `get_organization_comparison_report()` | ✅ |  |
| `GET` | `/admin/staff-performance` | `get_staff_performance_report()` | ✅ |  |
| `GET` | `/customer/summary` | `get_customer_summary_report()` | ✅ |  |
| `GET` | `/defra-factors/{reporting_year}` | `get_defra_factors_by_year()` | ✅ |  |
| `GET` | `/defra-mapping` | `get_defra_mapping()` | ✅ |  |
| `GET` | `/emissions/trend` | `get_emissions_trend_report()` | ✅ |  |
| `POST` | `/generate` | `generate_custom_report()` | ✅ |  |
| `POST` | `/generate-enhanced-report` | `generate_enhanced_sustainability_report()` | ✅ |  |
| `GET` | `/metrics` | `get_available_metrics()` | ✅ |  |
| `GET` | `/report_status` | `report_service_status()` | ✅ |  |
| `POST` | `/schedule` | `create_report_schedule()` | ✅ |  |
| `GET` | `/schedule` | `get_report_schedules()` | ✅ |  |
| `GET` | `/schedule/frequencies` | `get_schedule_frequencies()` | ✅ |  |
| `DELETE` | `/schedule/{schedule_id}` | `delete_report_schedule()` | ✅ |  |
| `GET` | `/shared` | `get_shared_reports()` | ✅ |  |
| `GET` | `/templates` | `get_report_templates()` | ✅ |  |
| `POST` | `/templates` | `create_report_template()` | ✅ |  |
| `GET` | `/templates/categories` | `get_template_categories()` | ✅ |  |
| `PUT` | `/templates/{template_id}` | `update_report_template()` | ✅ |  |
| `DELETE` | `/templates/{template_id}` | `delete_report_template()` | ✅ |  |
| `GET` | `/types` | `get_report_types()` | ✅ |  |
| `POST` | `/{report_id}/share` | `share_report()` | ✅ |  |


## routes\upload.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/batches/stats` | `get_batch_stats()` | ✅ |  |
| `POST` | `/batches/{batch_id}/cancel` | `cancel_batch()` | ✅ |  |
| `GET` | `/batches/{batch_id}/progress` | `get_batch_progress()` | ✅ |  |
| `GET` | `/batches/{batch_id}/status` | `get_batch_status()` | ✅ |  |
| `POST` | `/repair-pdf` | `repair_pdf()` | ✅ |  |
| `POST` | `/test-upload` | `test_upload()` | ✅ |  |
| `POST` | `/upload` | `upload_document()` | ✅ |  |
| `POST` | `/upload-batch` | `upload_batch()` | ✅ |  |
| `POST` | `/upload-csv` | `upload_csv()` | ✅ |  |
| `POST` | `/upload-pdf` | `upload_pdf()` | ✅ |  |


## routes\users.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/change-password` | `change_password()` | ✅ |  |
| `POST` | `/password-reset` | `request_password_reset()` | ✅ |  |
| `POST` | `/password-reset/confirm` | `confirm_password_reset()` | ✅ |  |
| `GET` | `/profile` | `get_user_profile()` | ✅ |  |
| `PUT` | `/profile` | `update_user_profile()` | ✅ |  |


## routes\waitlist.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/` | `add_to_waitlist()` | ✅ |  |
| `GET` | `/` | `get_waitlist()` | ✅ |  |



**Total endpoints:** 397
