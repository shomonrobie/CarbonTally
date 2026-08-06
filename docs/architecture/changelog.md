Changelog
Version 2.0.0 - July 2026
Added
New Modules:

routes/customer_dashboard.py - Customer dashboard endpoints (7 endpoints)

routes/admin/dashboard.py - Admin dashboard endpoints (8 endpoints)

routes/communication.py - Communication endpoints (14 endpoints)

routes/admin/audit_logs.py - Audit log endpoints (6 endpoints)

routes/customer_verifications.py - Verification endpoints (6 endpoints)

routes/customer_documents.py - Enhanced with document types (9 endpoints)

New Features:

Document type classification system

Auto-classification of uploaded documents

Staff organization of customer documents

Customer verification workflow

Communication system (messages & conversations)

Notification system

Unified audit logging

Dashboard enhancements

New Tables:

document_types

audit_logs

conversations

conversation_activity_log

messages

message_activity_log

notifications

notification_delivery_log

customer_verifications

verification_activity_log

Modified
Files:

routes/customer_documents.py - Added new endpoints and document type support

routes/reports.py - Added new report types

routes/organizations/dashboard.py - Enhanced with new data

routes/organizations/files.py - Added document type classification

database.py - Added new helper functions

Tables:

customer_documents - Added document type fields, classification fields, billing period fields

emissions_logs - Added customer_document_id

manual_review_queue - Added customer_document_id

Removed
routes/admin/staff_enhanced_bak.py - Backup file no longer needed

Fixed
All group_by and clone() issues in Supabase queries

Route ordering conflicts

Deprecated datetime usage (utcnow() → now(timezone.utc))

Import issues in various modules

