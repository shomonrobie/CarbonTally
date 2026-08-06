# CarbonTally API Endpoints

*Generated on D:\carbon_ledger*

## Table of Contents

- [routes\admin\assignments.py](#routesadminassignmentspy)
- [routes\admin\audit.py](#routesadminauditpy)
- [routes\admin\beta.py](#routesadminbetapy)
- [routes\admin\bulk.py](#routesadminbulkpy)
- [routes\admin\defra.py](#routesadmindefrapy)
- [routes\admin\email_templates.py](#routesadminemail_templatespy)
- [routes\admin\extraction.py](#routesadminextractionpy)
- [routes\admin\logs.py](#routesadminlogspy)
- [routes\admin\permissions.py](#routesadminpermissionspy)
- [routes\admin\review_history.py](#routesadminreview_historypy)
- [routes\admin\reviews.py](#routesadminreviewspy)
- [routes\admin\settings.py](#routesadminsettingspy)
- [routes\admin\staff.py](#routesadminstaffpy)
- [routes\admin\staff_enhanced.py](#routesadminstaff_enhancedpy)
- [routes\admin\workload.py](#routesadminworkloadpy)
- [routes\documents.py](#routesdocumentspy)
- [routes\documents\activity.py](#routesdocumentsactivitypy)
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

## routes\admin\assignments.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/available` | `get_available_reviews()` | ✅ |  |
| `POST` | `/batch/{batch_id}/assign` | `assign_batch()` | ✅ |  |
| `GET` | `/staff` | `get_staff_list()` | ✅ |  |
| `GET` | `/stats` | `get_assignment_stats()` | ✅ |  |
| `POST` | `/{review_id}/assign` | `assign_review()` | ✅ |  |


## routes\admin\audit.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/activity` | `get_activity_logs()` | ✅ |  |
| `GET` | `/activity/export` | `export_activity_logs()` | ✅ |  |
| `GET` | `/activity/search` | `search_activity_logs()` | ✅ |  |
| `GET` | `/activity/{log_id}` | `get_activity_log_detail()` | ✅ |  |


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


## routes\admin\defra.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/activities` | `get_defra_activities()` | ✅ |  |
| `GET` | `/factors` | `get_defra_factors()` | ✅ |  |
| `POST` | `/factors` | `create_defra_factor()` | ✅ |  |
| `POST` | `/factors/bulk` | `create_defra_factors_bulk()` | ✅ |  |
| `GET` | `/factors/{factor_id}` | `get_defra_factor()` | ✅ |  |
| `PUT` | `/factors/{factor_id}` | `update_defra_factor()` | ✅ |  |
| `DELETE` | `/factors/{factor_id}` | `delete_defra_factor()` | ✅ |  |
| `GET` | `/validate` | `validate_defra_factor()` | ✅ |  |
| `GET` | `/years` | `get_defra_years()` | ✅ |  |


## routes\admin\email_templates.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/system/health` | `get_system_health()` | ✅ |  |
| `GET` | `/system/performance` | `get_system_performance()` | ✅ |  |
| `GET` | `/system/usage` | `get_system_usage()` | ✅ |  |


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
| `GET` | `/roles` | `list_roles()` | ✅ |  |
| `POST` | `/roles` | `create_role()` | ✅ |  |
| `GET` | `/roles` | `get_roles()` | ✅ |  |
| `GET` | `/roles/{role_id}` | `get_role()` | ✅ |  |
| `PUT` | `/roles/{role_id}` | `update_role()` | ✅ |  |
| `DELETE` | `/roles/{role_id}` | `delete_role()` | ✅ |  |
| `GET` | `/roles/{role_id}` | `get_role()` | ✅ |  |
| `PUT` | `/roles/{role_id}` | `update_role_permissions()` | ✅ |  |


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
| `GET` | `/staff/workload` | `get_staff_workloads()` | ✅ |  |
| `GET` | `/{review_id}` | `get_review_details()` | ✅ |  |
| `POST` | `/{review_id}/assign` | `assign_review()` | ✅ |  |
| `POST` | `/{review_id}/complete` | `complete_review()` | ✅ |  |
| `POST` | `/{review_id}/reject` | `reject_review()` | ✅ |  |
| `POST` | `/{review_id}/start` | `start_review()` | ✅ |  |


## routes\admin\settings.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/history` | `get_settings_history()` | ✅ |  |
| `POST` | `/reset` | `reset_settings()` | ✅ |  |
| `POST` | `/validate` | `validate_settings()` | ✅ |  |


## routes\admin\staff.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `get_all_staff()` | ✅ |  |
| `POST` | `/` | `create_staff_member()` | ✅ |  |
| `GET` | `/` | `get_all_staff()` | ✅ |  |
| `GET` | `/{staff_id}` | `get_staff_member()` | ✅ |  |
| `PUT` | `/{staff_id}` | `update_staff_member()` | ✅ |  |
| `DELETE` | `/{staff_id}` | `delete_staff_member()` | ✅ |  |
| `PUT` | `/{staff_id}/role` | `update_staff_role()` | ✅ |  |


## routes\admin\staff_enhanced.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/activity` | `get_staff_activity()` | ✅ |  |
| `GET` | `/performance` | `get_staff_performance()` | ✅ |  |
| `GET` | `/performance/export` | `export_staff_performance()` | ✅ |  |
| `GET` | `/{staff_id}/activity-log` | `get_staff_activity_log()` | ✅ |  |
| `GET` | `/{staff_id}/performance-history` | `get_staff_performance_history()` | ✅ |  |
| `POST` | `/{staff_id}/reset-password` | `reset_staff_password()` | ✅ |  |


## routes\admin\workload.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/queue/reassign` | `reassign_review()` | ✅ |  |
| `GET` | `/queue/settings` | `get_queue_settings()` | ✅ |  |
| `PUT` | `/queue/settings` | `update_queue_settings()` | ✅ |  |
| `GET` | `/queue/stats` | `get_queue_stats()` | ✅ |  |
| `GET` | `/staff/workload` | `get_staff_workload()` | ✅ |  |
| `GET` | `/staff/workload/{staff_id}` | `get_staff_workload_detail()` | ✅ |  |


## routes\documents.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `get_documents()` | ✅ |  |
| `POST` | `/admin/{file_id}/status` | `update_document_status()` | ✅ |  |
| `GET` | `/stats` | `get_document_stats()` | ✅ |  |
| `POST` | `/{file_id}/review` | `customer_review_document()` | ✅ |  |
| `GET` | `/{file_id}/status` | `get_document_status()` | ✅ |  |


## routes\documents\activity.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/admin/reviews/customer` | `get_customer_reviews_admin()` | ✅ |  |
| `GET` | `/organizations/{org_id}/documents/activity` | `get_organization_document_activity()` | ✅ |  |
| `GET` | `/{file_id}/activity` | `get_document_activity()` | ✅ |  |
| `GET` | `/{file_id}/activity/export` | `export_document_activity()` | ✅ |  |
| `POST` | `/{file_id}/review/response` | `respond_to_review()` | ✅ |  |
| `GET` | `/{file_id}/reviews` | `get_document_reviews()` | ✅ |  |


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
| `POST` | `/emissions` | `create_emission_record()` | ✅ |  |
| `GET` | `/emissions` | `get_emissions()` | ✅ |  |
| `POST` | `/emissions/bulk` | `bulk_create_emissions()` | ✅ |  |
| `GET` | `/emissions/export` | `export_emissions()` | ✅ |  |
| `GET` | `/emissions/stats` | `get_emission_stats()` | ✅ |  |
| `POST` | `/emissions/verify` | `verify_emissions()` | ✅ |  |
| `DELETE` | `/emissions/{record_id}` | `delete_emission_record()` | ✅ |  |
| `PUT` | `/emissions/{record_id}` | `update_emission_record()` | ✅ |  |


## routes\feedback.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `` | `submit_feedback()` | ✅ |  |
| `GET` | `` | `get_user_feedback()` | ✅ |  |
| `GET` | `/admin/pending` | `get_pending_feedback()` | ✅ |  |
| `GET` | `/admin/stats` | `get_feedback_stats()` | ✅ |  |
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
| `GET` | `/` | `get_assets()` | ✅ |  |
| `POST` | `/` | `create_asset()` | ✅ |  |
| `GET` | `/facilities` | `get_facilities()` | ✅ |  |
| `POST` | `/facilities` | `create_facility()` | ✅ |  |
| `DELETE` | `/facilities/{facility_id}` | `delete_facility()` | ✅ |  |
| `DELETE` | `/{asset_id}` | `delete_asset()` | ✅ |  |
| `POST` | `/{org_id}/assets/bulk/update` | `bulk_update_assets()` | ✅ |  |
| `GET` | `/{org_id}/assets/stats` | `get_asset_stats()` | ✅ |  |
| `PUT` | `/{org_id}/assets/{asset_id}` | `update_asset()` | ✅ |  |
| `PATCH` | `/{org_id}/assets/{asset_id}` | `patch_asset()` | ✅ |  |
| `GET` | `/{org_id}/facilities/stats` | `get_facility_stats()` | ✅ |  |
| `PUT` | `/{org_id}/facilities/{facility_id}` | `update_facility()` | ✅ |  |
| `PATCH` | `/{org_id}/facilities/{facility_id}` | `patch_facility()` | ✅ |  |
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
| `GET` | `/activity` | `get_organization_activity()` | ✅ |  |
| `GET` | `/summary` | `get_dashboard_summary()` | ✅ |  |


## routes\organizations\data.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/assets` | `get_organization_assets()` | ✅ |  |
| `GET` | `/defra-factors` | `get_defra_factors()` | ✅ |  |
| `GET` | `/emissions` | `get_organization_emissions()` | ✅ |  |
| `GET` | `/emissions/export` | `export_emissions_csv()` | ✅ |  |


## routes\organizations\exports.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `` | `get_exports()` | ✅ |  |
| `POST` | `/emissions` | `export_emissions_data()` | ✅ |  |
| `DELETE` | `/{export_id}` | `delete_export()` | ✅ |  |
| `GET` | `/{export_id}/download` | `download_export()` | ✅ |  |


## routes\organizations\files.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `get_organization_files()` | ✅ |  |
| `POST` | `/bulk-upload` | `bulk_upload_files()` | ✅ |  |
| `GET` | `/stats` | `get_file_stats()` | ✅ |  |
| `POST` | `/upload` | `upload_file()` | ✅ |  |
| `DELETE` | `/{file_id}` | `delete_file()` | ✅ |  |
| `GET` | `/{file_id}/download` | `download_file()` | ✅ |  |
| `GET` | `/{file_id}/url` | `get_file_download_url_endpoint()` | ✅ |  |
| `GET` | `/{org_id}/files/archived` | `get_archived_files()` | ✅ |  |
| `POST` | `/{org_id}/files/{file_id}/archive` | `archive_file()` | ✅ |  |
| `DELETE` | `/{org_id}/files/{file_id}/permanent` | `permanent_delete_file()` | ✅ |  |
| `POST` | `/{org_id}/files/{file_id}/restore` | `restore_file()` | ✅ |  |


## routes\organizations\management.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `GET` | `/` | `get_all_organizations()` | ✅ |  |
| `POST` | `/` | `create_organization()` | ✅ |  |
| `GET` | `/` | `get_all_organizations()` | ✅ |  |
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
| `GET` | `/assets` | `get_assets_list()` | ✅ |  |
| `GET` | `/categories` | `get_categories()` | ✅ |  |
| `GET` | `/facilities` | `get_facilities_list()` | ✅ |  |
| `GET` | `/fuel-types` | `get_fuel_types()` | ✅ |  |
| `GET` | `/units` | `get_units()` | ✅ |  |


## routes\reports.py

*Directory: Other*

| Method | Endpoint | Function | Async | Summary |
|--------|----------|----------|-------|---------|
| `POST` | `/admin/import-defra-factors` | `import_defra_factors()` | ✅ |  |
| `GET` | `/api/defra-factors/{reporting_year}` | `get_defra_factors_by_year()` | ✅ |  |
| `GET` | `/api/defra-mapping` | `get_defra_mapping()` | ✅ |  |
| `POST` | `/generate-enhanced-report` | `generate_enhanced_sustainability_report()` | ✅ |  |
| `GET` | `/report-status` | `report_service_status()` | ✅ |  |


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



**Total endpoints:** 254