Complete Endpoints List
Total Endpoints: 332
1. ADMIN ENDPOINTS (123 endpoints)
1.1 Admin - Analytics (/api/admin/analytics)
#	Method	Endpoint	Function	Summary
1	GET	/system/health	get_system_health()	System health check
2	GET	/system/performance	get_system_performance()	System performance metrics
3	GET	/system/usage	get_system_usage()	System usage statistics
1.2 Admin - Assignments (/api/admin/assignments)
#	Method	Endpoint	Function	Summary
4	GET	/assignment-stats	get_assignment_stats()	Assignment statistics
5	GET	/available	get_available_reviews()	Available reviews for assignment
6	POST	/batch/{batch_id}/assign	assign_batch()	Assign batch to staff
7	GET	/staff	get_staff_list()	Staff list for assignments
1.3 Admin - Audit (/api/admin/audit)
#	Method	Endpoint	Function	Summary
8	GET	/activity	get_activity_logs()	Get activity logs
9	GET	/activity/export	export_activity_logs()	Export activity logs
10	GET	/activity/search	search_activity_logs()	Search activity logs
11	GET	/activity/{log_id}	get_activity_log_detail()	Get log detail
1.4 Admin - Audit Logs (/api/admin/audit-logs) ✅ NEW
#	Method	Endpoint	Function	Summary
12	GET	/	get_audit_logs()	Search audit logs
13	GET	/messages	get_message_logs()	Message logs
14	GET	/notifications	get_notification_logs()	Notification logs
15	GET	/verifications	get_verification_logs()	Verification logs
16	GET	/export	export_audit_logs()	Export audit logs
17	GET	/stats	get_audit_stats()	Audit statistics
1.5 Admin - Beta (/api/admin/beta)
#	Method	Endpoint	Function	Summary
18	GET	/codes	get_beta_codes()	Get beta codes
19	POST	/codes	create_beta_code()	Create beta code
20	GET	/codes/validate/{code}	validate_beta_code()	Validate beta code
21	DELETE	/codes/{code_id}	delete_beta_code()	Delete beta code
22	PUT	/codes/{code_id}/status	update_beta_code_status()	Update code status
23	GET	/users	get_beta_users()	Get beta users
24	POST	/users	create_beta_user()	Create beta user
25	GET	/users/stats	get_beta_stats()	Beta statistics
26	DELETE	/users/{user_id}	delete_beta_user()	Delete beta user
27	PUT	/users/{user_id}/access	update_beta_user_access()	Update user access
1.6 Admin - Bulk (/api/admin/bulk)
#	Method	Endpoint	Function	Summary
28	DELETE	/documents/bulk	bulk_delete_documents()	Bulk delete documents
29	POST	/documents/status	bulk_update_document_status()	Bulk update document status
30	POST	/organizations/status	bulk_update_organization_status()	Bulk update organization status
1.7 Admin - Dashboard (/api/admin/dashboard) ✅ NEW
#	Method	Endpoint	Function	Summary
31	GET	/stats	get_admin_dashboard_stats()	Overall dashboard stats
32	GET	/documents	get_document_overview()	Document overview
33	GET	/staff	get_staff_performance()	Staff performance
34	GET	/organizations	get_organization_health()	Organization health
35	GET	/sla	get_sla_compliance()	SLA compliance
36	GET	/system	get_system_health()	System health
37	GET	/queue	get_queue_overview()	Queue overview
38	GET	/export	export_dashboard_data()	Export dashboard data
1.8 Admin - DEFRA (/api/admin/defra)
#	Method	Endpoint	Function	Summary
39	GET	/activities	get_defra_activities()	Get DEFRA activities
40	GET	/factors	get_admin_defra_factors()	Get DEFRA factors
41	POST	/factors	create_defra_factor()	Create DEFRA factor
42	POST	/factors/bulk	create_defra_factors_bulk()	Bulk create factors
43	GET	/factors/{factor_id}	get_defra_factor()	Get factor detail
44	PUT	/factors/{factor_id}	update_defra_factor()	Update factor
45	DELETE	/factors/{factor_id}	delete_defra_factor()	Delete factor
46	GET	/validate	validate_defra_factor()	Validate factor
47	GET	/years	get_defra_years()	Get available years
1.9 Admin - Email Templates (/api/admin/email)
#	Method	Endpoint	Function	Summary
48	GET	/templates	get_email_templates()	Get templates
49	POST	/templates	create_email_template()	Create template
50	POST	/reset-defaults	reset_to_default_templates()	Reset to defaults
51	GET	/types	get_template_types()	Get template types
52	GET	/templates/{template_id}	get_email_template()	Get template
53	PUT	/templates/{template_id}	update_email_template()	Update template
54	DELETE	/templates/{template_id}	delete_email_template()	Delete template
55	POST	/templates/{template_id}/preview	preview_email_template()	Preview template
1.10 Admin - Extraction (/api/admin/extraction)
#	Method	Endpoint	Function	Summary
56	POST	/approve	approve_extraction()	Approve extraction
57	POST	/batch/approve	approve_pdf_batch()	Approve PDF batch
58	POST	/manual-review-note	add_manual_review_note()	Add review note
59	GET	/reviews/pending	get_pending_reviews()	Get pending reviews
1.11 Admin - Logs (/api/admin/logs)
#	Method	Endpoint	Function	Summary
60	GET	/email	get_email_logs()	Get email logs
61	GET	/email/email/{email_address}	get_email_logs_by_email()	Get logs by email
62	GET	/email/stats	get_email_stats()	Email statistics
63	GET	/email/{log_id}	get_email_log_detail()	Get email log detail
64	GET	/processing	get_processing_logs()	Get processing logs
65	GET	/processing/file/{file_id}	get_processing_logs_by_file()	Get logs by file
66	GET	/processing/stats	get_processing_stats()	Processing statistics
67	GET	/processing/{log_id}	get_processing_log_detail()	Get processing log detail
1.12 Admin - Permissions (/api/admin/permissions)
#	Method	Endpoint	Function	Summary
68	GET	/permissions/list	list_available_permissions()	List permissions
69	GET	/roles	get_roles()	Get roles
70	POST	/roles	create_role()	Create role
71	GET	/roles/{role_id}	get_role()	Get role
72	PUT	/roles/{role_id}	update_role()	Update role
73	DELETE	/roles/{role_id}	delete_role()	Delete role
74	POST	/setup-defaults	setup_default_roles()	Setup default roles
1.13 Admin - Review History (/api/admin/review-history)
#	Method	Endpoint	Function	Summary
75	GET	/history	get_all_review_history()	Get review history
76	GET	/history/audit	get_review_audit_trail()	Get audit trail
77	GET	/history/audit/export	export_review_audit_trail()	Export audit trail
78	GET	/history/staff/{staff_id}	get_staff_assignment_history()	Staff assignment history
79	GET	/{review_id}/history	get_review_history()	Get review history
1.14 Admin - Reviews (/api/admin/reviews)
#	Method	Endpoint	Function	Summary
80	GET	/my-queue	get_my_review_queue()	My review queue
81	POST	/my-queue/{review_id}/start	start_review()	Start review
82	GET	/queue	get_review_queue()	Review queue
83	POST	/queue/escalate	escalate_review()	Escalate review
84	GET	/queue/priority	get_priority_queue()	Priority queue
85	POST	/queue/reorder	reorder_queue()	Reorder queue
86	GET	/queue/sla-monitor	get_sla_monitor()	SLA monitor
87	GET	/queue/stats/detailed	get_detailed_queue_stats()	Detailed queue stats
88	GET	/{review_id}	get_review_details()	Get review details
89	POST	/{review_id}/assign	assign_review()	Assign review
90	POST	/{review_id}/complete	complete_review()	Complete review
91	POST	/{review_id}/reject	reject_review()	Reject review
1.15 Admin - Settings (/api/admin/settings)
#	Method	Endpoint	Function	Summary
92	POST	/reset	reset_settings()	Reset settings
93	GET	/settings-history	get_settings_history()	Settings history
94	POST	/validate	validate_settings()	Validate settings
1.16 Admin - Staff (/api/admin/staff)
#	Method	Endpoint	Function	Summary
95	GET	``	get_all_staff()	Get all staff
96	POST	/	create_staff_member()	Create staff
97	GET	/activity	get_staff_activity()	Staff activity
98	GET	/me	get_my_staff_profile()	My staff profile
99	GET	/performance	get_staff_performance()	Staff performance
100	GET	/performance/export	export_staff_performance()	Export performance
101	GET	/{staff_id}	get_staff_member()	Get staff member
102	PUT	/{staff_id}	update_staff_member()	Update staff
103	DELETE	/{staff_id}	delete_staff_member()	Delete staff
104	GET	/{staff_id}/activity-log	get_staff_activity_log()	Staff activity log
105	GET	/{staff_id}/performance-history	get_staff_performance_history()	Performance history
106	POST	/{staff_id}/reset-password	reset_staff_password()	Reset password
107	PUT	/{staff_id}/role	update_staff_role()	Update role
1.17 Admin - Workload (/api/admin/workload)
#	Method	Endpoint	Function	Summary
108	POST	/queue/reassign	reassign_review()	Reassign review
109	GET	/queue/settings	get_queue_settings()	Get queue settings
110	PUT	/queue/settings	update_queue_settings()	Update queue settings
111	GET	/queue/stats	get_queue_stats()	Queue statistics
112	GET	/staff/workload	get_staff_workload_endpoint()	Staff workload
113	GET	/staff/workload/{staff_id}	get_staff_workload_detail()	Staff workload detail
2. ORGANIZATION ENDPOINTS (76 endpoints)
2.1 Organizations - Analytics (/api/organizations/analytics)
#	Method	Endpoint	Function	Summary
114	GET	/asset-performance	get_asset_performance()	Asset performance
115	GET	/emissions-trend	get_emissions_trend()	Emissions trend
116	GET	/scope-comparison	get_scope_comparison()	Scope comparison
117	GET	/summary	get_analytics_summary()	Analytics summary
2.2 Organizations - Assets (/api/organizations/{org_id})
#	Method	Endpoint	Function	Summary
118	GET	/assets	get_assets()	Get assets
119	POST	/assets	create_asset()	Create asset
120	POST	/assets/bulk/update	bulk_update_assets()	Bulk update assets
121	GET	/assets/stats	get_asset_stats_endpoint()	Asset statistics
122	PUT	/assets/{asset_id}	update_asset()	Update asset
123	PATCH	/assets/{asset_id}	patch_asset()	Patch asset
124	DELETE	/assets/{asset_id}	delete_asset()	Delete asset
125	GET	/facilities	get_facilities()	Get facilities
126	POST	/facilities	create_facility()	Create facility
127	GET	/facilities/stats	get_facility_stats_endpoint()	Facility statistics
128	PUT	/facilities/{facility_id}	update_facility()	Update facility
129	PATCH	/facilities/{facility_id}	patch_facility()	Patch facility
130	DELETE	/facilities/{facility_id}	delete_facility()	Delete facility
131	POST	/facilities/{facility_id}/status	update_facility_status()	Update facility status
2.3 Organizations - Bulk (/api/organizations/{org_id})
#	Method	Endpoint	Function	Summary
132	POST	/assets/bulk/create	bulk_create_assets()	Bulk create assets
133	POST	/members/bulk/invite	bulk_invite_members()	Bulk invite members
2.4 Organizations - Dashboard (/api/organizations/dashboard)
#	Method	Endpoint	Function	Summary
134	GET	/dashboard-summary	get_dashboard_summary()	Dashboard summary
135	GET	/organization-activity	get_organization_activity()	Organization activity
2.5 Organizations - Data (/api/organizations/{org_id})
#	Method	Endpoint	Function	Summary
136	GET	/assets	get_organization_assets()	Get organization assets
137	GET	/defra-factors	get_organization_defra_factors()	Get DEFRA factors
138	GET	/emissions-data	get_organization_emissions()	Get emissions data
139	GET	/emissions/export-csv	export_emissions_csv()	Export emissions CSV
2.6 Organizations - Exports (/api/organizations/exports)
#	Method	Endpoint	Function	Summary
140	GET	``	get_exports()	Get exports
141	POST	/exports/emissions	export_emissions_data()	Export emissions
142	DELETE	/{export_id}	delete_export()	Delete export
143	GET	/{export_id}/download	download_export()	Download export
2.7 Organizations - Files (/api/organizations/{org_id}/files)
#	Method	Endpoint	Function	Summary
144	GET	/	get_organization_files()	Get files
145	POST	/upload	upload_file()	Upload file
146	POST	/bulk-upload	bulk_upload_files()	Bulk upload
147	GET	/stats	get_file_stats()	File statistics
148	DELETE	/{file_id}	delete_file()	Delete file
149	GET	/{file_id}/download	download_file()	Download file
150	GET	/{file_id}/url	get_file_download_url_endpoint()	Get download URL
151	GET	/archived	get_archived_files()	Get archived files
152	POST	/{file_id}/archive	archive_file()	Archive file
153	DELETE	/{file_id}/permanent	permanent_delete_file()	Permanent delete
154	POST	/{file_id}/restore	restore_file()	Restore file
2.8 Organizations - Management (/api/organizations)
#	Method	Endpoint	Function	Summary
155	POST	/	create_organization()	Create organization
156	GET	/{org_id}	get_organization()	Get organization
157	PUT	/{org_id}	update_organization()	Update organization
158	DELETE	/{org_id}	delete_organization()	Delete organization
159	GET	/{org_id}/metadata	get_organization_metadata()	Get metadata
160	PUT	/{org_id}/metadata	update_organization_metadata()	Update metadata
161	GET	/{org_id}/stats	get_organization_stats_endpoint()	Organization stats
2.9 Organizations - Members (/api/organizations/{org_id}/members)
#	Method	Endpoint	Function	Summary
162	GET	/	get_organization_members()	Get members
163	POST	/invite	invite_organization_member()	Invite member
164	PUT	/{member_id}	update_organization_member()	Update member
165	DELETE	/{member_id}	remove_organization_member()	Remove member
166	POST	/{member_id}/resend-invite	resend_invitation()	Resend invitation
167	POST	/bulk/remove	bulk_remove_members()	Bulk remove members
168	POST	/bulk/update	bulk_update_members()	Bulk update members
169	GET	/roles	get_member_roles()	Get member roles
170	GET	/stats	get_member_stats()	Member statistics
2.10 Organizations - Metadata (/api/organizations/{org_id}/metadata)
#	Method	Endpoint	Function	Summary
171	GET	/all	get_all_metadata()	Get all metadata
172	GET	/contacts	get_contact_metadata()	Contact metadata
173	PUT	/contacts	update_contact_metadata()	Update contacts
174	GET	/custom-metrics	get_custom_metrics()	Custom metrics
175	PUT	/custom-metrics	update_custom_metrics()	Update custom metrics
176	GET	/employees	get_employee_metadata()	Employee metadata
177	PUT	/employees	update_employee_metadata()	Update employees
178	GET	/financials	get_financial_metadata()	Financial metadata
179	PUT	/financials	update_financial_metadata()	Update financials
180	GET	/industry	get_industry_metadata()	Industry metadata
181	PUT	/industry	update_industry_metadata()	Update industry
182	GET	/required-fields	get_required_metadata_fields()	Required fields
183	GET	/sustainability	get_sustainability_metadata()	Sustainability metadata
184	PUT	/sustainability	update_sustainability_metadata()	Update sustainability
185	POST	/validate	validate_metadata()	Validate metadata
2.11 Organizations - Team (/api/organizations/{org_id})
#	Method	Endpoint	Function	Summary
186	POST	/invite	invite_team_member()	Invite team member
187	GET	/members	get_team_members()	Get team members
188	PATCH	/members/{member_id}	update_member_role()	Update member role
189	DELETE	/members/{member_id}	remove_member()	Remove member
3. DOCUMENT ENDPOINTS (19 endpoints)
3.1 Documents - Main (/api/documents)
#	Method	Endpoint	Function	Summary
190	GET	/	get_documents()	Get documents
191	POST	/admin/{file_id}/status	update_document_status()	Update document status
192	GET	/stats	get_document_stats()	Document statistics
193	POST	/{file_id}/review	customer_review_document()	Customer review document
194	GET	/{file_id}/status	get_document_status()	Get document status
3.2 Documents - Activity (/api/documents)
#	Method	Endpoint	Function	Summary
195	GET	/{file_id}/activity	get_document_activity()	Document activity
196	GET	/{file_id}/activity/export	export_document_activity()	Export activity
197	GET	/{file_id}/reviews	get_document_reviews()	Document reviews
198	POST	/{file_id}/review/response	respond_to_review()	Respond to review
199	GET	/admin/reviews/customer	get_customer_reviews_admin()	Customer reviews admin
200	GET	/organizations/{org_id}/documents/activity	get_organization_document_activity()	Organization activity
4. CUSTOMER DOCUMENTS (9 endpoints)
4.1 Customer Documents (/api/customer-documents)
#	Method	Endpoint	Function	Summary
201	GET	/	get_customer_documents()	Get customer documents
202	GET	/stats	get_customer_document_stats()	Document statistics
203	GET	/pending	get_pending_customer_reviews()	Pending reviews
204	GET	/assets	get_documents_by_asset()	Documents by asset
205	GET	/assets/{asset_id}	get_documents_for_asset()	Documents for asset
206	GET	/{document_id}	get_customer_document()	Get document detail
207	GET	/{document_id}/extraction	get_extraction_details()	Extraction details
208	POST	/{document_id}/verify	verify_customer_document()	Verify document
209	POST	/{document_id}/request-review	request_staff_review()	Request staff review
5. CUSTOMER DASHBOARD (7 endpoints) ✅ NEW
5.1 Customer Dashboard (/api/customer/dashboard)
#	Method	Endpoint	Function	Summary
210	GET	/stats	get_customer_dashboard_stats()	Dashboard statistics
211	GET	/documents	get_customer_documents_overview()	Document overview
212	GET	/assets	get_customer_asset_performance()	Asset performance
213	GET	/emissions	get_customer_emissions_overview()	Emissions overview
214	GET	/pending	get_customer_pending_actions()	Pending actions
215	GET	/activity	get_customer_recent_activity()	Recent activity
216	GET	/notifications	get_customer_notifications()	Notifications
6. CUSTOMER VERIFICATIONS (6 endpoints) ✅ NEW
6.1 Customer Verifications (/api/customer/verifications)
#	Method	Endpoint	Function	Summary
217	GET	/	get_customer_verifications()	Get verifications
218	GET	/{verification_id}	get_customer_verification_detail()	Get verification detail
219	POST	/	submit_customer_verification()	Submit verification
220	PUT	/{verification_id}/approve	approve_customer_verification()	Approve verification
221	PUT	/{verification_id}/reject	reject_customer_verification()	Reject verification
222	PUT	/{verification_id}/revision	request_verification_revision()	Request revision
7. COMMUNICATION (14 endpoints) ✅ NEW
7.1 Communication - Messages (/api/communication)
#	Method	Endpoint	Function	Summary
223	POST	/messages	send_message()	Send message
224	GET	/messages	get_messages()	Get messages
225	GET	/messages/{message_id}	get_message_detail()	Get message detail
226	PUT	/messages/{message_id}/read	mark_message_read()	Mark message as read
227	DELETE	/messages/{message_id}	delete_message()	Delete message
7.2 Communication - Conversations
#	Method	Endpoint	Function	Summary
228	GET	/conversations	get_conversations()	Get conversations
229	GET	/conversations/{conversation_id}	get_conversation()	Get conversation
230	POST	/conversations	start_conversation()	Start conversation
231	PUT	/conversations/{conversation_id}/close	close_conversation()	Close conversation
232	PUT	/conversations/{conversation_id}/archive	archive_conversation()	Archive conversation
7.3 Communication - Notifications
#	Method	Endpoint	Function	Summary
233	GET	/notifications	get_notifications()	Get notifications
234	GET	/notifications/unread	get_unread_notifications()	Get unread count
235	PUT	/notifications/{notification_id}/read	mark_notification_read()	Mark notification as read
236	PUT	/notifications/mark-all-read	mark_all_notifications_read()	Mark all as read
8. REFERENCE ENDPOINTS (7 endpoints)
8.1 Reference (/api/reference)
#	Method	Endpoint	Function	Summary
237	GET	/asset-types	get_asset_types()	Get asset types
238	GET	/assets	get_assets_list()	Get assets list
239	GET	/categories	get_reference_categories()	Get categories
240	GET	/facilities	get_facilities_list()	Get facilities list
241	GET	/facility-types	get_facility_types()	Get facility types
242	GET	/fuel-types	get_fuel_types()	Get fuel types
243	GET	/units	get_units()	Get units
9. REPORT ENDPOINTS (10 endpoints)
9.1 Reports (/api/reports)
#	Method	Endpoint	Function	Summary
244	POST	/admin/import-defra-factors	import_defra_factors()	Import DEFRA factors
245	GET	/defra-factors/{reporting_year}	get_defra_factors_by_year()	Get DEFRA factors
246	GET	/defra-mapping	get_defra_mapping()	Get DEFRA mapping
247	POST	/generate-enhanced-report	generate_enhanced_sustainability_report()	Generate enhanced report
248	GET	/report_status	report_service_status()	Report service status
9.2 Reports - Enhanced (/api/reports) ✅ NEW
#	Method	Endpoint	Function	Summary
249	GET	/customer/summary	get_customer_summary_report()	Customer summary report
250	GET	/admin/staff-performance	get_staff_performance_report()	Staff performance report
251	GET	/admin/organization-comparison	get_organization_comparison_report()	Organization comparison
252	GET	/emissions/trend	get_emissions_trend_report()	Emissions trend report
253	POST	/generate	generate_custom_report()	Generate custom report
10. OTHER ENDPOINTS (79 endpoints)
10.1 Drafts (/api/drafts)
#	Method	Endpoint	Function	Summary
254	GET	/	get_drafts()	Get drafts
255	POST	/save	save_draft()	Save draft
256	GET	/{draft_id}	get_draft()	Get draft
257	DELETE	/{draft_id}	delete_draft()	Delete draft
258	POST	/{draft_id}/submit	submit_draft()	Submit draft
10.2 Drafts - Enhanced (/api/drafts)
#	Method	Endpoint	Function	Summary
259	GET	/{draft_id}/progress	get_draft_progress()	Get draft progress
260	POST	/{draft_id}/publish	publish_draft()	Publish draft
261	GET	/{draft_id}/sections	get_draft_sections()	Get draft sections
262	POST	/{draft_id}/sections/{section_id}	update_draft_section()	Update draft section
263	DELETE	/{draft_id}/sections/{section_id}	delete_draft_section()	Delete draft section
264	POST	/{draft_id}/validate	validate_draft()	Validate draft
10.3 Emissions (/api/emissions)
#	Method	Endpoint	Function	Summary
265	POST	/emissions	create_emission_record()	Create emission record
266	GET	/emissions	get_emissions()	Get emissions
267	POST	/emissions/bulk	bulk_create_emissions()	Bulk create emissions
268	GET	/emissions/export	export_emissions()	Export emissions
269	GET	/emissions/stats	get_emission_stats()	Emission statistics
270	POST	/emissions/verify	verify_emissions()	Verify emissions
271	DELETE	/emissions/{record_id}	delete_emission_record()	Delete emission record
272	PUT	/emissions/{record_id}	update_emission_record()	Update emission record
10.4 Feedback (/api/feedback)
#	Method	Endpoint	Function	Summary
273	POST	/	submit_feedback()	Submit feedback
274	GET	/	get_user_feedback()	Get user feedback
275	GET	/{feedback_id}	get_feedback_detail()	Get feedback detail
276	PUT	/{feedback_id}	update_feedback_status()	Update feedback status
10.5 Glossary (/api/glossary)
#	Method	Endpoint	Function	Summary
277	GET	/	get_glossary()	Get glossary
278	POST	/	create_glossary_term()	Create glossary term
279	GET	/categories	get_glossary_categories()	Get glossary categories
280	GET	/search	search_glossary()	Search glossary
281	GET	/{term_id}	get_glossary_term()	Get glossary term
282	PUT	/{term_id}	update_glossary_term()	Update glossary term
283	DELETE	/{term_id}	delete_glossary_term()	Delete glossary term
284	POST	/{term_id}/restore	restore_glossary_term()	Restore glossary term
10.6 Logs (/api/logs)
#	Method	Endpoint	Function	Summary
285	POST	/	create_log()	Create log
286	GET	/	get_logs()	Get logs
287	GET	/analytics/errors	get_error_logs()	Get error logs
288	GET	/analytics/stats	get_log_stats()	Log statistics
289	GET	/analytics/users	get_user_activity()	User activity
290	GET	/documents/{file_id}	get_document_logs()	Document logs
10.7 Notifications (/api/notifications)
#	Method	Endpoint	Function	Summary
291	POST	/batch/completion	notify_batch_completion()	Notify batch completion
292	POST	/customer/manual-extraction	notify_customer_manual_extraction()	Notify customer
293	POST	/staff	notify_staff()	Notify staff
294	GET	/templates	get_notification_templates()	Get notification templates
10.8 Upload (/api/upload)
#	Method	Endpoint	Function	Summary
295	GET	/batches/stats	get_batch_stats()	Get batch statistics
296	POST	/batches/{batch_id}/cancel	cancel_batch()	Cancel batch
297	GET	/batches/{batch_id}/progress	get_batch_progress()	Get batch progress
298	GET	/batches/{batch_id}/status	get_batch_status()	Get batch status
299	POST	/repair-pdf	repair_pdf()	Repair PDF
300	POST	/test-upload	test_upload()	Test upload
301	POST	/upload	upload_document()	Upload document
302	POST	/upload-batch	upload_batch()	Upload batch
303	POST	/upload-csv	upload_csv()	Upload CSV
304	POST	/upload-pdf	upload_pdf()	Upload PDF
10.9 Users (/api/users)
#	Method	Endpoint	Function	Summary
305	POST	/change-password	change_password()	Change password
306	POST	/password-reset	request_password_reset()	Request password reset
307	POST	/password-reset/confirm	confirm_password_reset()	Confirm password reset
308	GET	/profile	get_user_profile()	Get user profile
309	PUT	/profile	update_user_profile()	Update user profile
10.10 Waitlist (/api/waitlist)
#	Method	Endpoint	Function	Summary
310	POST	/	add_to_waitlist()	Add to waitlist
311	GET	/	get_waitlist()	Get waitlist
10.11 Customer Documents Organization (/api/customer-documents) ✅ NEW
#	Method	Endpoint	Function	Summary
312	POST	/{document_id}/organize	organize_document_for_customer()	Staff organizes document
10.12 Document Types (/api/document-types) ✅ NEW
#	Method	Endpoint	Function	Summary
313	GET	/	get_document_types()	Get all document types
314	GET	/stats	get_document_type_stats()	Document type statistics
ENDPOINT SUMMARY
Category	Count
Admin	123
Organization	76
Documents	19
Customer Documents	9
Customer Dashboard	7
Customer Verifications	6
Communication	14
Reference	7
Reports	10
Other	41
TOTAL	332
API Version
Current Version: v2.0.0

Base URL: http://localhost:8000/api/

Authentication: Bearer Token (JWT)

Content-Type: application/json




## Changelog - July 2026

### Added
- `routes/customer_dashboard.py` - Customer dashboard endpoints
- `routes/admin/dashboard.py` - Admin dashboard endpoints
- `routes/communication.py` - Communication endpoints
- `routes/admin/audit_logs.py` - Audit log endpoints
- `routes/customer_verifications.py` - Verification endpoints
- New tables: audit_logs, conversations, messages, notifications, etc.
- Complete audit trail system
- Customer verification workflow

### Modified
- `routes/customer_documents.py` - Added new endpoints
- `routes/reports.py` - Added new report types
- `routes/organizations/dashboard.py` - Enhanced with new data

### Removed
- `routes/admin/staff_enhanced_bak.py` - Backup file no longer needed

### Fixed
- All `group_by` and `clone()` issues
- Route ordering conflicts
- Deprecated datetime usage


Documentation Note to Keep:
markdown
## Database Changes - Customer Documents (2026-07-28)

### New Table: `customer_documents`
Purpose: Track customer-uploaded documents and link them to assets.

Columns:
- id: UUID (Primary Key)
- organization_id: UUID → organizations(id)
- organization_member_id: UUID → organization_members(id)
- asset_id: UUID → assets(id)
- file_name, file_url, file_type
- status: pending, processing, extracted, approved, rejected
- manual_review_queue_id: UUID → manual_review_queue(id)
- upload_date, created_at, updated_at

### Modified Table: `manual_review_queue`
Added column:
- customer_document_id: UUID → customer_documents(id)

### Purpose:
1. Track which asset a document belongs to
2. Complete audit trail from upload to emission record
3. Enable customer verification of extracted data
4. Better workflow management

Dashboard Recommendations for Customer & Admin Dashboards
Based on your new customer_documents table and the complete workflow (upload → extraction → verification → emissions), here are the recommended dashboard changes:

1. Customer Dashboard (Customer View)
Current State
Likely shows: Document status, emissions overview, basic stats

Recommended Additions
A. Document Status Widget
python
# New endpoint: GET /api/customer-documents/stats
{
    "total_documents": 45,
    "by_status": {
        "pending": 5,      # Awaiting extraction
        "processing": 3,   # Being processed
        "extracted": 2,    # Ready for review
        "approved": 30,    # Customer approved
        "rejected": 5      # Customer rejected
    },
    "by_asset": {
        "asset_id_1": {"total": 10, "approved": 8},
        "asset_id_2": {"total": 8, "approved": 6}
    },
    "pending_review": 2,   # Awaiting customer action
    "needs_attention": 5   # Rejected or flagged
}
B. Asset Performance Widget
python
# New endpoint: GET /api/customer-documents/assets/performance
{
    "assets": [
        {
            "id": "asset_1",
            "name": "Vehicle A",
            "total_documents": 12,
            "approved_documents": 10,
            "pending_review": 1,
            "total_emissions_tonnes": 45.5,
            "last_upload": "2024-01-15T10:30:00Z"
        }
    ],
    "summary": {
        "total_assets": 5,
        "total_documents": 45,
        "total_emissions_tonnes": 189.3
    }
}
C. Document Review Queue Widget
python
# New endpoint: GET /api/customer-documents/pending-review
{
    "pending_reviews": [
        {
            "id": "doc_123",
            "file_name": "Fuel_Slip_ABC123.pdf",
            "asset_name": "Vehicle A",
            "uploaded_at": "2024-01-14T09:00:00Z",
            "extraction_data": {
                "consumption": 45.5,
                "fuel_type": "Diesel",
                "asset_name": "Vehicle A"
            },
            "customer_notes": "Please verify this fuel slip"
        }
    ],
    "total": 3,
    "urgent": 1  # SLA approaching
}
D. Emissions Overview Widget
python
# Existing emissions stats but filtered by customer documents
{
    "total_emissions_tonnes": 189.3,
    "by_scope": {
        "scope_1": 120.5,
        "scope_2": 45.8,
        "scope_3": 23.0
    },
    "by_asset": {
        "Vehicle A": 45.5,
        "Vehicle B": 38.2,
        "Equipment C": 25.1
    },
    "trend": "decreasing",  # Compared to previous period
    "percentage_change": -5.2
}
Customer Dashboard API Endpoints
python
# backend/routes/customer_dashboard.py

@router.get("/dashboard/stats")
async def get_customer_dashboard_stats(
    current_user: AuthUser = Depends(require_org_member())
):
    """Get customer dashboard statistics."""
    try:
        supabase = get_supabase_client()
        org_id = current_user.organization_id
        
        # Get document stats
        doc_stats = await get_customer_document_stats(supabase, org_id)
        
        # Get asset performance
        asset_performance = await get_asset_performance(supabase, org_id)
        
        # Get pending reviews
        pending_reviews = await get_pending_customer_reviews(supabase, org_id)
        
        # Get emissions summary
        emissions_summary = await get_customer_emissions_summary(supabase, org_id)
        
        return {
            "success": True,
            "document_stats": doc_stats,
            "asset_performance": asset_performance,
            "pending_reviews": pending_reviews,
            "emissions_summary": emissions_summary,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
2. Admin Dashboard (Admin/Staff View)
Current State
Likely shows: Staff workload, queue stats, system health

Recommended Additions
A. Customer Document Overview Widget
python
# New endpoint: GET /api/admin/dashboard/customer-documents
{
    "total_customer_documents": 345,
    "by_organization": {
        "org_1": {"total": 45, "pending": 5, "approved": 30},
        "org_2": {"total": 78, "pending": 12, "approved": 55}
    },
    "by_status": {
        "pending": 25,      # Awaiting extraction
        "processing": 15,   # Staff working on them
        "extracted": 10,    # Awaiting admin approval
        "approved": 250,    # Customer approved
        "rejected": 45      # Customer rejected
    },
    "by_asset_type": {
        "vehicle": 180,
        "equipment": 95,
        "facility": 70
    },
    "total_emissions_tonnes": 1245.8
}
B. Staff Performance Widget (Enhanced)
python
# Enhanced with customer document metrics
{
    "staff_performance": [
        {
            "staff_id": "staff_1",
            "name": "John Doe",
            "documents_extracted": 45,
            "avg_extraction_time": 12.5,  # minutes
            "accuracy_rate": 95.2,
            "pending_count": 3,
            "current_workload": 8  # documents in queue
        }
    ],
    "team_summary": {
        "total_extracted": 234,
        "avg_accuracy": 94.8,
        "avg_time": 14.2,
        "total_pending": 25
    }
}
C. Organization Health Widget
python
# New endpoint: GET /api/admin/dashboard/organization-health
{
    "organizations": [
        {
            "id": "org_1",
            "name": "Acme Corp",
            "total_documents": 45,
            "documents_this_month": 12,
            "approval_rate": 85.2,
            "avg_extraction_time": 18.5,
            "total_emissions_tonnes": 234.5,
            "status": "active",
            "last_activity": "2024-01-15T10:30:00Z"
        }
    ],
    "summary": {
        "total_organizations": 25,
        "active_organizations": 20,
        "total_documents": 2345,
        "total_emissions_tonnes": 12450.8
    }
}
D. SLA Compliance Widget
python
# New endpoint: GET /api/admin/dashboard/sla-compliance
{
    "sla_metrics": {
        "breached": 3,
        "at_risk": 5,
        "on_track": 42,
        "compliance_rate": 89.4
    },
    "breached_reviews": [
        {
            "id": "review_123",
            "file_name": "Fuel_Slip_XYZ.pdf",
            "organization": "Acme Corp",
            "assigned_to": "John Doe",
            "created_at": "2024-01-10T09:00:00Z",
            "sla_deadline": "2024-01-12T09:00:00Z",
            "breach_hours": 48
        }
    ]
}
Admin Dashboard API Endpoints
python
# backend/routes/admin/dashboard.py

@router.get("/dashboard/admin/stats")
async def get_admin_dashboard_stats(
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Get admin dashboard statistics."""
    try:
        supabase = get_supabase_client()
        
        # Get customer document overview
        doc_overview = await get_customer_document_overview(supabase)
        
        # Get staff performance
        staff_performance = await get_staff_performance_metrics(supabase)
        
        # Get organization health
        org_health = await get_organization_health(supabase)
        
        # Get SLA compliance
        sla_compliance = await get_sla_compliance(supabase)
        
        # Get system health
        system_health = await get_system_health_metrics(supabase)
        
        return {
            "success": True,
            "document_overview": doc_overview,
            "staff_performance": staff_performance,
            "organization_health": org_health,
            "sla_compliance": sla_compliance,
            "system_health": system_health,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
3. New Database Functions for Dashboard
sql
-- Customer document stats function
CREATE OR REPLACE FUNCTION get_customer_document_stats(org_id UUID)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_documents', COUNT(*),
        'by_status', json_build_object(
            'pending', COUNT(*) FILTER (WHERE status = 'pending'),
            'processing', COUNT(*) FILTER (WHERE status = 'processing'),
            'extracted', COUNT(*) FILTER (WHERE status = 'extracted'),
            'approved', COUNT(*) FILTER (WHERE status = 'approved'),
            'rejected', COUNT(*) FILTER (WHERE status = 'rejected')
        ),
        'by_asset', (
            SELECT json_agg(
                json_build_object(
                    'asset_id', a.id,
                    'asset_name', a.name,
                    'total', COUNT(cd.id),
                    'approved', COUNT(*) FILTER (WHERE cd.status = 'approved')
                )
            )
            FROM customer_documents cd
            JOIN assets a ON a.id = cd.asset_id
            WHERE cd.organization_id = org_id
            GROUP BY a.id, a.name
        ),
        'pending_review', COUNT(*) FILTER (WHERE status = 'extracted'),
        'needs_attention', COUNT(*) FILTER (WHERE status = 'rejected')
    ) INTO result
    FROM customer_documents
    WHERE organization_id = org_id;
    
    RETURN result;
END;
$$;

-- Admin document overview function
CREATE OR REPLACE FUNCTION get_admin_document_overview()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_documents', COUNT(*),
        'by_organization', (
            SELECT json_agg(
                json_build_object(
                    'organization_id', o.id,
                    'organization_name', o.name,
                    'total', COUNT(cd.id),
                    'pending', COUNT(*) FILTER (WHERE cd.status = 'pending'),
                    'approved', COUNT(*) FILTER (WHERE cd.status = 'approved')
                )
            )
            FROM organizations o
            LEFT JOIN customer_documents cd ON cd.organization_id = o.id
            GROUP BY o.id, o.name
        ),
        'by_status', json_build_object(
            'pending', COUNT(*) FILTER (WHERE status = 'pending'),
            'processing', COUNT(*) FILTER (WHERE status = 'processing'),
            'extracted', COUNT(*) FILTER (WHERE status = 'extracted'),
            'approved', COUNT(*) FILTER (WHERE status = 'approved'),
            'rejected', COUNT(*) FILTER (WHERE status = 'rejected')
        )
    ) INTO result
    FROM customer_documents;
    
    RETURN result;
END;
$$;

-- SLA compliance function
CREATE OR REPLACE FUNCTION get_sla_compliance()
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'breached', COUNT(*) FILTER (WHERE sla_breached = true),
        'at_risk', COUNT(*) FILTER (WHERE 
            sla_deadline > NOW() AND 
            sla_deadline < NOW() + INTERVAL '4 hours'
        ),
        'on_track', COUNT(*) FILTER (WHERE 
            sla_breached = false AND 
            (sla_deadline IS NULL OR sla_deadline > NOW() + INTERVAL '4 hours')
        ),
        'compliance_rate', ROUND(
            (COUNT(*) FILTER (WHERE sla_breached = false)::DECIMAL / COUNT(*) * 100),
            2
        )
    ) INTO result
    FROM manual_review_queue
    WHERE status IN ('assigned', 'in_progress');
    
    RETURN result;
END;
$$;
4. Dashboard Widget Recommendations
Customer Dashboard Widgets
Widget	Priority	Data Source	Refresh Rate
Document Status Summary	High	customer_documents	Real-time
Pending Reviews Queue	High	customer_documents + manual_review_queue	Real-time
Asset Performance	High	customer_documents + assets	Daily
Emissions Overview	Medium	emissions_logs	Real-time
Recent Activity	Medium	customer_documents + document_activity_log	Real-time
Quick Actions (Upload)	High	-	-
Admin Dashboard Widgets
Widget	Priority	Data Source	Refresh Rate
Document Overview	High	customer_documents	Real-time
Staff Performance	High	staff_profiles + manual_review_queue	Real-time
SLA Compliance	High	manual_review_queue	Real-time
Organization Health	Medium	customer_documents + organizations	Daily
Queue Stats	High	manual_review_queue	Real-time
System Health	Medium	system_settings + logs	Real-time
5. Recommended Route Structure
python
# backend/routes/customer_dashboard.py
@router.get("/dashboard/stats")           # Main dashboard stats
@router.get("/dashboard/documents")       # Document list with filters
@router.get("/dashboard/assets")          # Asset performance
@router.get("/dashboard/emissions")       # Emissions summary
@router.get("/dashboard/pending")         # Pending reviews

# backend/routes/admin/dashboard.py
@router.get("/admin/dashboard/stats")      # Admin dashboard
@router.get("/admin/dashboard/documents")  # Document overview
@router.get("/admin/dashboard/staff")      # Staff performance
@router.get("/admin/dashboard/organizations") # Organization health
@router.get("/admin/dashboard/sla")        # SLA compliance
@router.get("/admin/dashboard/system")     # System health
6. Implementation Priority
Phase 1 (Immediate) - High Priority
✅ Customer Document Status Widget

✅ Pending Reviews Queue

✅ Admin Document Overview

✅ Staff Performance Metrics

Phase 2 (Next Sprint) - Medium Priority
Asset Performance Widget

Organization Health Widget

SLA Compliance Widget

Emissions Overview Widget

Phase 3 (Future) - Low Priority
Predictive Analytics

Custom Reports

Export Functionality

Mobile Optimizations

7. Important Note: Existing Routes
Your existing admin/user/customer dashboards already handle basic stats. The new customer_documents table adds:

Asset linking for documents

Complete audit trail from upload to emission record

Customer verification workflow

Better analytics for both customers and admins