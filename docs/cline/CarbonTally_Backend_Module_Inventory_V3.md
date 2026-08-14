# CarbonTally Backend Module Inventory V3

> READ-ONLY automated repository inventory.

This document was generated automatically from the existing CarbonTally backend source tree.

**Important:** heuristic classifications must be reviewed against the actual implementation before making V3 changes.

## 1. Repository

- Root: `D:\carbon_ledger`
- Python modules: **285**
- Classes: **604**
- Top-level functions: **1189**
- API routes detected: **487**
- Parse errors: **2**

## 2. Important Architecture Rule

CarbonTally has two different provider concepts:

1. **Emission-factor providers** — DEFRA, SEAI, EPA, ADEME, IPCC, etc.

2. **Human data-processing providers** — Babui Limited and future processing entities.

This inventory must NOT assume that a generic module containing the word `provider` represents a human processing provider.

## 3. Module Summary

| Module | Package | Lines | Classes | Functions | Routes | DB Tables | Category | Provider Type | V3 Impact |
|---|---|---:|---:|---:|---:|---|---|---|---|
| `admin/serve.py` | `admin` | 68 | 1 | 0 | 0 | build, the | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/auth.py` | `backend` | 549 | 1 | 25 | 0 | auth, database, datetime, dotenv, fastapi, organization_members, pydantic, roles, staff_profiles, supabase, typing | API, Storage, authentication / security | - | EXTEND / REVIEW |
| `backend/config.py` | `backend` | 50 | 1 | 0 | 0 | dotenv, supabase | Storage | - | EXTEND / REVIEW |
| `backend/core/__init__.py` | `backend` | 49 | 0 | 0 | 0 | any | audit / logging | - | NO DIRECT V3 IMPACT |
| `backend/core/exceptions.py` | `backend.core` | 116 | 13 | 0 | 0 | __future__, typing | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/core/logging.py` | `backend.core` | 45 | 0 | 2 | 0 | __future__ | audit / logging | - | NO DIRECT V3 IMPACT |
| `backend/core/types.py` | `backend.core` | 66 | 3 | 0 | 0 | __future__, dataclasses, datetime, enum, typing | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/data/__init__.py` | `backend` | 31 | 0 | 0 | 0 | - | CSV / Excel, audit / logging, calculation, database / repository, document processing, emission factors, reporting | - | NO CHANGE |
| `backend/data/audit.py` | `backend.data` | 262 | 1 | 3 | 0 | __future__, data, domain, public, typing | AI extraction, CSV / Excel, audit / logging | - | NO CHANGE |
| `backend/data/base.py` | `backend.data` | 169 | 1 | 5 | 0 | JSONB, __future__, abc, decimal, typing | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/data/documents.py` | `backend.data` | 150 | 1 | 1 | 0 | __future__, an, data, datetime, domain, public, the, typing | AI extraction, document processing | - | NO CHANGE |
| `backend/data/emission_factors.py` | `backend.data` | 306 | 1 | 3 | 0 | __future__, data, decimal, domain, its, public, so, typing | AI extraction, calculation, emission factors | - | NO CHANGE |
| `backend/data/emissions_logs.py` | `backend.data` | 313 | 1 | 2 | 0 | __future__, an, core, data, datetime, decimal, domain, public, start_date, typing | AI extraction, audit / logging, calculation | - | NO CHANGE |
| `backend/data/events.py` | `backend.data` | 156 | 1 | 4 | 0 | __future__, data, domain, public, the, typing | AI extraction, audit / logging, workflow | - | NO CHANGE |
| `backend/data/factor_aliases.py` | `backend.data` | 143 | 1 | 1 | 0 | __future__, data, domain, public, typing, when | AI extraction, emission factors, factor matching | - | NO CHANGE |
| `backend/data/imports.py` | `backend.data` | 317 | 1 | 3 | 0 | __future__, a, data, domain, public, the, typing | AI extraction, CSV / Excel, factor provider | - | NO CHANGE |
| `backend/data/organizations.py` | `backend.data` | 227 | 1 | 7 | 0 | __future__, data, domain, public, typing | AI extraction | - | NO CHANGE |
| `backend/data/reports.py` | `backend.data` | 181 | 1 | 2 | 0 | __future__, data, datetime, domain, public, typing | AI extraction, database / repository, reporting | - | NO CHANGE |
| `backend/database.py` | `backend` | 162 | 0 | 6 | 0 | datetime, dotenv, glossary, organizations, supabase | Storage, database / repository | - | EXTEND / REVIEW |
| `backend/domain/__init__.py` | `backend` | 151 | 0 | 0 | 0 | - | AI extraction, audit / logging, calculation, database / repository, document processing, emission factors, factor matching, factor provider, reporting, validation / QA, workflow | - | NO CHANGE |
| `backend/domain/audit.py` | `backend.domain` | 104 | 3 | 0 | 0 | __future__, dataclasses, datetime, typing | AI extraction, audit / logging | - | NO CHANGE |
| `backend/domain/benchmarking.py` | `backend.domain` | 196 | 4 | 0 | 0 | __future__, dataclasses, datetime, decimal, enum, reporting_year, the, typing | AI extraction | - | NO CHANGE |
| `backend/domain/calculation.py` | `backend.domain` | 160 | 6 | 0 | 0 | __future__, core, dataclasses, decimal, domain, enum, inputs, the, typing | AI extraction, calculation, emission factors | - | NO CHANGE |
| `backend/domain/document.py` | `backend.domain` | 81 | 5 | 0 | 0 | __future__, a, dataclasses, datetime, typing | AI extraction, document processing | - | NO CHANGE |
| `backend/domain/factor.py` | `backend.domain` | 156 | 3 | 1 | 0 | __future__, core, dataclasses, datetime, decimal, the, typing | AI extraction, emission factors | - | NO CHANGE |
| `backend/domain/matching.py` | `backend.domain` | 197 | 8 | 0 | 0 | __future__, abc, dataclasses, datetime, domain, typing | AI extraction, emission factors, factor matching | - | NO CHANGE |
| `backend/domain/organization.py` | `backend.domain` | 74 | 5 | 0 | 0 | __future__, dataclasses, datetime, typing | AI extraction | - | NO CHANGE |
| `backend/domain/provider.py` | `backend.domain` | 182 | 9 | 0 | 0 | __future__, a, dataclasses, datetime, typing | AI extraction, factor provider | - | NO CHANGE |
| `backend/domain/report.py` | `backend.domain` | 69 | 4 | 0 | 0 | __future__, dataclasses, datetime, typing | AI extraction, database / repository, reporting | - | NO CHANGE |
| `backend/domain/validation.py` | `backend.domain` | 150 | 4 | 0 | 0 | __future__, core, dataclasses, enum, typing | AI extraction, validation / QA | - | NO CHANGE |
| `backend/domain/workflow.py` | `backend.domain` | 335 | 19 | 0 | 0 | __future__, a, abc, dataclasses, datetime, decimal, the, typing | AI extraction, workflow | - | NO CHANGE |
| `backend/engines/__init__.py` | `backend` | 72 | 0 | 0 | 0 | __future__, engines | AI extraction, calculation, database / repository, emission factors, factor matching, reporting, validation / QA, workflow | - | NO CHANGE |
| `backend/engines/ai_extraction.py` | `backend.engines` | 254 | 1 | 1 | 0 | None, __future__, an, core, datetime, document, domain, engines, exc, infra, the, typing | AI extraction, audit / logging, document processing, workflow | - | NO CHANGE |
| `backend/engines/benchmarking.py` | `backend.engines` | 693 | 4 | 5 | 0 | __future__, core, decimal, domain, infra, organization, the, typing | AI extraction, audit / logging, calculation, emission factors | - | NO CHANGE |
| `backend/engines/calculation.py` | `backend.engines` | 426 | 3 | 0 | 0 | __future__, a, core, datetime, decimal, domain, exc, infra, the, typing | AI extraction, audit / logging, calculation, emission factors, factor matching, workflow | - | NO CHANGE |
| `backend/engines/extraction.py` | `backend.engines` | 306 | 2 | 0 | 0 | __future__, core, datetime, domain, infra, typing | AI extraction, audit / logging, document processing, workflow | - | NO CHANGE |
| `backend/engines/factor_matching.py` | `backend.engines` | 257 | 1 | 1 | 0 | __future__, core, datetime, domain, engines, infra, typing | AI extraction, audit / logging, emission factors, factor matching, workflow | - | NO CHANGE |
| `backend/engines/matching_stages.py` | `backend.engines` | 362 | 7 | 1 | 0 | __future__, core, data, difflib, domain, typing | AI extraction, audit / logging, emission factors, factor matching | - | NO CHANGE |
| `backend/engines/report_generation.py` | `backend.engines` | 831 | 10 | 1 | 0 | CalculationEngine, ValidationEngine, __future__, core, dataclasses, datetime, decimal, domain, exc, infra, typing | AI extraction, audit / logging, calculation, database / repository, emission factors, reporting, validation / QA, workflow | - | NO CHANGE |
| `backend/engines/validation.py` | `backend.engines` | 931 | 4 | 2 | 0 | __future__, collections, core, datetime, decimal, domain, infra, typing | AI extraction, audit / logging, calculation, emission factors, factor matching, validation / QA, workflow | - | NO CHANGE |
| `backend/engines/workflow.py` | `backend.engines` | 851 | 8 | 5 | 0 | __future__, core, dataclasses, datetime, decimal, domain, engines, exc, extraction, infra, status, the, typing | AI extraction, audit / logging, calculation, document processing, emission factors, factor matching, workflow | - | NO CHANGE |
| `backend/glossary copy.py` | `backend` | 5 | 0 | 0 | 0 | pydantic, typing | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/glossary.py` | `backend` | 172 | 1 | 5 | 5 | a, glossary, pydantic, typing | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/infra/__init__.py` | `backend` | 12 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/infra/audit_logger.py` | `backend.infra` | 255 | 2 | 5 | 0 | __future__, core, data, datetime, domain, infra, its, typing | AI extraction, Storage, audit / logging | - | NO CHANGE |
| `backend/infra/config.py` | `backend.infra` | 159 | 2 | 6 | 0 | __future__, core, dataclasses, exc, infra, the, typing | Storage | - | EXTEND / REVIEW |
| `backend/infra/event_bus.py` | `backend.infra` | 166 | 1 | 2 | 0 | __future__, core, domain, typing | AI extraction, audit / logging, workflow | - | NO CHANGE |
| `backend/infra/llm_client.py` | `backend.infra` | 178 | 2 | 0 | 0 | __future__, a, core, dataclasses, exc, typing | AI extraction | - | NO CHANGE |
| `backend/infra/search_index.py` | `backend.infra` | 232 | 2 | 3 | 0 | __future__, a, collections, domain, the, typing | AI extraction, emission factors | - | NO CHANGE |
| `backend/infra/supabase.py` | `backend.infra` | 149 | 0 | 9 | 0 | __future__, dotenv, supabase, the, typing | Storage | - | EXTEND / REVIEW |
| `backend/main copy 2.py` | `backend` | 3966 | 8 | 69 | 39 | CarbonTally, PIL, a, activity_categories, assets, auth, batch, beta_access_codes, beta_users, database, datetime, defra_conversion_factors, documents, dotenv, emissions_logs, environment, facilities, fastapi, fpdf, glossary, manual_review_queue, organization_members, organizations, pdf2image, pdf_engine, pydantic, pypdf, report_generator, reportlab, settings, staff_profiles, start_date, summary, supabase, system, system_settings, the, token, typing, upload_batches, user, validation, waitlist, your | AI extraction, API, Storage, authentication / security, database / repository, reporting | - | NO CHANGE |
| `backend/main copy.py` | `backend` | 3257 | 5 | 52 | 31 | CarbonTally, PIL, a, activity_categories, assets, batch, beta_access_codes, beta_users, database, datetime, defra_conversion_factors, documents, dotenv, emissions_logs, facilities, fastapi, fpdf, glossary, manual, manual_review_queue, organization_members, organizations, pdf2image, pdf_engine, pydantic, pypdf, report_generator, reportlab, staff_profiles, start_date, summary, supabase, the, through, typing, upload_batches, user, waitlist, your | AI extraction, API, Storage, database / repository, reporting | - | NO CHANGE |
| `backend/main.py` | `backend` | 363 | 0 | 6 | 2 | config, database, datetime, dotenv, fastapi, glossary, routes | AI extraction, API, database / repository | - | NO CHANGE |
| `backend/middleware/rate_limit.py` | `backend.middleware` | 54 | 1 | 0 | 0 | fastapi, starlette, typing | API | - | NO DIRECT V3 IMPACT |
| `backend/pdf_engine.py` | `backend` | 340 | 1 | 0 | 0 | PIL, datetime, digital, document, file, image, pdf2image, scanned | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/process_emissions.py` | `backend` | 106 | 0 | 2 | 0 | - | calculation | - | NO CHANGE |
| `backend/report_generator.py` | `backend` | 1072 | 7 | 6 | 1 | Scope, data, dataclasses, datetime, direct, emissions, emissions_logs, fastapi, fpdf, operational, organization_metadata, organizations, pydantic, supabase, the, typing | API, Storage, database / repository, reporting | - | EXTEND / REVIEW |
| `backend/routes/__init__.py` | `backend` | 87 | 0 | 0 | 0 | - | API | - | NO DIRECT V3 IMPACT |
| `backend/routes/admin/__init__.py` | `backend.routes` | 39 | 0 | 0 | 0 | - | API | - | NO DIRECT V3 IMPACT |
| `backend/routes/admin/analytics.py` | `backend.routes.admin` | 278 | 0 | 3 | 3 | auth, database, datetime, fastapi, manual_review_queue, organization_files, organizations, processing_logs, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/admin/assignments.py` | `backend.routes.admin` | 460 | 2 | 4 | 4 | auth, batch, database, datetime, document, fastapi, manual_review_queue, organization_files, pydantic, review, review_assignment_history, staff_profiles, typing, upload_batches, utils | API, authentication / security, database / repository, document processing | - | EXTEND / REVIEW |
| `backend/routes/admin/audit.py` | `backend.routes.admin` | 197 | 1 | 4 | 4 | activity_logs, auth, database, datetime, fastapi, pydantic, typing | API, CSV / Excel, audit / logging, authentication / security, database / repository | - | NO CHANGE |
| `backend/routes/admin/audit_logs.py` | `backend.routes.admin` | 1432 | 9 | 12 | 12 | audit_logs, auth, customer_verifications, database, datetime, fastapi, first, last, message_activity_log, messages, notification_delivery_log, notifications, now, organizations, pydantic, supabase, typing, verification_activity_log | API, Storage, audit / logging, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/admin/beta.py` | `backend.routes.admin` | 500 | 5 | 11 | 10 | auth, beta, beta_access_codes, beta_users, database, datetime, fastapi, pydantic, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/admin/bulk.py` | `backend.routes.admin` | 302 | 2 | 3 | 3 | activity_logs, auth, completed, database, datetime, document, fastapi, organization, organization_files, organizations, pydantic, status, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/admin/dashboard.py` | `backend.routes.admin` | 1579 | 10 | 12 | 12 | ID, a, audit, audit_logs, auth, customer_documents, database, datetime, document_types, emissions_logs, fastapi, get_admin_alerts, manual_review_queue, needed, now, organization_files, organization_members, organizations, pydantic, staff_profiles, supabase, the, typing | API, Storage, authentication / security, database / repository, reporting | - | EXTEND / REVIEW |
| `backend/routes/admin/defra.py` | `backend.routes.admin` | 613 | 6 | 11 | 9 | DEFRA, a, auth, database, datetime, defra_conversion_factors, dict, emissions_logs, factor, fastapi, pydantic, typing | API, authentication / security, database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `backend/routes/admin/document-types.py` | `backend.routes.admin` | 808 | 3 | 14 | 14 | ERP, a, accounting, an, auth, data, database, datetime, document, document_types, extraction, fastapi, in, mappings, metadata, pydantic, suppliers, template, typing, update, utility | API, authentication / security, database / repository, document processing | - | EXTEND / REVIEW |
| `backend/routes/admin/email_templates.py` | `backend.routes.admin` | 670 | 4 | 9 | 8 | Beta, CarbonTally, an, auth, database, datetime, email, email_templates, fastapi, pydantic, the, typing | AI extraction, API, authentication / security, database / repository | - | NO CHANGE |
| `backend/routes/admin/extraction.py` | `backend.routes.admin` | 511 | 4 | 5 | 4 | asset_name, assets, auth, batch, database, datetime, defra_conversion_factors, emissions_logs, extraction, fastapi, main, manual_review_queue, pydantic, request, review, start_date, the, typing, upload_batches | AI extraction, API, authentication / security, database / repository | - | NO CHANGE |
| `backend/routes/admin/logs.py` | `backend.routes.admin` | 350 | 0 | 8 | 8 | auth, database, datetime, email_logs, fastapi, processing_logs, pydantic, typing | API, audit / logging, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/admin/permissions.py` | `backend.routes.admin` | 585 | 5 | 9 | 7 | a, auth, database, datetime, dict, documents, fastapi, pydantic, role, roles, staff_profiles, typing | API, RBAC, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/admin/review_history.py` | `backend.routes.admin` | 212 | 0 | 5 | 5 | auth, database, datetime, fastapi, review_assignment_history, review_audit_trail, typing | API, CSV / Excel, authentication / security, database / repository, validation / QA | - | NO CHANGE |
| `backend/routes/admin/reviews.py` | `backend.routes.admin` | 1300 | 3 | 15 | 12 | auth, database, datetime, document, document_activity_log, escalation, fastapi, manual_review_queue, or, organization_files, priority, pydantic, request, review, review_assignment_history, staff, staff_profiles, staff_workload, typing, upload_batches, utils | API, authentication / security, database / repository, validation / QA | - | EXTEND / REVIEW |
| `backend/routes/admin/settings.py` | `backend.routes.admin` | 167 | 2 | 3 | 3 | auth, database, datetime, fastapi, pydantic, settings, system_settings, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/admin/staff.py` | `backend.routes.admin` | 1879 | 6 | 19 | 16 | a, auth, database, datetime, fastapi, manual_review_queue, pydantic, review_assignment_history, reviews_completed, roles, seconds, staff, staff_profiles, staff_result, staff_workload, supabase, typing, utils | AI extraction, API, CSV / Excel, Storage, authentication / security, database / repository | - | NO CHANGE |
| `backend/routes/admin/workload.py` | `backend.routes.admin` | 896 | 4 | 10 | 10 | auth, collections, customer_documents, database, datetime, fastapi, manual_review_queue, pydantic, queue, queue_settings, review, review_assignment_history, staff_profiles, staff_workload, supabase, typing, utils | API, Storage, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/communication.py` | `backend.routes` | 2326 | 16 | 22 | 22 | a, all, auth, conversation, conversations, database, datetime, fastapi, message, messages, notification, notifications, organization_members, participants, pydantic, staff_profiles, supabase, times, typing | API, Realtime / communication, Storage, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/customer_dashboard.py` | `backend.routes` | 1239 | 9 | 15 | 12 | assets, audit, audit_logs, auth, customer_documents, customer_verifications, database, datetime, emissions_logs, fastapi, manual_review_queue, notifications, organization_members, priority, pydantic, supabase, typing | API, Storage, authentication / security, database / repository, reporting | - | EXTEND / REVIEW |
| `backend/routes/customer_documents.py` | `backend.routes` | 2109 | 13 | 17 | 16 | assets, audit_logs, auth, customer_document, customer_documents, database, datetime, document, document_types, enum, fastapi, manual_review_queue, metadata, organization_members, pydantic, staff_profiles, supabase, typing | API, Storage, authentication / security, database / repository, document processing | - | EXTEND / REVIEW |
| `backend/routes/customer_verifications.py` | `backend.routes` | 1928 | 12 | 13 | 13 | action_details, audit_logs, auth, customer_documents, customer_verifications, database, datetime, document, fastapi, organization_members, organizations, pydantic, supabase, typing, verification, verification_activity_log | API, Storage, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/document_activity.py` | `backend.routes` | 338 | 1 | 6 | 6 | auth, customer_review_log, database, datetime, document, document_activity_log, fastapi, organization_files, organization_members, pydantic, typing | API, CSV / Excel, authentication / security, database / repository, document processing | - | NO CHANGE |
| `backend/routes/documents/__init__.py` | `backend.routes` | 13 | 0 | 0 | 0 | - | API, document processing | - | EXTEND / REVIEW |
| `backend/routes/documents_main.py` | `backend.routes` | 780 | 2 | 5 | 5 | assets, auth, customer_documents, customer_review_log, data, database, datetime, defra_conversion_factors, document, document_activity_log, emissions_logs, fastapi, manual_review_queue, metadata, organization_files, organization_members, pydantic, the, typing | AI extraction, API, authentication / security, database / repository, document processing | - | NO CHANGE |
| `backend/routes/drafts.py` | `backend.routes` | 474 | 3 | 5 | 5 | a, assets, auth, database, datetime, defra_conversion_factors, document, draft_entries, emissions_logs, existing, fastapi, organization_files, pydantic, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/drafts_enhanced.py` | `backend.routes` | 410 | 2 | 6 | 6 | a, auth, database, datetime, draft, draft_entries, fastapi, organization_members, progress, pydantic, section, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/emissions.py` | `backend.routes` | 1509 | 7 | 15 | 15 | Endpoints, an, audit_logs, auth, customer_documents, database, datetime, emission, emissions_logs, fastapi, organization_members, pydantic, record, supabase, this, typing, verification_activity_log | API, CSV / Excel, Storage, authentication / security, calculation, database / repository | - | NO CHANGE |
| `backend/routes/feedback.py` | `backend.routes` | 289 | 2 | 6 | 6 | auth, database, datetime, fastapi, feedback, pydantic, typing, user_feedback | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/glossary.py` | `backend.routes` | 606 | 4 | 9 | 8 | a, auth, database, datetime, dict, fastapi, glossary, pydantic, term, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/logs.py` | `backend.routes` | 388 | 1 | 6 | 6 | activity_logs, auth, database, datetime, fastapi, pydantic, request, typing | API, audit / logging, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/notifications.py` | `backend.routes` | 565 | 4 | 9 | 4 | auth, batch, database, datetime, fastapi, manual_review_queue, organization, organization_members, organizations, pydantic, review, staff_profiles, typing, upload_batches, your | API, Realtime / communication, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/organizations/__init__.py` | `backend.routes` | 31 | 0 | 0 | 0 | - | API | - | NO DIRECT V3 IMPACT |
| `backend/routes/organizations/analytics.py` | `backend.routes.organizations` | 503 | 5 | 9 | 4 | assets, auth, database, date, datetime, emissions_logs, facilities, fastapi, pydantic, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/organizations/assets.py` | `backend.routes.organizations` | 1050 | 9 | 13 | 11 | a, an, asset, assets, auth, database, datetime, emissions_logs, facilities, facility, fastapi, organization_members, pydantic, typing, utils | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/organizations/bulk.py` | `backend.routes.organizations` | 270 | 5 | 2 | 2 | assets, auth, database, datetime, facilities, fastapi, organization_members, organizations, pydantic, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/organizations/dashboard.py` | `backend.routes.organizations` | 272 | 0 | 2 | 2 | auth, database, datetime, emissions_logs, fastapi, organization_members, organizations, path, typing | API, authentication / security, database / repository, reporting | - | EXTEND / REVIEW |
| `backend/routes/organizations/data.py` | `backend.routes.organizations` | 415 | 3 | 5 | 4 | assets, auth, database, datetime, defra_conversion_factors, emissions, emissions_logs, facilities, fastapi, organization_members, organizations, path, pydantic, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/organizations/exports.py` | `backend.routes.organizations` | 260 | 2 | 5 | 4 | auth, data, database, datetime, emissions_logs, export_history, fastapi, first, pydantic, storage, typing, uuid | API, CSV / Excel, authentication / security, database / repository | - | NO CHANGE |
| `backend/routes/organizations/files.py` | `backend.routes.organizations` | 1838 | 10 | 24 | 18 | Supabase, a, asset, assets, audit_logs, auth, comment, customer_documents, database, datetime, fastapi, file, filename, last, metadata, organization_files, organization_members, pydantic, staff_profiles, storage, supabase, the, this, typing, utils | API, Storage, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/organizations/management.py` | `backend.routes.organizations` | 1243 | 11 | 21 | 20 | an, auth, contact, custom, database, datetime, employee, fastapi, financial, industry, organization, organization_members, organization_metadata, organizations, pydantic, supabase, sustainability, typing, utils | API, Storage, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/organizations/members.py` | `backend.routes.organizations` | 971 | 5 | 13 | 10 | a, auth, completed, database, datetime, dict, existing, fastapi, member, members, organization, organization_members, organizations, our, pydantic, supabase, the, token, typing, user_invitations, utils, your, yourself | AI extraction, API, Storage, authentication / security, database / repository | - | NO CHANGE |
| `backend/routes/organizations/metadata.py` | `backend.routes.organizations` | 569 | 6 | 15 | 15 | auth, contact, custom, database, datetime, employee, fastapi, financial, industry, organization_metadata, pydantic, sustainability, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/organizations/team.py` | `backend.routes.organizations` | 285 | 1 | 4 | 4 | a, auth, database, fastapi, member, organization_members, pydantic, role, the, typing | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/reference.py` | `backend.routes` | 201 | 0 | 7 | 7 | activity_categories, auth, database, defra_conversion_factors, fastapi, typing, units | API, authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/routes/reports.py` | `backend.routes` | 2098 | 13 | 25 | 23 | a, audit_logs, auth, customer_documents, database, datetime, defra_conversion_factors, emissions_logs, fastapi, manual_review_queue, metadata, now, organization_members, organizations, pydantic, report, report_generator, report_history, report_schedules, report_templates, staff_profiles, supabase, this, typing | API, Storage, authentication / security, database / repository, reporting | - | EXTEND / REVIEW |
| `backend/routes/upload.py` | `backend.routes` | 1014 | 0 | 14 | 10 | PIL, assets, auth, batch, database, datetime, documents, fastapi, file, main, manual_review_queue, organization_files, organization_members, pdf2image, pdf_engine, pypdf, reportlab, summary, system_settings, the, typing, upload_batches, utils, validation | AI extraction, API, authentication / security, calculation, database / repository, reporting | - | NO CHANGE |
| `backend/routes/users.py` | `backend.routes` | 349 | 5 | 5 | 5 | auth, current, database, datetime, email, fastapi, organizations, password, password_reset_tokens, profile, pydantic, staff, staff_profiles, supabase, typing, user, utils | AI extraction, API, Storage, authentication / security, database / repository | - | NO CHANGE |
| `backend/routes/waitlist.py` | `backend.routes` | 24 | 1 | 2 | 2 | database, datetime, fastapi, pydantic | AI extraction, API, database / repository | - | NO CHANGE |
| `backend/services/email_service.py` | `backend.services` | 346 | 0 | 0 | 0 | datetime, email_logs, supabase, typing | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/tests/__init__.py` | `backend` | 2 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/tests/audit_code.py` | `backend.tests` | 364 | 1 | 1 | 0 | auth, collections, pathlib, tests, the, typing | audit / logging | - | NO DIRECT V3 IMPACT |
| `backend/tests/auth_helper.py` | `backend.tests` | 129 | 2 | 1 | 0 | datetime, typing | authentication / security | - | EXTEND / REVIEW |
| `backend/tests/check_imports.py` | `backend.tests` | 63 | 0 | 1 | 0 | auth, pathlib | CSV / Excel | - | NO CHANGE |
| `backend/tests/config.py` | `backend.tests` | 28 | 1 | 0 | 0 | dotenv | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/tests/create_test_users.py` | `backend.tests` | 197 | 0 | 3 | 0 | auth, database, dotenv, organization_members, organizations, pathlib, staff_profiles | authentication / security, database / repository | - | EXTEND / REVIEW |
| `backend/tests/export_postman.py` | `backend.tests` | 61 | 0 | 1 | 0 | pathlib | CSV / Excel | - | NO CHANGE |
| `backend/tests/fix_imports.py` | `backend.tests` | 57 | 0 | 1 | 0 | auth, pathlib | CSV / Excel | - | NO CHANGE |
| `backend/tests/integration/__init__.py` | `backend.tests` | 6 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/tests/integration/conftest.py` | `backend.tests.integration` | 182 | 0 | 6 | 0 | __future__, data, datetime, domain, public | AI extraction | - | NO CHANGE |
| `backend/tests/integration/test_ai_extraction.py` | `backend.tests.integration` | 106 | 1 | 3 | 0 | __future__, data, domain, engines, http, infra, tests, typing | AI extraction, audit / logging, document processing, workflow | - | NO CHANGE |
| `backend/tests/integration/test_audit.py` | `backend.tests.integration` | 103 | 0 | 6 | 0 | __future__, data, datetime, domain, tests | AI extraction, audit / logging | - | NO CHANGE |
| `backend/tests/integration/test_audit_logger.py` | `backend.tests.integration` | 99 | 0 | 6 | 0 | __future__, data, domain, infra, tests | AI extraction, audit / logging | - | NO CHANGE |
| `backend/tests/integration/test_calculation.py` | `backend.tests.integration` | 278 | 0 | 11 | 0 | __future__, core, data, datetime, decimal, domain, engines, infra, public, tests | AI extraction, audit / logging, calculation, emission factors, workflow | - | NO CHANGE |
| `backend/tests/integration/test_config.py` | `backend.tests.integration` | 47 | 0 | 4 | 0 | __future__, collections, infra | Storage | - | EXTEND / REVIEW |
| `backend/tests/integration/test_documents.py` | `backend.tests.integration` | 93 | 0 | 6 | 0 | __future__, data, dataclasses, tests | document processing | - | EXTEND / REVIEW |
| `backend/tests/integration/test_emission_factors.py` | `backend.tests.integration` | 230 | 0 | 13 | 0 | __future__, data, decimal, domain, tests | AI extraction, CSV / Excel, calculation, emission factors | - | NO CHANGE |
| `backend/tests/integration/test_emissions_logs.py` | `backend.tests.integration` | 149 | 0 | 5 | 0 | __future__, core, data, dataclasses, datetime, decimal, domain, tests | AI extraction, audit / logging, calculation, emission factors | - | NO CHANGE |
| `backend/tests/integration/test_event_bus.py` | `backend.tests.integration` | 104 | 0 | 8 | 0 | __future__, data, datetime, domain, infra, tests, typing | AI extraction, audit / logging, workflow | - | NO CHANGE |
| `backend/tests/integration/test_events.py` | `backend.tests.integration` | 111 | 0 | 5 | 0 | __future__, data, datetime, decimal, domain, tests | AI extraction, audit / logging, workflow | - | NO CHANGE |
| `backend/tests/integration/test_extraction.py` | `backend.tests.integration` | 81 | 0 | 3 | 0 | __future__, core, data, domain, engines, infra, tests | AI extraction, audit / logging, document processing, workflow | - | NO CHANGE |
| `backend/tests/integration/test_factor_aliases.py` | `backend.tests.integration` | 95 | 0 | 6 | 0 | __future__, data, dataclasses, domain, tests | AI extraction, emission factors, factor matching | - | NO CHANGE |
| `backend/tests/integration/test_factor_matching.py` | `backend.tests.integration` | 330 | 1 | 11 | 0 | __future__, data, datetime, decimal, domain, engines, infra, tests, the, typing | AI extraction, audit / logging, calculation, emission factors, factor matching, workflow | - | NO CHANGE |
| `backend/tests/integration/test_imports.py` | `backend.tests.integration` | 129 | 0 | 6 | 0 | __future__, data, dataclasses, domain, tests | AI extraction, CSV / Excel, factor provider | - | NO CHANGE |
| `backend/tests/integration/test_infra.py` | `backend.tests.integration` | 34 | 0 | 3 | 0 | __future__, infra | Storage | - | EXTEND / REVIEW |
| `backend/tests/integration/test_llm_client.py` | `backend.tests.integration` | 111 | 3 | 5 | 0 | __future__, core, http, infra, server, typing | AI extraction | - | NO CHANGE |
| `backend/tests/integration/test_organizations.py` | `backend.tests.integration` | 166 | 0 | 10 | 0 | __future__, data, datetime, domain, public, tests | AI extraction | - | NO CHANGE |
| `backend/tests/integration/test_reports.py` | `backend.tests.integration` | 87 | 0 | 5 | 0 | __future__, data, dataclasses, tests | database / repository, reporting | - | EXTEND / REVIEW |
| `backend/tests/integration/test_search_index.py` | `backend.tests.integration` | 78 | 0 | 3 | 0 | __future__, data, decimal, domain, infra, tests, the | AI extraction, calculation, emission factors | - | NO CHANGE |
| `backend/tests/integration/test_workflow.py` | `backend.tests.integration` | 466 | 1 | 12 | 0 | __future__, core, data, decimal, domain, engines, http, infra, public, tests, typing | AI extraction, audit / logging, calculation, document processing, emission factors, factor matching, workflow | - | NO CHANGE |
| `backend/tests/setup_test_data.py` | `backend.tests` | 599 | 0 | 8 | 0 | Supabase, beta_access_codes, database, datetime, dotenv, organization_members, organizations, pathlib, role, staff_profiles, supabase | Storage, database / repository | - | EXTEND / REVIEW |
| `backend/tests/setup_test_orgs.py` | `backend.tests` | 393 | 0 | 5 | 0 | database, datetime, email, organization_members, organizations, pathlib, staff_profiles, supabase | Storage, database / repository | - | EXTEND / REVIEW |
| `backend/tests/test_all_endpoints.py` | `backend.tests` | 743 | 2 | 1 | 0 | datetime, dotenv, financial, org, organizations, pathlib, profile, supabase, typing | API, Storage | - | EXTEND / REVIEW |
| `backend/tests/test_api.py` | `backend.tests` | 761 | 1 | 1 | 0 | asset, contact, datetime, emission, employee, facility, financial, glossary, industry, organization, pathlib, profile, sustainability, term, tests, typing, user | API, authentication / security | - | EXTEND / REVIEW |
| `backend/tests/test_api_simple.py` | `backend.tests` | 473 | 1 | 1 | 0 | dotenv, pathlib, supabase, typing, user | API, Storage | - | EXTEND / REVIEW |
| `backend/tests/test_auth_simple.py` | `backend.tests` | 56 | 0 | 1 | 0 | dotenv | authentication / security | - | EXTEND / REVIEW |
| `backend/tests/test_failing_endpoints.py` | `backend.tests` | 330 | 2 | 1 | 0 | dotenv, pathlib, supabase, typing | AI extraction, API, Storage | - | NO CHANGE |
| `backend/tests/unit/__init__.py` | `backend.tests` | 2 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/tests/unit/domain/__init__.py` | `backend.tests.unit` | 2 | 0 | 0 | 0 | - | AI extraction | - | NO CHANGE |
| `backend/tests/unit/domain/test_audit.py` | `backend.tests.unit.domain` | 89 | 2 | 1 | 0 | __future__, dataclasses, datetime, domain | AI extraction, audit / logging | - | NO CHANGE |
| `backend/tests/unit/domain/test_benchmarking.py` | `backend.tests.unit.domain` | 164 | 4 | 1 | 0 | __future__, dataclasses, decimal, domain | AI extraction | - | NO CHANGE |
| `backend/tests/unit/domain/test_calculation.py` | `backend.tests.unit.domain` | 115 | 3 | 2 | 0 | __future__, dataclasses, datetime, decimal, domain | AI extraction, calculation, emission factors | - | NO CHANGE |
| `backend/tests/unit/domain/test_document.py` | `backend.tests.unit.domain` | 87 | 2 | 1 | 0 | __future__, dataclasses, datetime, domain | AI extraction, document processing | - | NO CHANGE |
| `backend/tests/unit/domain/test_factor.py` | `backend.tests.unit.domain` | 154 | 2 | 1 | 0 | __future__, core, dataclasses, datetime, decimal, domain | AI extraction, emission factors | - | NO CHANGE |
| `backend/tests/unit/domain/test_matching.py` | `backend.tests.unit.domain` | 169 | 6 | 1 | 0 | __future__, dataclasses, datetime, decimal, domain | AI extraction, emission factors, factor matching | - | NO CHANGE |
| `backend/tests/unit/domain/test_organization.py` | `backend.tests.unit.domain` | 73 | 4 | 1 | 0 | __future__, dataclasses, datetime, domain | AI extraction | - | NO CHANGE |
| `backend/tests/unit/domain/test_provider.py` | `backend.tests.unit.domain` | 199 | 6 | 1 | 0 | __future__, dataclasses, datetime, domain | AI extraction, factor provider | - | NO CHANGE |
| `backend/tests/unit/domain/test_report.py` | `backend.tests.unit.domain` | 101 | 4 | 1 | 0 | __future__, dataclasses, datetime, domain | AI extraction, database / repository, reporting | - | NO CHANGE |
| `backend/tests/unit/domain/test_validation.py` | `backend.tests.unit.domain` | 157 | 4 | 1 | 0 | __future__, dataclasses, domain | AI extraction, validation / QA | - | NO CHANGE |
| `backend/tests/unit/domain/test_workflow.py` | `backend.tests.unit.domain` | 236 | 9 | 2 | 0 | __future__, dataclasses, datetime, decimal, domain, typing | AI extraction, workflow | - | NO CHANGE |
| `backend/tests/unit/engines/__init__.py` | `backend.tests.unit` | 2 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/tests/unit/engines/test_ai_extraction.py` | `backend.tests.unit.engines` | 244 | 5 | 4 | 0 | __future__, core, datetime, domain, engines, infra, typing | AI extraction, audit / logging, document processing, workflow | - | NO CHANGE |
| `backend/tests/unit/engines/test_benchmarking.py` | `backend.tests.unit.engines` | 731 | 17 | 6 | 0 | __future__, core, datetime, decimal, domain, the, typing | AI extraction, audit / logging, calculation, emission factors | - | NO CHANGE |
| `backend/tests/unit/engines/test_calculation.py` | `backend.tests.unit.engines` | 451 | 6 | 3 | 0 | __future__, core, datetime, decimal, domain, engines, infra, typing | AI extraction, audit / logging, calculation, emission factors, factor matching, workflow | - | NO CHANGE |
| `backend/tests/unit/engines/test_extraction.py` | `backend.tests.unit.engines` | 214 | 4 | 2 | 0 | __future__, core, datetime, domain, engines, infra, typing | AI extraction, audit / logging, document processing, workflow | - | NO CHANGE |
| `backend/tests/unit/engines/test_factor_matching.py` | `backend.tests.unit.engines` | 323 | 4 | 4 | 0 | __future__, datetime, decimal, domain, engines, infra, typing | AI extraction, audit / logging, emission factors, factor matching, workflow | - | NO CHANGE |
| `backend/tests/unit/engines/test_matching_stages.py` | `backend.tests.unit.engines` | 349 | 6 | 3 | 0 | __future__, datetime, decimal, domain, engines, infra, typing | AI extraction, emission factors, factor matching | - | NO CHANGE |
| `backend/tests/unit/engines/test_validation.py` | `backend.tests.unit.engines` | 821 | 16 | 12 | 0 | __future__, core, datetime, decimal, domain, infra, typing | AI extraction, audit / logging, calculation, emission factors, factor matching, validation / QA, workflow | - | NO CHANGE |
| `backend/tests/unit/engines/test_workflow.py` | `backend.tests.unit.engines` | 649 | 7 | 24 | 0 | __future__, core, datetime, decimal, domain, engines, infra, typing | AI extraction, audit / logging, calculation, document processing, emission factors, factor matching, workflow | - | NO CHANGE |
| `backend/tests/unit/infra/__init__.py` | `backend.tests.unit` | 2 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/tests/unit/infra/test_audit_logger.py` | `backend.tests.unit.infra` | 276 | 5 | 1 | 0 | __future__, domain, infra | AI extraction, audit / logging | - | NO CHANGE |
| `backend/tests/unit/infra/test_config.py` | `backend.tests.unit.infra` | 157 | 3 | 1 | 0 | __future__, collections, infra | uncategorized | - | NO DIRECT V3 IMPACT |
| `backend/tests/unit/infra/test_event_bus.py` | `backend.tests.unit.infra` | 206 | 3 | 1 | 0 | __future__, datetime, domain, infra, typing | AI extraction, audit / logging, workflow | - | NO CHANGE |
| `backend/tests/unit/infra/test_llm_client.py` | `backend.tests.unit.infra` | 111 | 1 | 0 | 0 | __future__, core, infra, llm | AI extraction | - | NO CHANGE |
| `backend/tests/unit/infra/test_search_index.py` | `backend.tests.unit.infra` | 223 | 5 | 1 | 0 | __future__, decimal, domain, infra, typing | AI extraction, emission factors | - | NO CHANGE |
| `backend/tests/unit/test_core.py` | `backend.tests.unit` | 123 | 3 | 0 | 0 | __future__, core, dataclasses, datetime | audit / logging | - | NO DIRECT V3 IMPACT |
| `backend/tests/verify_setup.py` | `backend.tests` | 113 | 0 | 1 | 0 | auth, beta_access_codes, database, organization_members, organizations, pathlib, staff_profiles | database / repository | - | EXTEND / REVIEW |
| `backend/utils/__init__.py` | `backend` | 113 | 0 | 0 | 0 | - | AI extraction, calculation, document processing | - | NO CHANGE |
| `backend/utils/audit_logger.py` | `backend.utils` | 148 | 0 | 5 | 0 | audit_logs, database, datetime, typing | audit / logging, database / repository | - | EXTEND / REVIEW |
| `backend/utils/document_classifier.py` | `backend.utils` | 145 | 0 | 1 | 0 | database, datetime, document_types, typing | database / repository, document processing | - | EXTEND / REVIEW |
| `backend/utils/email.py` | `backend.utils` | 651 | 0 | 14 | 0 | Beta, database, datetime, email_logs, email_templates, the, typing | AI extraction | - | NO CHANGE |
| `backend/utils/emissions.py` | `backend.utils` | 499 | 0 | 11 | 0 | activity_categories, database, datetime, defra_conversion_factors, the, typing | calculation | - | NO CHANGE |
| `backend/utils/organization_utils.py` | `backend.utils` | 235 | 0 | 7 | 0 | assets, emissions_logs, facilities, organization_files, organization_members, organizations, supabase, typing | Storage | - | EXTEND / REVIEW |
| `backend/utils/staff_workload.py` | `backend.utils` | 171 | 0 | 3 | 0 | database, datetime, manual_review_queue, staff_profiles, staff_workload, table, the, typing | database / repository | - | EXTEND / REVIEW |
| `create_admin_dashboard.py` | `create_admin_dashboard` | 547 | 0 | 5 | 0 | filename, organization_members, pathlib, staff_profiles, with | reporting | - | NO DIRECT V3 IMPACT |
| `demodatagen/config.py` | `demodatagen` | 158 | 1 | 0 | 0 | datetime, pathlib, typing | uncategorized | - | NO DIRECT V3 IMPACT |
| `demodatagen/generators/__init__.py` | `demodatagen` | 1 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `demodatagen/generators/base_generator.py` | `demodatagen.generators` | 260 | 1 | 0 | 0 | abc, config, datetime, pathlib, tqdm, typing, utils | CSV / Excel, audit / logging | - | NO CHANGE |
| `demodatagen/generators/carbon/generate_activity_categories.py` | `demodatagen.generators.carbon` | 1 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `demodatagen/generators/carbon/generate_emissions_logs.py` | `demodatagen.generators.carbon` | 1 | 0 | 0 | 0 | - | audit / logging, calculation | - | NO CHANGE |
| `demodatagen/generators/collaboration/generate_conversations.py` | `demodatagen.generators.collaboration` | 1 | 0 | 0 | 0 | - | Realtime / communication | - | NO DIRECT V3 IMPACT |
| `demodatagen/generators/collaboration/generate_messages.py` | `demodatagen.generators.collaboration` | 1 | 0 | 0 | 0 | - | Realtime / communication | - | NO DIRECT V3 IMPACT |
| `demodatagen/generators/core/generate_organizations.py` | `demodatagen.generators.core` | 632 | 2 | 1 | 0 | a, config, dataclasses, date, datetime, faker, generators, pathlib, typing, utils | factor provider | - | REVIEW — PROVIDER SEMANTICS |
| `demodatagen/generators/core/generate_staff_profiles.py` | `demodatagen.generators.core` | 1 | 0 | 0 | 0 | - | Storage | - | EXTEND / REVIEW |
| `demodatagen/generators/core/generate_users.py` | `demodatagen.generators.core` | 1 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `demodatagen/generators/documents/generate_customer_documents.py` | `demodatagen.generators.documents` | 1 | 0 | 0 | 0 | - | document processing | - | EXTEND / REVIEW |
| `demodatagen/generators/documents/generate_document_types.py` | `demodatagen.generators.documents` | 1 | 0 | 0 | 0 | - | document processing | - | EXTEND / REVIEW |
| `demodatagen/generators/facilities/generate_assets.py` | `demodatagen.generators.facilities` | 1 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `demodatagen/generators/facilities/generate_facilities.py` | `demodatagen.generators.facilities` | 1 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `demodatagen/organizations.py` | `demodatagen` | 1043 | 5 | 1 | 0 | company, dataclasses, datetime, faker, pathlib, the, timestamp, typing | CSV / Excel, factor provider | - | NO CHANGE |
| `demodatagen/scripts/export_to_sql.py` | `demodatagen.scripts` | 243 | 1 | 1 | 0 | config, datetime, filename, pathlib, typing | CSV / Excel | - | NO CHANGE |
| `demodatagen/scripts/run_all_generators.py` | `demodatagen.scripts` | 199 | 1 | 1 | 0 | config, datetime, generators, pathlib, typing | audit / logging | - | NO DIRECT V3 IMPACT |
| `demodatagen/scripts/validate_data.py` | `demodatagen.scripts` | 284 | 1 | 1 | 0 | config, datetime, pathlib, typing, utils | CSV / Excel, validation / QA | - | NO CHANGE |
| `demodatagen/utils/__init__.py` | `demodatagen` | 19 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `demodatagen/utils/data_validators.py` | `demodatagen.utils` | 169 | 1 | 0 | 0 | datetime, typing | validation / QA | - | EXTEND / REVIEW |
| `demodatagen/utils/date_utils.py` | `demodatagen.utils` | 262 | 1 | 0 | 0 | datetime, dateutil, typing | uncategorized | - | NO DIRECT V3 IMPACT |
| `demodatagen/utils/id_generators.py` | `demodatagen.utils` | 117 | 1 | 0 | 0 | typing | uncategorized | - | NO DIRECT V3 IMPACT |
| `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/19fc925d-0962-8a3a-8000-0fb8fbe59ca5/scratch/postprocess.py` | `docs.Final_Kimi.Kimi_Agent_UK_IE_Compliance_Audit_Report.19fc925d-0962-8a3a-8000-0fb8fbe59ca5.scratch` | 236 | 0 | 13 | 0 | docx | audit / logging, database / repository, reporting | - | EXTEND / REVIEW |
| `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/scratch_mm/style.py` | `docs.Final_Kimi.Kimi_Agent_UK_IE_Compliance_Audit_Report.scratch_mm` | 137 | 0 | 3 | 0 | docx | audit / logging, database / repository, reporting | - | EXTEND / REVIEW |
| `export_postman.py` | `export_postman` | 141 | 0 | 3 | 0 | datetime, pathlib, typing | CSV / Excel | - | NO CHANGE |
| `generate_api_docs.py` | `generate_api_docs` | 252 | 0 | 3 | 0 | collections, existing, list_endpoints, pathlib, the, typing | API | - | NO DIRECT V3 IMPACT |
| `generate_backend_inventory.py` | `generate_backend_inventory` | 1367 | 5 | 15 | 0 | __future__, dataclasses, organizations, pathlib, the, typing | uncategorized | - | NO DIRECT V3 IMPACT |
| `generate_messy_fuel_csv.py` | `generate_messy_fuel_csv` | 33 | 0 | 0 | 0 | datetime | CSV / Excel | - | NO CHANGE |
| `generate_messy_utility_csv.py` | `generate_messy_utility_csv` | 28 | 0 | 0 | 0 | - | CSV / Excel | - | NO CHANGE |
| `list_endpoints.py` | `list_endpoints` | 347 | 0 | 7 | 0 | file, module, pathlib, the, typing | API | - | NO DIRECT V3 IMPACT |
| `quick_api_ref.py` | `quick_api_ref` | 195 | 0 | 4 | 0 | pathlib, typing | API | - | NO DIRECT V3 IMPACT |
| `src/__init__.py` | `src` | 2 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `src/commands/__init__.py` | `src` | 2 | 0 | 0 | 0 | - | uncategorized | - | NO DIRECT V3 IMPACT |
| `src/commands/import_defra.py` | `src.commands` | 270 | 1 | 3 | 0 | __future__, dotenv, pathlib, src, the | CSV / Excel, audit / logging, database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/commands/import_seai.py` | `src.commands` | 161 | 0 | 2 | 0 | __future__, pathlib, src, the | AI extraction, CSV / Excel, audit / logging, database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/__init__.py` | `src` | 2 | 0 | 0 | 0 | - | factor provider | - | REVIEW — PROVIDER SEMANTICS |
| `src/providers/defra/__init__.py` | `src.providers` | 73 | 0 | 0 | 0 | - | CSV / Excel, database / repository, factor provider, validation / QA | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/defra/exporter.py` | `src.providers.defra` | 504 | 0 | 14 | 0 | __future__, collections, datetime, decimal, pathlib, supabase, typing | CSV / Excel, Storage, audit / logging, database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/defra/mapper.py` | `src.providers.defra` | 212 | 0 | 8 | 0 | __future__, decimal, the, typing | database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/defra/models.py` | `src.providers.defra` | 382 | 11 | 1 | 0 | __future__, a, dataclasses, datetime, decimal, typing | database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/defra/parser.py` | `src.providers.defra` | 374 | 0 | 15 | 0 | __future__, a, openpyxl, the, typing | database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/defra/validator.py` | `src.providers.defra` | 207 | 0 | 5 | 0 | __future__, the | database / repository, factor provider, validation / QA | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/__init__.py` | `src.providers` | 65 | 0 | 0 | 0 | - | AI extraction, CSV / Excel, database / repository, factor provider, validation / QA | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/exporter.py` | `src.providers.seai` | 370 | 0 | 11 | 0 | __future__, decimal, pathlib, public, typing | AI extraction, CSV / Excel, audit / logging, database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/mapper.py` | `src.providers.seai` | 164 | 0 | 6 | 0 | __future__, decimal, section, the, typing | AI extraction, database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/models.py` | `src.providers.seai` | 378 | 9 | 2 | 0 | __future__, dataclasses, decimal, the, typing | AI extraction, database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/parser.py` | `src.providers.seai` | 225 | 0 | 8 | 0 | __future__, an, pathlib, the, typing | AI extraction, audit / logging, database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/tests/conftest.py` | `src.providers.seai.tests` | 89 | 0 | 7 | 0 | __future__, pathlib, public, src | AI extraction, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/tests/test_defra_regression.py` | `src.providers.seai.tests` | 217 | 1 | 7 | 0 | __future__, datetime, decimal, domain, engines, infra, pathlib, public, src, the, typing | AI extraction, calculation, emission factors, factor matching, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/tests/test_import.py` | `src.providers.seai.tests` | 152 | 0 | 6 | 0 | __future__, decimal, public, src | AI extraction, CSV / Excel, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/tests/test_mapper.py` | `src.providers.seai.tests` | 158 | 0 | 13 | 0 | __future__, decimal, src, the | AI extraction, database / repository, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/tests/test_parser.py` | `src.providers.seai.tests` | 102 | 0 | 8 | 0 | __future__, src | AI extraction, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/tests/test_validator.py` | `src.providers.seai.tests` | 140 | 0 | 15 | 0 | __future__, decimal, src | AI extraction, database / repository, factor provider, validation / QA | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `src/providers/seai/validator.py` | `src.providers.seai` | 129 | 0 | 2 | 0 | __future__, collections | AI extraction, database / repository, factor provider, validation / QA | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `test_endpoints.py` | `test_endpoints` | 130 | 0 | 4 | 0 | pathlib, typing | AI extraction, API | - | NO CHANGE |
| `tools/carbon_data_factory/analyze_project.py` | `tools.carbon_data_factory` | 33 | 0 | 1 | 0 | - | emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/__init__.py` | `tools.carbon_data_factory` | 4 | 0 | 0 | 0 | - | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/base_importer.py` | `tools.carbon_data_factory.importers` | 13 | 1 | 0 | 0 | abc | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/orchestrator.py` | `tools.carbon_data_factory.importers` | 14 | 1 | 0 | 0 | - | CSV / Excel, emission factors, workflow | - | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/__init__.py` | `tools.carbon_data_factory.importers` | 4 | 0 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | - | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/defra/__init__.py` | `tools.carbon_data_factory.importers.providers` | 4 | 0 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/defra/importer.py` | `tools.carbon_data_factory.importers.providers.defra` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/defra/normalizer.py` | `tools.carbon_data_factory.importers.providers.defra` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/defra/parser.py` | `tools.carbon_data_factory.importers.providers.defra` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/defra/pivoter.py` | `tools.carbon_data_factory.importers.providers.defra` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/defra/schema.py` | `tools.carbon_data_factory.importers.providers.defra` | 8 | 0 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/defra/transformer.py` | `tools.carbon_data_factory.importers.providers.defra` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/defra/validator.py` | `tools.carbon_data_factory.importers.providers.defra` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, factor provider, validation / QA | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/epa/__init__.py` | `tools.carbon_data_factory.importers.providers` | 4 | 0 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/epa/importer.py` | `tools.carbon_data_factory.importers.providers.epa` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/epa/normalizer.py` | `tools.carbon_data_factory.importers.providers.epa` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/epa/parser.py` | `tools.carbon_data_factory.importers.providers.epa` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/epa/schema.py` | `tools.carbon_data_factory.importers.providers.epa` | 8 | 0 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/epa/transformer.py` | `tools.carbon_data_factory.importers.providers.epa` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/epa/validator.py` | `tools.carbon_data_factory.importers.providers.epa` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, factor provider, validation / QA | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/seai/__init__.py` | `tools.carbon_data_factory.importers.providers` | 4 | 0 | 0 | 0 | - | AI extraction, CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/seai/importer.py` | `tools.carbon_data_factory.importers.providers.seai` | 12 | 1 | 0 | 0 | - | AI extraction, CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/seai/normalizer.py` | `tools.carbon_data_factory.importers.providers.seai` | 12 | 1 | 0 | 0 | - | AI extraction, CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/seai/parser.py` | `tools.carbon_data_factory.importers.providers.seai` | 12 | 1 | 0 | 0 | - | AI extraction, CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/seai/schema.py` | `tools.carbon_data_factory.importers.providers.seai` | 8 | 0 | 0 | 0 | - | AI extraction, CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/seai/transformer.py` | `tools.carbon_data_factory.importers.providers.seai` | 12 | 1 | 0 | 0 | - | AI extraction, CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/providers/seai/validator.py` | `tools.carbon_data_factory.importers.providers.seai` | 12 | 1 | 0 | 0 | - | AI extraction, CSV / Excel, emission factors, factor provider, validation / QA | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/shared/__init__.py` | `tools.carbon_data_factory.importers` | 4 | 0 | 0 | 0 | - | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/shared/change_detector.py` | `tools.carbon_data_factory.importers.shared` | 12 | 0 | 1 | 0 | - | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/shared/db.py` | `tools.carbon_data_factory.importers.shared` | 6 | 0 | 1 | 0 | - | CSV / Excel, database / repository, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/shared/hierarchy.py` | `tools.carbon_data_factory.importers.shared` | 6 | 0 | 1 | 0 | flat | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/shared/storage.py` | `tools.carbon_data_factory.importers.shared` | 11 | 0 | 2 | 0 | - | CSV / Excel, Storage, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/shared/units.py` | `tools.carbon_data_factory.importers.shared` | 12 | 0 | 1 | 0 | - | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/shared/validators.py` | `tools.carbon_data_factory.importers.shared` | 6 | 0 | 1 | 0 | - | CSV / Excel, emission factors, validation / QA | - | NO CHANGE |
| `tools/carbon_data_factory/importers/stages/__init__.py` | `tools.carbon_data_factory.importers` | 4 | 0 | 0 | 0 | - | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/stages/base_stage.py` | `tools.carbon_data_factory.importers.stages` | 13 | 1 | 0 | 0 | abc | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/stages/importer.py` | `tools.carbon_data_factory.importers.stages` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/stages/normalizer.py` | `tools.carbon_data_factory.importers.stages` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/stages/parser.py` | `tools.carbon_data_factory.importers.stages` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/stages/pivoter.py` | `tools.carbon_data_factory.importers.stages` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/stages/transformer.py` | `tools.carbon_data_factory.importers.stages` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/stages/validator.py` | `tools.carbon_data_factory.importers.stages` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors, validation / QA | - | NO CHANGE |
| `tools/carbon_data_factory/importers/stages/verifier.py` | `tools.carbon_data_factory.importers.stages` | 12 | 1 | 0 | 0 | - | CSV / Excel, emission factors | - | NO CHANGE |
| `tools/carbon_data_factory/importers/tests/integration/test_defra_import.py` | `tools.carbon_data_factory.importers.tests.integration` | 9 | 0 | 1 | 0 | importers | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/tests/unit/test_defra_parser.py` | `tools.carbon_data_factory.importers.tests.unit` | 9 | 0 | 1 | 0 | importers | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |
| `tools/carbon_data_factory/importers/tests/unit/test_defra_pivoter.py` | `tools.carbon_data_factory.importers.tests.unit` | 9 | 0 | 1 | 0 | importers | CSV / Excel, emission factors, factor provider | EMISSION-FACTOR PROVIDER | NO CHANGE |

## 4. Detailed Module Inventory

### 4.1 `admin/serve.py`

- **Module:** `admin.serve`
- **Package:** `admin`
- **Lines:** 68
- **Size:** 2,363 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `CustomHandler` (line 10; bases: `http.server.SimpleHTTPRequestHandler`)
  - `__init__()` (line 11)
  - `do_GET()` (line 14)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `build`
- `the`

#### Imports

- `http.server`
- `os`
- `socketserver`
- `urllib.parse`

### 4.2 `backend/auth.py`

- **Module:** `backend.auth`
- **Package:** `backend`
- **Lines:** 549
- **Size:** 19,245 bytes
- **Categories:** API, Storage, authentication / security
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `AuthUser` (line 54; bases: `BaseModel`)

#### Top-Level Functions

- `get_supabase_client()` (line 75)
- `get_role_permissions_from_db()` (line 103)
- `async get_current_user()` (line 126)
- `require_auth()` (line 291)
- `async auth_checker()` (line 297)
- `require_admin()` (line 310)
- `async admin_checker()` (line 315)
- `require_staff()` (line 335)
- `async staff_checker()` (line 340)
- `require_org_member()` (line 360)
- `async org_member_checker()` (line 365)
- `require_org_admin()` (line 385)
- `async org_admin_checker()` (line 390)
- `require_org_access()` (line 428)
- `async org_access_checker()` (line 433)
- `require_role()` (line 456)
- `async role_checker()` (line 460)
- `require_permission()` (line 472)
- `async permission_checker()` (line 476)
- `require_any_permission()` (line 488)
- `async permission_checker()` (line 490)
- `require_all_permissions()` (line 506)
- `async permission_checker()` (line 508)
- `get_role_permissions()` (line 528)
- `async get_current_user_optional()` (line 535)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `auth`
- `database`
- `datetime`
- `dotenv`
- `fastapi`
- `organization_members`
- `pydantic`
- `roles`
- `staff_profiles`
- `supabase`
- `typing`

#### Imports

- `datetime`
- `dotenv`
- `fastapi`
- `fastapi.security`
- `jwt`
- `os`
- `pydantic`
- `supabase`
- `traceback`
- `typing`

### 4.3 `backend/config.py`

- **Module:** `backend.config`
- **Package:** `backend`
- **Lines:** 50
- **Size:** 1,678 bytes
- **Categories:** Storage
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `Config` (line 8; bases: `-`)
  - `get_supabase_client()` (line 45)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `dotenv`
- `supabase`

#### Imports

- `dotenv`
- `os`
- `supabase`

### 4.4 `backend/core/__init__.py`

- **Module:** `backend.core`
- **Package:** `backend`
- **Lines:** 49
- **Size:** 1,412 bytes
- **Categories:** audit / logging
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `any`

#### Imports

- `.exceptions`
- `.logging`
- `.types`

### 4.5 `backend/core/exceptions.py`

- **Module:** `backend.core.exceptions`
- **Package:** `backend.core`
- **Lines:** 116
- **Size:** 3,681 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `CarbonTallyError` (line 13; bases: `Exception`)
  - `__init__()` (line 28)
- `FactorNotFoundError` (line 34; bases: `CarbonTallyError`)
- `FactorAmbiguousError` (line 41; bases: `CarbonTallyError`)
- `ExtractionFailedError` (line 48; bases: `CarbonTallyError`)
- `AIExtractionFailedError` (line 55; bases: `CarbonTallyError`)
- `ImportValidationError` (line 62; bases: `CarbonTallyError`)
- `ReportGenerationFailedError` (line 69; bases: `CarbonTallyError`)
- `WorkflowInvalidTransitionError` (line 76; bases: `CarbonTallyError`)
- `WorkflowMaxRetriesError` (line 83; bases: `CarbonTallyError`)
- `ValidationFailedError` (line 90; bases: `CarbonTallyError`)
- `BenchmarkDataInsufficientError` (line 97; bases: `CarbonTallyError`)
- `UnitMismatchError` (line 104; bases: `CarbonTallyError`)
- `UnknownProviderError` (line 111; bases: `CarbonTallyError`)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `typing`

#### Imports

- `__future__`
- `typing`

### 4.6 `backend/core/logging.py`

- **Module:** `backend.core.logging`
- **Package:** `backend.core`
- **Lines:** 45
- **Size:** 1,507 bytes
- **Categories:** audit / logging
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- `configure_logging()` (line 17)
- `get_logger()` (line 35)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`

#### Imports

- `__future__`
- `logging`
- `sys`

### 4.7 `backend/core/types.py`

- **Module:** `backend.core.types`
- **Package:** `backend.core`
- **Lines:** 66
- **Size:** 2,174 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `Country` (line 24; bases: `StrEnum`)
- `Scope` (line 31; bases: `StrEnum`)
- `DateRange` (line 41; bases: `-`)
  - `__post_init__()` (line 52)
  - `contains()` (line 59)
  - `overlaps()` (line 63)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `enum`
- `typing`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `enum`
- `typing`

### 4.8 `backend/data/__init__.py`

- **Module:** `backend.data`
- **Package:** `backend`
- **Lines:** 31
- **Size:** 1,019 bytes
- **Categories:** CSV / Excel, audit / logging, calculation, database / repository, document processing, emission factors, reporting
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.audit`
- `.base`
- `.documents`
- `.emission_factors`
- `.emissions_logs`
- `.events`
- `.factor_aliases`
- `.imports`
- `.organizations`
- `.reports`

### 4.9 `backend/data/audit.py`

- **Module:** `backend.data.audit`
- **Package:** `backend.data`
- **Lines:** 262
- **Size:** 10,131 bytes
- **Categories:** AI extraction, CSV / Excel, audit / logging
- **V3 impact:** **NO CHANGE**

#### Classes

- `AuditRepository` (line 80; bases: `AbstractRepository[AuditEntry]`)
  - `async record()` (line 83)
  - `async query()` (line 110)
  - `async export_csv()` (line 148)
  - `async get_by_correlation()` (line 173)
  - `async get()` (line 185)
  - `async save()` (line 193)
  - `async delete()` (line 257)

#### Top-Level Functions

- `_actor_uuid()` (line 41)
- `_entry_metadata()` (line 50)
- `_row_to_entry()` (line 60)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `domain`
- `public`
- `typing`

#### Imports

- `__future__`
- `csv`
- `data.base`
- `domain.audit`
- `io`
- `typing`
- `uuid`

### 4.10 `backend/data/base.py`

- **Module:** `backend.data.base`
- **Package:** `backend.data`
- **Lines:** 169
- **Size:** 5,801 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `AbstractRepository` (line 24; bases: `ABC, Generic[T]`)
  - `__init__()` (line 31)
  - `async get()` (line 37)
  - `async save()` (line 41)
  - `async delete()` (line 45)
  - `async _fetch_one()` (line 48)
  - `async _fetch_all()` (line 55)
  - `async _execute()` (line 60)

#### Top-Level Functions

- `to_jsonable()` (line 71)
- `dumps_jsonb()` (line 92)
- `loads_jsonb()` (line 97)
- `coerce_json()` (line 106)
- `_coerce_scalar()` (line 140)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `JSONB`
- `__future__`
- `abc`
- `decimal`
- `typing`

#### Imports

- `__future__`
- `abc`
- `asyncpg`
- `datetime`
- `decimal`
- `json`
- `typing`
- `uuid`

### 4.11 `backend/data/documents.py`

- **Module:** `backend.data.documents`
- **Package:** `backend.data`
- **Lines:** 150
- **Size:** 5,492 bytes
- **Categories:** AI extraction, document processing
- **V3 impact:** **NO CHANGE**

#### Classes

- `DocumentsRepository` (line 43; bases: `AbstractRepository[Document]`)
  - `async create_from_upload()` (line 46)
  - `async update_status()` (line 68)
  - `async get_pending_extraction()` (line 84)
  - `async get_by_org()` (line 95)
  - `async get()` (line 107)
  - `async save()` (line 115)
  - `async delete()` (line 145)

#### Top-Level Functions

- `_row_to_document()` (line 25)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `an`
- `data`
- `datetime`
- `domain`
- `public`
- `the`
- `typing`

#### Imports

- `__future__`
- `data.base`
- `datetime`
- `domain.document`
- `typing`

### 4.12 `backend/data/emission_factors.py`

- **Module:** `backend.data.emission_factors`
- **Package:** `backend.data`
- **Lines:** 306
- **Size:** 11,679 bytes
- **Categories:** AI extraction, calculation, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `EmissionFactorsRepository` (line 74; bases: `AbstractRepository[EmissionFactor]`)
  - `async get()` (line 77)
  - `async find_by_natural_key()` (line 84)
  - `async find_by_activity()` (line 114)
  - `async bulk_upsert()` (line 149)
  - `async get_active_set()` (line 198)
  - `async deactivate_by_batch()` (line 213)
  - `async load_all_for_index()` (line 226)
  - `async count_by_provider()` (line 234)
  - `async save()` (line 248)
  - `async delete()` (line 292)

#### Top-Level Functions

- `_natural_key()` (line 31)
- `_row_to_factor()` (line 48)
- `_rowcount()` (line 299)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `decimal`
- `domain`
- `its`
- `public`
- `so`
- `typing`

#### Imports

- `__future__`
- `data.base`
- `decimal`
- `domain.factor`
- `typing`

### 4.13 `backend/data/emissions_logs.py`

- **Module:** `backend.data.emissions_logs`
- **Package:** `backend.data`
- **Lines:** 313
- **Size:** 11,381 bytes
- **Categories:** AI extraction, audit / logging, calculation
- **V3 impact:** **NO CHANGE**

#### Classes

- `EmissionsLogsRepository` (line 75; bases: `AbstractRepository[EmissionLog]`)
  - `async create()` (line 78)
  - `async find_by_org()` (line 119)
  - `async aggregate()` (line 135)
  - `async count_by_scope()` (line 189)
  - `async get()` (line 205)
  - `async save()` (line 213)
  - `async save_snapshot()` (line 249)
  - `async delete()` (line 307)

#### Top-Level Functions

- `_row_to_log()` (line 42)
- `_log_metadata()` (line 62)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `an`
- `core`
- `data`
- `datetime`
- `decimal`
- `domain`
- `public`
- `start_date`
- `typing`

#### Imports

- `__future__`
- `core.types`
- `data.base`
- `datetime`
- `decimal`
- `domain.calculation`
- `typing`

### 4.14 `backend/data/events.py`

- **Module:** `backend.data.events`
- **Package:** `backend.data`
- **Lines:** 156
- **Size:** 5,721 bytes
- **Categories:** AI extraction, audit / logging, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `EventsRepository` (line 90; bases: `AbstractRepository[DomainEvent]`)
  - `async store()` (line 93)
  - `async get_by_correlation()` (line 114)
  - `async replay()` (line 126)
  - `async get()` (line 138)
  - `async save()` (line 146)
  - `async delete()` (line 150)

#### Top-Level Functions

- `_event_registry()` (line 27)
- `_resolve_event_class()` (line 41)
- `_event_to_payload()` (line 60)
- `_event_from_row()` (line 70)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `domain`
- `public`
- `the`
- `typing`

#### Imports

- `__future__`
- `data.base`
- `dataclasses`
- `domain`
- `domain.workflow`
- `typing`

### 4.15 `backend/data/factor_aliases.py`

- **Module:** `backend.data.factor_aliases`
- **Package:** `backend.data`
- **Lines:** 143
- **Size:** 5,308 bytes
- **Categories:** AI extraction, emission factors, factor matching
- **V3 impact:** **NO CHANGE**

#### Classes

- `FactorAliasesRepository` (line 32; bases: `AbstractRepository[FactorAlias]`)
  - `async find_by_alias()` (line 35)
  - `async get_global_aliases()` (line 61)
  - `async get_org_aliases()` (line 72)
  - `async get()` (line 84)
  - `async save()` (line 92)
  - `async delete()` (line 138)

#### Top-Level Functions

- `_row_to_alias()` (line 19)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `domain`
- `public`
- `typing`
- `when`

#### Imports

- `__future__`
- `data.base`
- `domain.matching`
- `typing`

### 4.16 `backend/data/imports.py`

- **Module:** `backend.data.imports`
- **Package:** `backend.data`
- **Lines:** 317
- **Size:** 11,076 bytes
- **Categories:** AI extraction, CSV / Excel, factor provider
- **V3 impact:** **NO CHANGE**

#### Classes

- `ImportsRepository` (line 74; bases: `AbstractRepository[ImportBatch]`)
  - `async create_batch()` (line 77)
  - `async complete_batch()` (line 109)
  - `async fail_batch()` (line 143)
  - `async activate_batch()` (line 165)
  - `async deactivate_batch()` (line 202)
  - `async rollback_batch()` (line 217)
  - `async get_active()` (line 237)
  - `async get_history()` (line 250)
  - `async get()` (line 262)
  - `async save()` (line 270)
  - `async delete()` (line 311)

#### Top-Level Functions

- `_errors_to_jsonb()` (line 23)
- `_errors_from_jsonb()` (line 36)
- `_row_to_batch()` (line 53)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `a`
- `data`
- `domain`
- `public`
- `the`
- `typing`

#### Imports

- `__future__`
- `data.base`
- `domain.provider`
- `typing`

### 4.17 `backend/data/organizations.py`

- **Module:** `backend.data.organizations`
- **Package:** `backend.data`
- **Lines:** 227
- **Size:** 7,659 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- `OrganizationsRepository` (line 103; bases: `AbstractRepository[Organization]`)
  - `async get_by_id()` (line 106)
  - `async get_members()` (line 110)
  - `async get_metadata()` (line 122)
  - `async get_facilities()` (line 134)
  - `async get_assets()` (line 146)
  - `async get()` (line 158)
  - `async save()` (line 166)
  - `async delete()` (line 189)
  - `async update_metadata()` (line 195)

#### Top-Level Functions

- `_row_to_org()` (line 36)
- `_row_to_member()` (line 47)
- `_row_to_metadata()` (line 59)
- `_row_to_facility()` (line 70)
- `_row_to_asset()` (line 85)
- `_as_float()` (line 96)
- `_as_int()` (line 100)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `domain`
- `public`
- `typing`

#### Imports

- `__future__`
- `data.base`
- `domain.organization`
- `typing`

### 4.18 `backend/data/reports.py`

- **Module:** `backend.data.reports`
- **Package:** `backend.data`
- **Lines:** 181
- **Size:** 6,710 bytes
- **Categories:** AI extraction, database / repository, reporting
- **V3 impact:** **NO CHANGE**

#### Classes

- `ReportsRepository` (line 47; bases: `AbstractRepository[GeneratedReport]`)
  - `async create_generation_request()` (line 50)
  - `async complete_generation()` (line 75)
  - `async get_by_org()` (line 114)
  - `async get()` (line 126)
  - `async save()` (line 137)
  - `async delete()` (line 175)

#### Top-Level Functions

- `_row_to_report()` (line 23)
- `_page_count_jsonb()` (line 42)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `datetime`
- `domain`
- `public`
- `typing`

#### Imports

- `__future__`
- `data.base`
- `datetime`
- `domain.report`
- `typing`

### 4.19 `backend/database.py`

- **Module:** `backend.database`
- **Package:** `backend`
- **Lines:** 162
- **Size:** 5,238 bytes
- **Categories:** Storage, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `get_supabase_client()` (line 28)
- `reset_supabase_client()` (line 72)
- `is_supabase_connected()` (line 81)
- `get_supabase_health()` (line 95)
- `get_supabase_admin()` (line 130)
- `close_supabase_client()` (line 140)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `datetime`
- `dotenv`
- `glossary`
- `organizations`
- `supabase`

#### Imports

- `atexit`
- `datetime`
- `dotenv`
- `os`
- `supabase`
- `traceback`

### 4.20 `backend/domain/__init__.py`

- **Module:** `backend.domain`
- **Package:** `backend`
- **Lines:** 151
- **Size:** 3,506 bytes
- **Categories:** AI extraction, audit / logging, calculation, database / repository, document processing, emission factors, factor matching, factor provider, reporting, validation / QA, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.audit`
- `.benchmarking`
- `.calculation`
- `.document`
- `.factor`
- `.matching`
- `.organization`
- `.provider`
- `.report`
- `.validation`
- `.workflow`

### 4.21 `backend/domain/audit.py`

- **Module:** `backend.domain.audit`
- **Package:** `backend.domain`
- **Lines:** 104
- **Size:** 3,596 bytes
- **Categories:** AI extraction, audit / logging
- **V3 impact:** **NO CHANGE**

#### Classes

- `AuditEntry` (line 14; bases: `-`)
- `AuditTrail` (line 48; bases: `-`)
  - `__post_init__()` (line 54)
  - `by_action()` (line 62)
  - `by_entity()` (line 66)
- `AuditQuery` (line 76; bases: `-`)
  - `__post_init__()` (line 93)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `typing`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `typing`

### 4.22 `backend/domain/benchmarking.py`

- **Module:** `backend.domain.benchmarking`
- **Package:** `backend.domain`
- **Lines:** 196
- **Size:** 7,662 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- `BenchmarkAvailability` (line 50; bases: `StrEnum`)
- `BenchmarkMetric` (line 69; bases: `-`)
  - `__post_init__()` (line 109)
  - `is_available()` (line 116)
- `BenchmarkRequest` (line 122; bases: `-`)
  - `__post_init__()` (line 144)
- `BenchmarkResult` (line 172; bases: `-`)
  - `metric()` (line 192)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `decimal`
- `enum`
- `reporting_year`
- `the`
- `typing`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `decimal`
- `enum`
- `typing`

### 4.23 `backend/domain/calculation.py`

- **Module:** `backend.domain.calculation`
- **Package:** `backend.domain`
- **Lines:** 160
- **Size:** 4,969 bytes
- **Categories:** AI extraction, calculation, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `CalculationMethodology` (line 19; bases: `StrEnum`)
- `CalculationSnapshot` (line 30; bases: `-`)
  - `_canonical()` (line 55)
  - `build_content_hash()` (line 71)
  - `verify_reproducibility()` (line 75)
- `CalculationResult` (line 85; bases: `-`)
- `VerificationResult` (line 96; bases: `-`)
- `EmissionLog` (line 105; bases: `-`)
  - `__post_init__()` (line 127)
- `EmissionsAggregate` (line 137; bases: `-`)
  - `__post_init__()` (line 153)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `dataclasses`
- `decimal`
- `domain`
- `enum`
- `inputs`
- `the`
- `typing`

#### Imports

- `__future__`
- `core.types`
- `dataclasses`
- `datetime`
- `decimal`
- `domain.factor`
- `enum`
- `hashlib`
- `typing`

### 4.24 `backend/domain/document.py`

- **Module:** `backend.domain.document`
- **Package:** `backend.domain`
- **Lines:** 81
- **Size:** 2,203 bytes
- **Categories:** AI extraction, document processing
- **V3 impact:** **NO CHANGE**

#### Classes

- `Document` (line 14; bases: `-`)
- `ExtractedPage` (line 28; bases: `-`)
- `ExtractedTable` (line 37; bases: `-`)
- `ExtractionField` (line 46; bases: `-`)
- `ExtractionResult` (line 56; bases: `-`)
  - `__post_init__()` (line 73)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `a`
- `dataclasses`
- `datetime`
- `typing`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `typing`

### 4.25 `backend/domain/factor.py`

- **Module:** `backend.domain.factor`
- **Package:** `backend.domain`
- **Lines:** 156
- **Size:** 5,789 bytes
- **Categories:** AI extraction, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `EmissionFactor` (line 36; bases: `-`)
  - `__post_init__()` (line 70)
  - `calculate_emissions()` (line 82)
  - `with_new_year()` (line 106)
- `FactorSetMetadata` (line 119; bases: `-`)
- `FactorSet` (line 129; bases: `-`)
  - `find_by_natural_key()` (line 138)
  - `search_by_activity()` (line 142)

#### Top-Level Functions

- `gas_coverage()` (line 19)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `dataclasses`
- `datetime`
- `decimal`
- `the`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `dataclasses`
- `datetime`
- `decimal`
- `typing`

### 4.26 `backend/domain/matching.py`

- **Module:** `backend.domain.matching`
- **Package:** `backend.domain`
- **Lines:** 197
- **Size:** 6,250 bytes
- **Categories:** AI extraction, emission factors, factor matching
- **V3 impact:** **NO CHANGE**

#### Classes

- `FactorSearch` (line 17; bases: `Protocol`)
  - `exact_natural_key()` (line 23)
  - `keyword_search()` (line 25)
- `MatchingStage` (line 35; bases: `ABC`)
  - `name()` (line 44)
  - `async execute()` (line 48)
- `MatchRequest` (line 53; bases: `-`)
  - `__post_init__()` (line 66)
- `StageResult` (line 80; bases: `-`)
  - `__post_init__()` (line 92)
- `Suggestion` (line 104; bases: `-`)
- `MatchResult` (line 114; bases: `-`)
  - `__post_init__()` (line 127)
  - `no_match()` (line 138)
- `FactorAlias` (line 153; bases: `-`)
- `MatchingPipelineConfig` (line 169; bases: `-`)
  - `__post_init__()` (line 187)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `abc`
- `dataclasses`
- `datetime`
- `domain`
- `typing`

#### Imports

- `__future__`
- `abc`
- `dataclasses`
- `datetime`
- `domain.factor`
- `typing`

### 4.27 `backend/domain/organization.py`

- **Module:** `backend.domain.organization`
- **Package:** `backend.domain`
- **Lines:** 74
- **Size:** 1,774 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- `Organization` (line 14; bases: `-`)
- `OrganizationMember` (line 25; bases: `-`)
- `Facility` (line 40; bases: `-`)
- `Asset` (line 51; bases: `-`)
- `OrganizationMetadata` (line 62; bases: `-`)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `typing`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `typing`

### 4.28 `backend/domain/provider.py`

- **Module:** `backend.domain.provider`
- **Package:** `backend.domain`
- **Lines:** 182
- **Size:** 5,089 bytes
- **Categories:** AI extraction, factor provider
- **V3 impact:** **NO CHANGE**

#### Classes

- `ProviderInfo` (line 15; bases: `-`)
- `ProviderVersion` (line 31; bases: `-`)
- `ImportError` (line 44; bases: `-`)
  - `__post_init__()` (line 52)
- `ImportBatch` (line 60; bases: `-`)
  - `__post_init__()` (line 84)
  - `activate()` (line 99)
  - `rollback()` (line 107)
- `DiscoveredSheet` (line 118; bases: `-`)
- `DiscoveryResult` (line 130; bases: `-`)
  - `__post_init__()` (line 140)
- `RawFactorRow` (line 146; bases: `-`)
- `NormalisedFactor` (line 155; bases: `-`)
  - `__post_init__()` (line 167)
- `ImportResult` (line 173; bases: `-`)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `a`
- `dataclasses`
- `datetime`
- `typing`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `typing`

### 4.29 `backend/domain/report.py`

- **Module:** `backend.domain.report`
- **Package:** `backend.domain`
- **Lines:** 69
- **Size:** 1,798 bytes
- **Categories:** AI extraction, database / repository, reporting
- **V3 impact:** **NO CHANGE**

#### Classes

- `ReportSection` (line 14; bases: `-`)
- `ReportTemplate` (line 24; bases: `-`)
- `ReportRequest` (line 34; bases: `-`)
  - `__post_init__()` (line 44)
- `GeneratedReport` (line 52; bases: `-`)
  - `__post_init__()` (line 64)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `typing`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `typing`

### 4.30 `backend/domain/validation.py`

- **Module:** `backend.domain.validation`
- **Package:** `backend.domain`
- **Lines:** 150
- **Size:** 5,359 bytes
- **Categories:** AI extraction, validation / QA
- **V3 impact:** **NO CHANGE**

#### Classes

- `ValidationSeverity` (line 22; bases: `StrEnum`)
- `ValidationIssue` (line 35; bases: `-`)
  - `__post_init__()` (line 60)
  - `is_blocking()` (line 71)
- `ValidationReport` (line 77; bases: `-`)
  - `ok()` (line 86)
  - `counts()` (line 91)
  - `blocking_errors()` (line 99)
  - `errors()` (line 103)
  - `warnings()` (line 109)
  - `merge()` (line 115)
- `ValidationRequest` (line 121; bases: `-`)
  - `__post_init__()` (line 143)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `dataclasses`
- `enum`
- `typing`

#### Imports

- `__future__`
- `core.types`
- `dataclasses`
- `enum`
- `typing`

### 4.31 `backend/domain/workflow.py`

- **Module:** `backend.domain.workflow`
- **Package:** `backend.domain`
- **Lines:** 335
- **Size:** 10,438 bytes
- **Categories:** AI extraction, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `WorkflowDefinition` (line 22; bases: `-`)
  - `can_transition()` (line 33)
  - `validate_state()` (line 37)
- `Transition` (line 77; bases: `-`)
- `DomainEvent` (line 93; bases: `ABC`)
- `DocumentUploaded` (line 113; bases: `DomainEvent`)
  - `__post_init__()` (line 120)
- `ExtractionRequested` (line 126; bases: `DomainEvent`)
  - `__post_init__()` (line 131)
- `ExtractionCompleted` (line 137; bases: `DomainEvent`)
  - `__post_init__()` (line 144)
- `FieldsExtracted` (line 154; bases: `DomainEvent`)
  - `__post_init__()` (line 161)
- `CalculationRequested` (line 169; bases: `DomainEvent`)
  - `__post_init__()` (line 175)
- `CalculationCompleted` (line 181; bases: `DomainEvent`)
  - `__post_init__()` (line 187)
- `ReportGenerated` (line 195; bases: `DomainEvent`)
  - `__post_init__()` (line 202)
- `ImportStarted` (line 208; bases: `DomainEvent`)
  - `__post_init__()` (line 214)
- `ImportCompleted` (line 220; bases: `DomainEvent`)
  - `__post_init__()` (line 226)
- `ImportRolledBack` (line 234; bases: `DomainEvent`)
  - `__post_init__()` (line 240)
- `FactorMatched` (line 246; bases: `DomainEvent`)
  - `__post_init__()` (line 253)
- `FactorNotFound` (line 261; bases: `DomainEvent`)
  - `__post_init__()` (line 268)
- `ValidationFailed` (line 274; bases: `DomainEvent`)
  - `__post_init__()` (line 281)
- `WorkflowStateChanged` (line 287; bases: `DomainEvent`)
  - `__post_init__()` (line 295)
- `SagaStep` (line 305; bases: `Protocol`)
  - `async execute()` (line 308)
  - `async compensate()` (line 310)
- `Saga` (line 313; bases: `ABC`)
  - `__init__()` (line 321)
  - `async execute()` (line 328)
  - `async compensate()` (line 332)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `a`
- `abc`
- `dataclasses`
- `datetime`
- `decimal`
- `the`
- `typing`

#### Imports

- `__future__`
- `abc`
- `dataclasses`
- `datetime`
- `decimal`
- `typing`

### 4.32 `backend/engines/__init__.py`

- **Module:** `backend.engines`
- **Package:** `backend`
- **Lines:** 72
- **Size:** 2,051 bytes
- **Categories:** AI extraction, calculation, database / repository, emission factors, factor matching, reporting, validation / QA, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `engines`

#### Imports

- `__future__`
- `engines.ai_extraction`
- `engines.benchmarking`
- `engines.calculation`
- `engines.extraction`
- `engines.factor_matching`
- `engines.matching_stages`
- `engines.report_generation`
- `engines.validation`
- `engines.workflow`

### 4.33 `backend/engines/ai_extraction.py`

- **Module:** `backend.engines.ai_extraction`
- **Package:** `backend.engines`
- **Lines:** 254
- **Size:** 9,406 bytes
- **Categories:** AI extraction, audit / logging, document processing, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `AIExtractionEngine` (line 51; bases: `-`)
  - `__init__()` (line 63)
  - `fields()` (line 89)
  - `max_text_chars()` (line 94)
  - `async extract_fields()` (line 98)
  - `async _call_llm()` (line 133)
  - `_build_prompt()` (line 141)
  - `_parse_response()` (line 155)
  - `async _set_status()` (line 200)
  - `async _publish()` (line 203)
  - `async _audit()` (line 215)

#### Top-Level Functions

- `_strip_code_fence()` (line 242)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `None`
- `__future__`
- `an`
- `core`
- `datetime`
- `document`
- `domain`
- `engines`
- `exc`
- `infra`
- `the`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `core.logging`
- `datetime`
- `domain.document`
- `domain.workflow`
- `engines.extraction`
- `infra.audit_logger`
- `infra.event_bus`
- `infra.llm_client`
- `json`
- `typing`
- `uuid`

### 4.34 `backend/engines/benchmarking.py`

- **Module:** `backend.engines.benchmarking`
- **Package:** `backend.engines`
- **Lines:** 693
- **Size:** 27,458 bytes
- **Categories:** AI extraction, audit / logging, calculation, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `LogsSource` (line 131; bases: `Protocol`)
  - `async aggregate()` (line 134)
  - `async find_by_org()` (line 138)
- `OrgSource` (line 141; bases: `Protocol`)
  - `async get_metadata()` (line 144)
  - `async get_facilities()` (line 146)
- `FactorLookup` (line 149; bases: `Protocol`)
  - `async get()` (line 152)
- `BenchmarkingEngine` (line 155; bases: `-`)
  - `__init__()` (line 166)
  - `async benchmark()` (line 181)
  - `_total_metric()` (line 287)
  - `_total_yoy_metric()` (line 300)
  - `_intensity_metrics()` (line 338)
  - `_intensity_metric()` (line 358)
  - `_scope_metrics()` (line 400)
  - `async _facility_metrics()` (line 443)
  - `_activity_intensity_metrics()` (line 528)
  - `async _by_group()` (line 624)
  - `async _load_factors()` (line 648)
  - `async _audit()` (line 663)

#### Top-Level Functions

- `_year_range()` (line 63)
- `_dec()` (line 68)
- `_pct()` (line 77)
- `_provenance()` (line 84)
- `_group_logs_by_activity()` (line 111)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `decimal`
- `domain`
- `infra`
- `organization`
- `the`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `core.logging`
- `core.types`
- `datetime`
- `decimal`
- `domain.benchmarking`
- `domain.calculation`
- `domain.factor`
- `domain.organization`
- `infra.audit_logger`
- `typing`

### 4.35 `backend/engines/calculation.py`

- **Module:** `backend.engines.calculation`
- **Package:** `backend.engines`
- **Lines:** 426
- **Size:** 16,106 bytes
- **Categories:** AI extraction, audit / logging, calculation, emission factors, factor matching, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `CalculationSink` (line 55; bases: `Protocol`)
  - `async save_snapshot()` (line 64)
  - `async create()` (line 76)
  - `async save()` (line 89)
- `CalculationRequest` (line 93; bases: `-`)
  - `__post_init__()` (line 119)
  - `from_match_result()` (line 145)
- `CalculationEngine` (line 194; bases: `-`)
  - `__init__()` (line 207)
  - `algorithm_version()` (line 225)
  - `async calculate()` (line 229)
  - `verify()` (line 276)
  - `_build_snapshot()` (line 296)
  - `async _persist_log()` (line 322)
  - `async _publish_requested()` (line 360)
  - `async _publish_completed()` (line 372)
  - `async _publish()` (line 384)
  - `async _audit()` (line 396)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `a`
- `core`
- `datetime`
- `decimal`
- `domain`
- `exc`
- `infra`
- `the`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `core.logging`
- `dataclasses`
- `datetime`
- `decimal`
- `domain.calculation`
- `domain.factor`
- `domain.matching`
- `domain.workflow`
- `infra.audit_logger`
- `infra.event_bus`
- `typing`
- `uuid`

### 4.36 `backend/engines/extraction.py`

- **Module:** `backend.engines.extraction`
- **Package:** `backend.engines`
- **Lines:** 306
- **Size:** 11,260 bytes
- **Categories:** AI extraction, audit / logging, document processing, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `DocumentSink` (line 65; bases: `Protocol`)
  - `async update_status()` (line 71)
- `DocumentExtractionEngine` (line 74; bases: `-`)
  - `__init__()` (line 88)
  - `page_separator()` (line 116)
  - `table_delimiter()` (line 121)
  - `async extract()` (line 125)
  - `_build_result()` (line 176)
  - `_extract_tables()` (line 204)
  - `_emit_table()` (line 227)
  - `_extract_fields()` (line 241)
  - `async _set_status()` (line 267)
  - `async _publish()` (line 270)
  - `async _audit()` (line 282)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `datetime`
- `domain`
- `infra`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `core.logging`
- `datetime`
- `domain.document`
- `domain.workflow`
- `infra.audit_logger`
- `infra.event_bus`
- `re`
- `typing`
- `uuid`

### 4.37 `backend/engines/factor_matching.py`

- **Module:** `backend.engines.factor_matching`
- **Package:** `backend.engines`
- **Lines:** 257
- **Size:** 9,649 bytes
- **Categories:** AI extraction, audit / logging, emission factors, factor matching, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `FactorMatchingEngine` (line 52; bases: `-`)
  - `__init__()` (line 64)
  - `stages()` (line 82)
  - `config()` (line 87)
  - `async match()` (line 91)
  - `async _suggestions()` (line 125)
  - `async _finalize()` (line 145)
  - `async _publish_event()` (line 153)
  - `async _audit()` (line 191)

#### Top-Level Functions

- `build_matching_pipeline()` (line 218)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `datetime`
- `domain`
- `engines`
- `infra`
- `typing`

#### Imports

- `__future__`
- `core.logging`
- `datetime`
- `domain.matching`
- `domain.workflow`
- `engines.matching_stages`
- `infra.audit_logger`
- `infra.event_bus`
- `typing`
- `uuid`

### 4.38 `backend/engines/matching_stages.py`

- **Module:** `backend.engines.matching_stages`
- **Package:** `backend.engines`
- **Lines:** 362
- **Size:** 12,576 bytes
- **Categories:** AI extraction, audit / logging, emission factors, factor matching
- **V3 impact:** **NO CHANGE**

#### Classes

- `RepositoryAliasResolver` (line 34; bases: `-`)
  - `__init__()` (line 41)
  - `async __call__()` (line 46)
- `ExactMatchStage` (line 72; bases: `MatchingStage`)
  - `name()` (line 76)
  - `async execute()` (line 79)
- `NaturalKeyStage` (line 108; bases: `MatchingStage`)
  - `name()` (line 112)
  - `async execute()` (line 115)
- `KeywordSearchStage` (line 142; bases: `MatchingStage`)
  - `__init__()` (line 145)
  - `name()` (line 151)
  - `min_confidence()` (line 155)
  - `async execute()` (line 159)
- `AliasMatchStage` (line 187; bases: `MatchingStage`)
  - `__init__()` (line 190)
  - `name()` (line 194)
  - `async execute()` (line 197)
- `FuzzyMatchStage` (line 239; bases: `MatchingStage`)
  - `__init__()` (line 242)
  - `name()` (line 248)
  - `threshold()` (line 252)
  - `async execute()` (line 256)
- `SemanticMatchStage` (line 293; bases: `MatchingStage`)
  - `__init__()` (line 302)
  - `name()` (line 315)
  - `async execute()` (line 318)

#### Top-Level Functions

- `_exact_activity_matches()` (line 57)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `data`
- `difflib`
- `domain`
- `typing`

#### Imports

- `__future__`
- `core.logging`
- `data.factor_aliases`
- `difflib`
- `domain.factor`
- `domain.matching`
- `typing`

### 4.39 `backend/engines/report_generation.py`

- **Module:** `backend.engines.report_generation`
- **Package:** `backend.engines`
- **Lines:** 831
- **Size:** 31,698 bytes
- **Categories:** AI extraction, audit / logging, calculation, database / repository, emission factors, reporting, validation / QA, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `ReportContent` (line 94; bases: `-`)
  - `render()` (line 105)
  - `to_dict()` (line 119)
- `ReportGenerationResult` (line 128; bases: `-`)
- `ReportsStore` (line 141; bases: `Protocol`)
  - `async create_generation_request()` (line 144)
  - `async complete_generation()` (line 148)
- `OrgSource` (line 158; bases: `Protocol`)
  - `async get()` (line 161)
  - `async get_metadata()` (line 163)
- `LogsSource` (line 166; bases: `Protocol`)
  - `async aggregate()` (line 169)
  - `async find_by_org()` (line 173)
- `FactorLookup` (line 176; bases: `Protocol`)
  - `async get()` (line 179)
- `ValidationSurface` (line 182; bases: `Protocol`)
  - `async validate()` (line 185)
- `BenchmarkingSurface` (line 188; bases: `Protocol`)
  - `async benchmark()` (line 191)
- `CalculationSurface` (line 194; bases: `Protocol`)
  - `verify()` (line 197)
- `ReportGenerationEngine` (line 200; bases: `-`)
  - `__init__()` (line 219)
  - `async generate()` (line 250)
  - `async build_content()` (line 293)
  - `_metadata_section()` (line 335)
  - `_organization_section()` (line 347)
  - `_period_section()` (line 370)
  - `_totals_section()` (line 381)
  - `_scopes_section()` (line 410)
  - `_activities_section()` (line 432)
  - `_validation_section()` (line 478)
  - `_benchmarking_section()` (line 509)
  - `_provenance_section()` (line 547)
  - `_calculation_section()` (line 570)
  - `_lineage_section()` (line 621)
  - `_generation_section()` (line 648)
  - `_provenance()` (line 666)
  - `async _validate()` (line 692)
  - `async _benchmark()` (line 712)
  - `_ordered_sections()` (line 738)
  - `_template_order()` (line 760)
  - `async _load_factors()` (line 768)
  - `async _publish_report_generated()` (line 783)
  - `async _audit()` (line 802)

#### Top-Level Functions

- `_jsonable()` (line 78)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `CalculationEngine`
- `ValidationEngine`
- `__future__`
- `core`
- `dataclasses`
- `datetime`
- `decimal`
- `domain`
- `exc`
- `infra`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `core.logging`
- `core.types`
- `dataclasses`
- `datetime`
- `decimal`
- `domain.benchmarking`
- `domain.calculation`
- `domain.factor`
- `domain.organization`
- `domain.report`
- `domain.validation`
- `domain.workflow`
- `infra.audit_logger`
- `infra.event_bus`
- `json`
- `typing`
- `uuid`

### 4.40 `backend/engines/validation.py`

- **Module:** `backend.engines.validation`
- **Package:** `backend.engines`
- **Lines:** 931
- **Size:** 36,804 bytes
- **Categories:** AI extraction, audit / logging, calculation, emission factors, factor matching, validation / QA, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `LogsSource` (line 138; bases: `Protocol`)
  - `async find_by_org()` (line 141)
- `OrgSource` (line 144; bases: `Protocol`)
  - `async get()` (line 147)
  - `async get_metadata()` (line 149)
  - `async get_facilities()` (line 151)
  - `async get_assets()` (line 153)
- `FactorLookup` (line 156; bases: `Protocol`)
  - `async get()` (line 159)
- `ValidationEngine` (line 162; bases: `-`)
  - `__init__()` (line 175)
  - `async validate()` (line 196)
  - `validate_input()` (line 242)
  - `async validate_logs()` (line 309)
  - `_validate_log_integrity()` (line 343)
  - `_validate_log_period()` (line 383)
  - `_validate_log_consistency()` (line 423)
  - `validate_snapshot()` (line 512)
  - `validate_match()` (line 650)
  - `async validate_org()` (line 760)
  - `async _validate_membership()` (line 811)
  - `async verify_snapshots()` (line 866)
  - `async _audit()` (line 884)
  - `async _publish_validation_failed()` (line 902)

#### Top-Level Functions

- `_family_expected_scope()` (line 91)
- `_issue()` (line 109)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `collections`
- `core`
- `datetime`
- `decimal`
- `domain`
- `infra`
- `typing`

#### Imports

- `__future__`
- `collections.abc`
- `core.exceptions`
- `core.logging`
- `core.types`
- `datetime`
- `decimal`
- `domain.calculation`
- `domain.factor`
- `domain.matching`
- `domain.organization`
- `domain.validation`
- `domain.workflow`
- `infra.audit_logger`
- `infra.event_bus`
- `typing`
- `uuid`

### 4.41 `backend/engines/workflow.py`

- **Module:** `backend.engines.workflow`
- **Package:** `backend.engines`
- **Lines:** 851
- **Size:** 33,853 bytes
- **Categories:** AI extraction, audit / logging, calculation, document processing, emission factors, factor matching, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `WorkflowDocumentSink` (line 94; bases: `Protocol`)
  - `async get()` (line 100)
  - `async update_status()` (line 102)
- `WorkflowEventSink` (line 105; bases: `Protocol`)
  - `async store()` (line 111)
- `MatchInput` (line 115; bases: `-`)
- `ActivityResolver` (line 133; bases: `Protocol`)
  - `resolve()` (line 140)
- `InvoiceActivityResolver` (line 145; bases: `-`)
  - `__init__()` (line 154)
  - `resolve()` (line 159)
- `WorkflowResult` (line 185; bases: `-`)
- `_WorkflowRun` (line 200; bases: `-`)
- `WorkflowOrchestrator` (line 227; bases: `-`)
  - `__init__()` (line 252)
  - `state_machine()` (line 304)
  - `max_retries()` (line 309)
  - `ai_confidence_threshold()` (line 314)
  - `auto_review()` (line 319)
  - `handlers_registered()` (line 324)
  - `register_handlers()` (line 332)
  - `async submit_document()` (line 353)
  - `async process_document()` (line 374)
  - `async _start_run()` (line 401)
  - `async _drive()` (line 459)
  - `_reset_stage_latches()` (line 522)
  - `async _run_extraction()` (line 533)
  - `async _run_ai()` (line 553)
  - `async _run_matching()` (line 568)
  - `async _run_calculation()` (line 605)
  - `async _transition()` (line 644)
  - `async _fail()` (line 681)
  - `async _emit()` (line 699)
  - `async _store_event()` (line 704)
  - `async _publish()` (line 714)
  - `async _audit()` (line 726)
  - `async _on_document_uploaded()` (line 759)
  - `async _on_fields_extracted()` (line 766)
  - `async _on_factor_matched()` (line 773)
  - `_find_run_by_match_request()` (line 780)
  - `_result()` (line 790)

#### Top-Level Functions

- `_clean()` (line 810)
- `_parse_decimal()` (line 817)
- `_parse_date()` (line 826)
- `_parse_year()` (line 837)
- `_year_from_date()` (line 847)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `dataclasses`
- `datetime`
- `decimal`
- `domain`
- `engines`
- `exc`
- `extraction`
- `infra`
- `status`
- `the`
- `typing`

#### Imports

- `__future__`
- `asyncio`
- `core.exceptions`
- `core.logging`
- `dataclasses`
- `datetime`
- `decimal`
- `domain.document`
- `domain.matching`
- `domain.workflow`
- `engines.ai_extraction`
- `engines.calculation`
- `engines.extraction`
- `engines.factor_matching`
- `infra.audit_logger`
- `infra.event_bus`
- `typing`
- `uuid`

### 4.42 `backend/glossary copy.py`

- **Module:** `backend.glossary copy`
- **Package:** `backend`
- **Lines:** 5
- **Size:** 109 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `pydantic`
- `typing`

#### Imports

- `pydantic`
- `typing`

### 4.43 `backend/glossary.py`

- **Module:** `backend.glossary`
- **Package:** `backend`
- **Lines:** 172
- **Size:** 5,624 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `GlossaryTerm` (line 6; bases: `BaseModel`)

#### Top-Level Functions

- `async get_glossary()` (line 14)
- `async get_glossary_term()` (line 42)
- `async create_glossary_term()` (line 71)
- `async update_glossary_term()` (line 111)
- `async delete_glossary_term()` (line 146)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/api/glossary` | `get_glossary` | 14 |
| `GET` | `/api/glossary/{term_id}` | `get_glossary_term` | 42 |
| `POST` | `/api/glossary` | `create_glossary_term` | 71 |
| `PUT` | `/api/glossary/{term_id}` | `update_glossary_term` | 111 |
| `DELETE` | `/api/glossary/{term_id}` | `delete_glossary_term` | 146 |

#### Database / Supabase Tables Detected

- `a`
- `glossary`
- `pydantic`
- `typing`

#### Imports

- `pydantic`
- `typing`

### 4.44 `backend/infra/__init__.py`

- **Module:** `backend.infra`
- **Package:** `backend`
- **Lines:** 12
- **Size:** 541 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.45 `backend/infra/audit_logger.py`

- **Module:** `backend.infra.audit_logger`
- **Package:** `backend.infra`
- **Lines:** 255
- **Size:** 9,222 bytes
- **Categories:** AI extraction, Storage, audit / logging
- **V3 impact:** **NO CHANGE**

#### Classes

- `AuditSink` (line 43; bases: `Protocol`)
  - `async record()` (line 46)
  - `async query()` (line 48)
- `AuditLogger` (line 51; bases: `-`)
  - `__init__()` (line 59)
  - `default_actor()` (line 64)
  - `async record()` (line 68)
  - `async query()` (line 72)
  - `async log_action()` (line 76)
  - `audit()` (line 107)
  - `decorate()` (line 132)
  - `async wrapper()` (line 133)
  - `async _try_record()` (line 179)

#### Top-Level Functions

- `_resolve_arg()` (line 211)
- `_resolve_before()` (line 218)
- `init_audit_logger()` (line 234)
- `async get_audit_logger()` (line 241)
- `reset_audit_logger()` (line 250)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `data`
- `datetime`
- `domain`
- `infra`
- `its`
- `typing`

#### Imports

- `__future__`
- `core.logging`
- `data.audit`
- `data.base`
- `datetime`
- `domain.audit`
- `infra.supabase`
- `inspect`
- `typing`
- `uuid`

### 4.46 `backend/infra/config.py`

- **Module:** `backend.infra.config`
- **Package:** `backend.infra`
- **Lines:** 159
- **Size:** 5,177 bytes
- **Categories:** Storage
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `ConfigError` (line 23; bases: `CarbonTallyError`)
- `AppConfig` (line 95; bases: `-`)
  - `log_level_int()` (line 110)

#### Top-Level Functions

- `parse_int()` (line 35)
- `parse_bool()` (line 57)
- `parse_log_level()` (line 79)
- `load_config()` (line 115)
- `get_config()` (line 147)
- `reset_config()` (line 155)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `dataclasses`
- `exc`
- `infra`
- `the`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `dataclasses`
- `infra.supabase`
- `os`
- `typing`

### 4.47 `backend/infra/event_bus.py`

- **Module:** `backend.infra.event_bus`
- **Package:** `backend.infra`
- **Lines:** 166
- **Size:** 6,117 bytes
- **Categories:** AI extraction, audit / logging, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `EventBus` (line 36; bases: `-`)
  - `__init__()` (line 44)
  - `max_handlers()` (line 52)
  - `subscribe()` (line 56)
  - `unsubscribe()` (line 76)
  - `subscriber_count()` (line 90)
  - `clear()` (line 98)
  - `async publish()` (line 103)
  - `async publish_and_wait()` (line 116)
  - `async drain()` (line 127)
  - `_matching_handlers()` (line 133)
  - `async _invoke()` (line 138)

#### Top-Level Functions

- `get_event_bus()` (line 154)
- `reset_event_bus()` (line 162)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `domain`
- `typing`

#### Imports

- `__future__`
- `asyncio`
- `core.logging`
- `domain.workflow`
- `inspect`
- `typing`

### 4.48 `backend/infra/llm_client.py`

- **Module:** `backend.infra.llm_client`
- **Package:** `backend.infra`
- **Lines:** 178
- **Size:** 6,302 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- `ChatCompletionResponse` (line 32; bases: `-`)
- `LLMClient` (line 44; bases: `-`)
  - `__init__()` (line 57)
  - `base_url()` (line 81)
  - `model()` (line 86)
  - `async complete()` (line 90)
  - `_default_transport()` (line 134)
  - `transport()` (line 135)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `a`
- `core`
- `dataclasses`
- `exc`
- `typing`

#### Imports

- `__future__`
- `asyncio`
- `core.exceptions`
- `dataclasses`
- `json`
- `typing`
- `urllib.error`
- `urllib.request`

### 4.49 `backend/infra/search_index.py`

- **Module:** `backend.infra.search_index`
- **Package:** `backend.infra`
- **Lines:** 232
- **Size:** 8,395 bytes
- **Categories:** AI extraction, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `FactorSource` (line 37; bases: `Protocol`)
  - `async load_all_for_index()` (line 41)
- `FactorSearchIndex` (line 44; bases: `-`)
  - `__init__()` (line 52)
  - `default_limit()` (line 63)
  - `load()` (line 71)
  - `rebuild()` (line 80)
  - `add_many()` (line 84)
  - `add()` (line 89)
  - `remove()` (line 103)
  - `get()` (line 122)
  - `exact_natural_key()` (line 126)
  - `keyword_search()` (line 132)
  - `__len__()` (line 183)
  - `snapshot()` (line 186)
  - `async from_repository()` (line 191)
  - `_rebuild_token_tables()` (line 206)

#### Top-Level Functions

- `_tokens()` (line 29)
- `get_search_index()` (line 219)
- `reset_search_index()` (line 227)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `a`
- `collections`
- `domain`
- `the`
- `typing`

#### Imports

- `__future__`
- `collections`
- `domain.factor`
- `re`
- `typing`

### 4.50 `backend/infra/supabase.py`

- **Module:** `backend.infra.supabase`
- **Package:** `backend.infra`
- **Lines:** 149
- **Size:** 4,825 bytes
- **Categories:** Storage
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `_ensure_env()` (line 44)
- `get_supabase_url()` (line 54)
- `get_service_role_key()` (line 61)
- `get_database_url()` (line 73)
- `create_service_client()` (line 87)
- `get_service_client()` (line 108)
- `reset_service_client()` (line 116)
- `async get_service_pool()` (line 129)
- `close_service_pool()` (line 143)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dotenv`
- `supabase`
- `the`
- `typing`

#### Imports

- `__future__`
- `asyncpg`
- `dotenv`
- `os`
- `supabase`
- `typing`

### 4.51 `backend/main copy 2.py`

- **Module:** `backend.main copy 2`
- **Package:** `backend`
- **Lines:** 3966
- **Size:** 163,919 bytes
- **Categories:** AI extraction, API, Storage, authentication / security, database / repository, reporting
- **V3 impact:** **NO CHANGE**

#### Classes

- `WaitlistRequest` (line 119; bases: `BaseModel`)
- `WaitlistResponse` (line 127; bases: `BaseModel`)
- `BetaInviteRequest` (line 2599; bases: `BaseModel`)
- `BetaInviteResponse` (line 2603; bases: `BaseModel`)
- `GlossaryTerm` (line 3019; bases: `BaseModel`)
- `UserRole` (line 3652; bases: `str`)
- `UserPermissions` (line 3659; bases: `BaseModel`)
- `AuthUser` (line 3670; bases: `BaseModel`)

#### Top-Level Functions

- `async health_check()` (line 137)
- `async get_system_settings()` (line 149)
- `async validate_file_upload()` (line 196)
- `async test_upload()` (line 229)
- `async add_to_waitlist()` (line 245)
- `async get_waitlist()` (line 322)
- `async get_waitlist_count()` (line 349)
- `get_emission_factor()` (line 397)
- `get_activity_category()` (line 467)
- `process_fuel_data()` (line 507)
- `normalize_fuel()` (line 523)
- `process_utility_data()` (line 575)
- `normalize_utility_type()` (line 596)
- `process_scope3_data()` (line 653)
- `normalize_scope3()` (line 673)
- `async get_defra_mapping()` (line 738)
- `async get_defra_factors_by_year()` (line 751)
- `async get_available_defra_factors()` (line 777)
- `extract_issues_from_result()` (line 809)
- `has_low_confidence()` (line 920)
- `calculate_emissions_with_defra()` (line 929)
- `read_root()` (line 970)
- `async upload_csv()` (line 974)
- `async upload_pdf()` (line 1037)
- `async upload_batch()` (line 1126)
- `async get_settings()` (line 1440)
- `async update_settings()` (line 1456)
- `async repair_pdf()` (line 1493)
- `async notify_staff_batch_review_needed()` (line 1614)
- `async approve_pdf_batch()` (line 1664)
- `send_email()` (line 1679)
- `async notify_customer_manual_extraction()` (line 1705)
- `async notify_batch_completion()` (line 1779)
- `send_batch_completion_email()` (line 1832)
- `async import_defra_factors()` (line 1881)
- `async approve_extraction()` (line 1929)
- `async add_manual_review_note()` (line 2013)
- `async generate_secr_report()` (line 2066)
- `async generate_csrd_report()` (line 2103)
- `async generate_issb_report()` (line 2138)
- `async generate_all_reports()` (line 2173)
- `map_to_ghg_protocol()` (line 2214)
- `async export_ghg_inventory()` (line 2242)
- `send_review_queue_email()` (line 2340)
- `async queue_for_manual_review()` (line 2411)
- `send_confirmation_email_sync()` (line 2517)
- `async send_beta_invite()` (line 2610)
- `send_magic_link_email_sync()` (line 2692)
- `async resend_beta_confirmation()` (line 2793)
- `async unsubscribe_from_waitlist()` (line 2836)
- `async resubscribe_to_waitlist()` (line 2872)
- `generate_beta_code()` (line 2909)
- `send_beta_invite_email_sync()` (line 2916)
- `async get_glossary()` (line 3028)
- `async get_glossary_term()` (line 3072)
- `async create_glossary_term()` (line 3101)
- `async update_glossary_term()` (line 3142)
- `async delete_glossary_term()` (line 3184)
- `async magic_auth()` (line 3221)
- `send_temp_password_email()` (line 3547)
- `get_supabase_client()` (line 3749)
- `async get_current_user()` (line 3758)
- `async require_role()` (line 3879)
- `async role_checker()` (line 3883)
- `async require_permission()` (line 3893)
- `async permission_checker()` (line 3897)
- `async test_auth()` (line 3932)
- `async test_roles()` (line 3949)
- `async test_permissions()` (line 3959)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/` | `health_check` | 137 |
| `GET` | `/health` | `health_check` | 137 |
| `POST` | `/test-upload` | `test_upload` | 229 |
| `POST` | `/api/waitlist` | `add_to_waitlist` | 245 |
| `GET` | `/api/waitlist` | `get_waitlist` | 322 |
| `GET` | `/api/waitlist/count` | `get_waitlist_count` | 349 |
| `GET` | `/api/defra-mapping` | `get_defra_mapping` | 738 |
| `GET` | `/api/defra-factors/{reporting_year}` | `get_defra_factors_by_year` | 751 |
| `GET` | `/` | `read_root` | 970 |
| `POST` | `/upload-csv` | `upload_csv` | 974 |
| `POST` | `/upload-pdf` | `upload_pdf` | 1037 |
| `POST` | `/upload-batch` | `upload_batch` | 1126 |
| `GET` | `/api/settings` | `get_settings` | 1440 |
| `PUT` | `/api/settings` | `update_settings` | 1456 |
| `POST` | `/repair-pdf` | `repair_pdf` | 1493 |
| `POST` | `/approve-pdf-batch` | `approve_pdf_batch` | 1664 |
| `POST` | `/notify-customer-manual-extraction` | `notify_customer_manual_extraction` | 1705 |
| `POST` | `/notify-batch-completion` | `notify_batch_completion` | 1779 |
| `POST` | `/admin/import-defra-factors` | `import_defra_factors` | 1881 |
| `POST` | `/approve-extraction` | `approve_extraction` | 1929 |
| `POST` | `/add-manual-review-note` | `add_manual_review_note` | 2013 |
| `POST` | `/generate-secr-report` | `generate_secr_report` | 2066 |
| `POST` | `/generate-csrd-report` | `generate_csrd_report` | 2103 |
| `POST` | `/generate-issb-report` | `generate_issb_report` | 2138 |
| `POST` | `/generate-all-reports` | `generate_all_reports` | 2173 |
| `POST` | `/export-ghg-inventory` | `export_ghg_inventory` | 2242 |
| `POST` | `/api/waitlist/invite` | `send_beta_invite` | 2610 |
| `POST` | `/api/send-beta-confirmation` | `resend_beta_confirmation` | 2793 |
| `POST` | `/api/waitlist/unsubscribe` | `unsubscribe_from_waitlist` | 2836 |
| `POST` | `/api/waitlist/resubscribe` | `resubscribe_to_waitlist` | 2872 |
| `GET` | `/api/glossary` | `get_glossary` | 3028 |
| `GET` | `/api/glossary/{term_id}` | `get_glossary_term` | 3072 |
| `POST` | `/api/glossary` | `create_glossary_term` | 3101 |
| `PUT` | `/api/glossary/{term_id}` | `update_glossary_term` | 3142 |
| `DELETE` | `/api/glossary/{term_id}` | `delete_glossary_term` | 3184 |
| `GET` | `/api/auth/magic` | `magic_auth` | 3221 |
| `GET` | `/api/test/auth` | `test_auth` | 3932 |
| `GET` | `/api/test/roles` | `test_roles` | 3949 |
| `GET` | `/api/test/permissions` | `test_permissions` | 3959 |

#### Database / Supabase Tables Detected

- `CarbonTally`
- `PIL`
- `a`
- `activity_categories`
- `assets`
- `auth`
- `batch`
- `beta_access_codes`
- `beta_users`
- `database`
- `datetime`
- `defra_conversion_factors`
- `documents`
- `dotenv`
- `emissions_logs`
- `environment`
- `facilities`
- `fastapi`
- `fpdf`
- `glossary`
- `manual_review_queue`
- `organization_members`
- `organizations`
- `pdf2image`
- `pdf_engine`
- `pydantic`
- `pypdf`
- `report_generator`
- `reportlab`
- `settings`
- `staff_profiles`
- `start_date`
- `summary`
- `supabase`
- `system`
- `system_settings`
- `the`
- `token`
- `typing`
- `upload_batches`
- `user`
- `validation`
- `waitlist`
- `your`

#### Imports

- `PIL`
- `auth`
- `base64`
- `datetime`
- `dotenv`
- `fastapi`
- `fastapi.middleware.cors`
- `fastapi.security`
- `fpdf`
- `httpx`
- `io`
- `jwt`
- `numpy`
- `os`
- `pandas`
- `pdf2image`
- `pdf_engine`
- `pydantic`
- `pypdf`
- `pytesseract`
- `re`
- `report_generator`
- `reportlab.lib.pagesizes`
- `reportlab.lib.units`
- `reportlab.lib.utils`
- `reportlab.pdfgen`
- `requests`
- `resend`
- `secrets`
- `string`
- `supabase`
- `traceback`
- `typing`
- `uuid`

### 4.52 `backend/main copy.py`

- **Module:** `backend.main copy`
- **Package:** `backend`
- **Lines:** 3257
- **Size:** 138,680 bytes
- **Categories:** AI extraction, API, Storage, database / repository, reporting
- **V3 impact:** **NO CHANGE**

#### Classes

- `WaitlistRequest` (line 101; bases: `BaseModel`)
- `WaitlistResponse` (line 109; bases: `BaseModel`)
- `BetaInviteRequest` (line 2209; bases: `BaseModel`)
- `BetaInviteResponse` (line 2213; bases: `BaseModel`)
- `GlossaryTerm` (line 2629; bases: `BaseModel`)

#### Top-Level Functions

- `async health_check()` (line 119)
- `async add_to_waitlist()` (line 132)
- `async get_waitlist()` (line 209)
- `async get_waitlist_count()` (line 236)
- `get_emission_factor()` (line 279)
- `get_activity_category()` (line 335)
- `process_fuel_data()` (line 371)
- `normalize_fuel()` (line 386)
- `process_utility_data()` (line 428)
- `normalize_utility_type()` (line 448)
- `process_scope3_data()` (line 494)
- `normalize_scope3()` (line 514)
- `extract_issues_from_result()` (line 565)
- `has_low_confidence()` (line 676)
- `calculate_emissions_with_defra()` (line 685)
- `read_root()` (line 726)
- `async upload_csv()` (line 730)
- `async upload_pdf()` (line 775)
- `async upload_batch()` (line 835)
- `async repair_pdf()` (line 1103)
- `async notify_staff_batch_review_needed()` (line 1224)
- `async approve_pdf_batch()` (line 1274)
- `send_email()` (line 1289)
- `async notify_customer_manual_extraction()` (line 1315)
- `async notify_batch_completion()` (line 1389)
- `send_batch_completion_email()` (line 1442)
- `async import_defra_factors()` (line 1491)
- `async approve_extraction()` (line 1539)
- `async add_manual_review_note()` (line 1623)
- `async generate_secr_report()` (line 1676)
- `async generate_csrd_report()` (line 1713)
- `async generate_issb_report()` (line 1748)
- `async generate_all_reports()` (line 1783)
- `map_to_ghg_protocol()` (line 1824)
- `async export_ghg_inventory()` (line 1852)
- `send_review_queue_email()` (line 1950)
- `async queue_for_manual_review()` (line 2021)
- `send_confirmation_email_sync()` (line 2127)
- `async send_beta_invite()` (line 2220)
- `send_magic_link_email_sync()` (line 2302)
- `async resend_beta_confirmation()` (line 2403)
- `async unsubscribe_from_waitlist()` (line 2446)
- `async resubscribe_to_waitlist()` (line 2482)
- `generate_beta_code()` (line 2519)
- `send_beta_invite_email_sync()` (line 2526)
- `async get_glossary()` (line 2638)
- `async get_glossary_term()` (line 2682)
- `async create_glossary_term()` (line 2711)
- `async update_glossary_term()` (line 2752)
- `async delete_glossary_term()` (line 2794)
- `async magic_auth()` (line 2831)
- `send_temp_password_email()` (line 3157)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/` | `health_check` | 119 |
| `GET` | `/health` | `health_check` | 119 |
| `POST` | `/api/waitlist` | `add_to_waitlist` | 132 |
| `GET` | `/api/waitlist` | `get_waitlist` | 209 |
| `GET` | `/api/waitlist/count` | `get_waitlist_count` | 236 |
| `GET` | `/` | `read_root` | 726 |
| `POST` | `/upload-csv` | `upload_csv` | 730 |
| `POST` | `/upload-pdf` | `upload_pdf` | 775 |
| `POST` | `/upload-batch` | `upload_batch` | 835 |
| `POST` | `/repair-pdf` | `repair_pdf` | 1103 |
| `POST` | `/approve-pdf-batch` | `approve_pdf_batch` | 1274 |
| `POST` | `/notify-customer-manual-extraction` | `notify_customer_manual_extraction` | 1315 |
| `POST` | `/notify-batch-completion` | `notify_batch_completion` | 1389 |
| `POST` | `/admin/import-defra-factors` | `import_defra_factors` | 1491 |
| `POST` | `/approve-extraction` | `approve_extraction` | 1539 |
| `POST` | `/add-manual-review-note` | `add_manual_review_note` | 1623 |
| `POST` | `/generate-secr-report` | `generate_secr_report` | 1676 |
| `POST` | `/generate-csrd-report` | `generate_csrd_report` | 1713 |
| `POST` | `/generate-issb-report` | `generate_issb_report` | 1748 |
| `POST` | `/generate-all-reports` | `generate_all_reports` | 1783 |
| `POST` | `/export-ghg-inventory` | `export_ghg_inventory` | 1852 |
| `POST` | `/api/waitlist/invite` | `send_beta_invite` | 2220 |
| `POST` | `/api/send-beta-confirmation` | `resend_beta_confirmation` | 2403 |
| `POST` | `/api/waitlist/unsubscribe` | `unsubscribe_from_waitlist` | 2446 |
| `POST` | `/api/waitlist/resubscribe` | `resubscribe_to_waitlist` | 2482 |
| `GET` | `/api/glossary` | `get_glossary` | 2638 |
| `GET` | `/api/glossary/{term_id}` | `get_glossary_term` | 2682 |
| `POST` | `/api/glossary` | `create_glossary_term` | 2711 |
| `PUT` | `/api/glossary/{term_id}` | `update_glossary_term` | 2752 |
| `DELETE` | `/api/glossary/{term_id}` | `delete_glossary_term` | 2794 |
| `GET` | `/api/auth/magic` | `magic_auth` | 2831 |

#### Database / Supabase Tables Detected

- `CarbonTally`
- `PIL`
- `a`
- `activity_categories`
- `assets`
- `batch`
- `beta_access_codes`
- `beta_users`
- `database`
- `datetime`
- `defra_conversion_factors`
- `documents`
- `dotenv`
- `emissions_logs`
- `facilities`
- `fastapi`
- `fpdf`
- `glossary`
- `manual`
- `manual_review_queue`
- `organization_members`
- `organizations`
- `pdf2image`
- `pdf_engine`
- `pydantic`
- `pypdf`
- `report_generator`
- `reportlab`
- `staff_profiles`
- `start_date`
- `summary`
- `supabase`
- `the`
- `through`
- `typing`
- `upload_batches`
- `user`
- `waitlist`
- `your`

#### Imports

- `PIL`
- `base64`
- `datetime`
- `dotenv`
- `fastapi`
- `fastapi.middleware.cors`
- `fpdf`
- `httpx`
- `io`
- `numpy`
- `os`
- `pandas`
- `pdf2image`
- `pdf_engine`
- `pydantic`
- `pypdf`
- `pytesseract`
- `re`
- `report_generator`
- `reportlab.lib.pagesizes`
- `reportlab.lib.units`
- `reportlab.lib.utils`
- `reportlab.pdfgen`
- `requests`
- `resend`
- `secrets`
- `string`
- `supabase`
- `traceback`
- `typing`
- `uuid`

### 4.53 `backend/main.py`

- **Module:** `backend.main`
- **Package:** `backend`
- **Lines:** 363
- **Size:** 12,883 bytes
- **Categories:** AI extraction, API, database / repository
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `async startup_event()` (line 242)
- `async root()` (line 249)
- `async health_check()` (line 262)
- `async http_exception_handler()` (line 296)
- `async generic_exception_handler()` (line 312)
- `async shutdown_event()` (line 336)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/` | `root` | 249 |
| `GET` | `/health` | `health_check` | 262 |

#### Database / Supabase Tables Detected

- `config`
- `database`
- `datetime`
- `dotenv`
- `fastapi`
- `glossary`
- `routes`

#### Imports

- `config`
- `database`
- `datetime`
- `dotenv`
- `fastapi`
- `fastapi.middleware.cors`
- `fastapi.responses`
- `os`
- `routes`
- `routes.admin`
- `routes.organizations`
- `traceback`
- `uvicorn`

### 4.54 `backend/middleware/rate_limit.py`

- **Module:** `backend.middleware.rate_limit`
- **Package:** `backend.middleware`
- **Lines:** 54
- **Size:** 1,985 bytes
- **Categories:** API
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `RateLimitMiddleware` (line 12; bases: `BaseHTTPMiddleware`)
  - `__init__()` (line 13)
  - `async dispatch()` (line 18)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `fastapi`
- `starlette`
- `typing`

#### Imports

- `fastapi`
- `os`
- `starlette.middleware.base`
- `time`
- `typing`

### 4.55 `backend/pdf_engine.py`

- **Module:** `backend.pdf_engine`
- **Package:** `backend`
- **Lines:** 340
- **Size:** 13,700 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `PDFExtractor` (line 12; bases: `-`)
  - `__init__()` (line 18)
  - `extract_and_parse()` (line 25)
  - `_extract_text_direct()` (line 58)
  - `_extract_text_ocr()` (line 72)
  - `_get_page_count()` (line 85)
  - `_parse_utility_bill()` (line 93)
  - `_parse_fuel_invoice()` (line 216)
  - `_parse_scope3_document()` (line 289)
  - `extract_and_parse_image()` (line 305)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `PIL`
- `datetime`
- `digital`
- `document`
- `file`
- `image`
- `pdf2image`
- `scanned`

#### Imports

- `PIL`
- `datetime`
- `io`
- `pdf2image`
- `pdfplumber`
- `pytesseract`
- `re`
- `uuid`

### 4.56 `backend/process_emissions.py`

- **Module:** `backend.process_emissions`
- **Package:** `backend`
- **Lines:** 106
- **Size:** 4,314 bytes
- **Categories:** calculation
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `process_fuel_card_data()` (line 6)
- `normalize_fuel_type()` (line 37)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `json`
- `numpy`
- `pandas`

### 4.57 `backend/report_generator.py`

- **Module:** `backend.report_generator`
- **Package:** `backend`
- **Lines:** 1072
- **Size:** 45,231 bytes
- **Categories:** API, Storage, database / repository, reporting
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `EmissionSource` (line 22; bases: `-`)
- `YearOverYearComparison` (line 35; bases: `-`)
- `MethodologyNote` (line 47; bases: `-`)
- `EfficiencyMeasure` (line 58; bases: `-`)
- `EnhancedSustainabilityReportPDF` (line 156; bases: `FPDF`)
  - `__init__()` (line 159)
  - `header()` (line 183)
  - `footer()` (line 198)
  - `add_paragraph()` (line 209)
  - `add_section_title()` (line 216)
  - `add_subsection_title()` (line 225)
  - `add_metric_box()` (line 232)
  - `add_cover_page()` (line 260)
  - `add_section_with_border()` (line 330)
  - `add_narrative_box()` (line 350)
  - `add_trend_indicator()` (line 377)
  - `add_data_table()` (line 406)
  - `add_methodology_section()` (line 459)
- `EnhancedSustainabilityReportGenerator` (line 506; bases: `-`)
  - `__init__()` (line 509)
  - `_fetch_organization_data()` (line 537)
  - `_fetch_emissions_data()` (line 580)
  - `_calculate_scope_totals()` (line 611)
  - `_calculate_yoy_comparison()` (line 640)
  - `_generate_methodology_notes()` (line 683)
  - `_generate_efficiency_measures()` (line 713)
  - `_generate_emission_sources()` (line 753)
  - `_generate_report_highlights()` (line 820)
  - `generate_enhanced_secr_report()` (line 841)
  - `_generate_enhanced_pdf()` (line 891)
- `EnhancedReportRequest` (line 1034; bases: `BaseModel`)

#### Top-Level Functions

- `sanitize_text()` (line 71)
- `format_currency()` (line 85)
- `get_trend_color()` (line 93)
- `generate_trend_arrow()` (line 106)
- `calculate_intensity_ratios()` (line 119)
- `async generate_enhanced_sustainability_report()` (line 1041)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/generate-enhanced-report` | `generate_enhanced_sustainability_report` | 1041 |

#### Database / Supabase Tables Detected

- `Scope`
- `data`
- `dataclasses`
- `datetime`
- `direct`
- `emissions`
- `emissions_logs`
- `fastapi`
- `fpdf`
- `operational`
- `organization_metadata`
- `organizations`
- `pydantic`
- `supabase`
- `the`
- `typing`

#### Imports

- `base64`
- `dataclasses`
- `datetime`
- `fastapi`
- `fpdf`
- `io`
- `os`
- `pandas`
- `pydantic`
- `supabase`
- `traceback`
- `typing`

### 4.58 `backend/routes/__init__.py`

- **Module:** `backend.routes`
- **Package:** `backend`
- **Lines:** 87
- **Size:** 1,868 bytes
- **Categories:** API
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.`
- `.admin`
- `.organizations`

### 4.59 `backend/routes/admin/__init__.py`

- **Module:** `backend.routes.admin`
- **Package:** `backend.routes`
- **Lines:** 39
- **Size:** 825 bytes
- **Categories:** API
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.`

### 4.60 `backend/routes/admin/analytics.py`

- **Module:** `backend.routes.admin.analytics`
- **Package:** `backend.routes.admin`
- **Lines:** 278
- **Size:** 10,492 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async get_system_health()` (line 19)
- `async get_system_performance()` (line 128)
- `async get_system_usage()` (line 207)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/system/health` | `get_system_health` | 19 |
| `GET` | `/system/performance` | `get_system_performance` | 128 |
| `GET` | `/system/usage` | `get_system_usage` | 207 |

#### Database / Supabase Tables Detected

- `auth`
- `database`
- `datetime`
- `fastapi`
- `manual_review_queue`
- `organization_files`
- `organizations`
- `processing_logs`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `typing`

### 4.61 `backend/routes/admin/assignments.py`

- **Module:** `backend.routes.admin.assignments`
- **Package:** `backend.routes.admin`
- **Lines:** 460
- **Size:** 17,152 bytes
- **Categories:** API, authentication / security, database / repository, document processing
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `AssignRequest` (line 16; bases: `BaseModel`)
- `BatchAssignRequest` (line 21; bases: `BaseModel`)

#### Top-Level Functions

- `async get_available_reviews()` (line 30)
- `async get_staff_list()` (line 174)
- `async assign_batch()` (line 231)
- `async get_assignment_stats()` (line 375)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/available` | `get_available_reviews` | 30 |
| `GET` | `/staff` | `get_staff_list` | 174 |
| `POST` | `/batch/{batch_id}/assign` | `assign_batch` | 231 |
| `GET` | `/assignment-stats` | `get_assignment_stats` | 375 |

#### Database / Supabase Tables Detected

- `auth`
- `batch`
- `database`
- `datetime`
- `document`
- `fastapi`
- `manual_review_queue`
- `organization_files`
- `pydantic`
- `review`
- `review_assignment_history`
- `staff_profiles`
- `typing`
- `upload_batches`
- `utils`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `traceback`
- `typing`
- `utils`

### 4.62 `backend/routes/admin/audit.py`

- **Module:** `backend.routes.admin.audit`
- **Package:** `backend.routes.admin`
- **Lines:** 197
- **Size:** 6,533 bytes
- **Categories:** API, CSV / Excel, audit / logging, authentication / security, database / repository
- **V3 impact:** **NO CHANGE**

#### Classes

- `ActivityFilter` (line 22; bases: `BaseModel`)

#### Top-Level Functions

- `async get_activity_logs()` (line 34)
- `async get_activity_log_detail()` (line 77)
- `async export_activity_logs()` (line 107)
- `async search_activity_logs()` (line 170)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/activity` | `get_activity_logs` | 34 |
| `GET` | `/activity/{log_id}` | `get_activity_log_detail` | 77 |
| `GET` | `/activity/export` | `export_activity_logs` | 107 |
| `GET` | `/activity/search` | `search_activity_logs` | 170 |

#### Database / Supabase Tables Detected

- `activity_logs`
- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

#### Imports

- `auth`
- `csv`
- `database`
- `datetime`
- `fastapi`
- `io`
- `json`
- `pydantic`
- `typing`

### 4.63 `backend/routes/admin/audit_logs.py`

- **Module:** `backend.routes.admin.audit_logs`
- **Package:** `backend.routes.admin`
- **Lines:** 1432
- **Size:** 55,504 bytes
- **Categories:** API, Storage, audit / logging, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `AuditLogResponse` (line 20; bases: `BaseModel`)
- `AuditLogsListResponse` (line 44; bases: `BaseModel`)
- `AuditStatsResponse` (line 53; bases: `BaseModel`)
- `ExportLogsResponse` (line 67; bases: `BaseModel`)
- `MessageLogResponse` (line 77; bases: `BaseModel`)
- `NotificationLogResponse` (line 94; bases: `BaseModel`)
- `VerificationLogResponse` (line 113; bases: `BaseModel`)
- `UserAuditActivityResponse` (line 919; bases: `BaseModel`)
- `UserAuditSummaryResponse` (line 935; bases: `BaseModel`)

#### Top-Level Functions

- `async search_audit_logs()` (line 135)
- `async get_message_logs()` (line 300)
- `async get_notification_logs()` (line 392)
- `async get_verification_logs()` (line 490)
- `async export_logs()` (line 592)
- `async get_audit_statistics()` (line 690)
- `async get_audit_organizations()` (line 846)
- `async get_audit_actions()` (line 878)
- `async get_user_audit_activity()` (line 951)
- `async get_user_audit_summary()` (line 1106)
- `async get_user_activity_details()` (line 1271)
- `async export_user_audit_data()` (line 1373)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/` | `search_audit_logs` | 135 |
| `GET` | `/messages` | `get_message_logs` | 300 |
| `GET` | `/notifications` | `get_notification_logs` | 392 |
| `GET` | `/verifications` | `get_verification_logs` | 490 |
| `GET` | `/export` | `export_logs` | 592 |
| `GET` | `/stats` | `get_audit_statistics` | 690 |
| `GET` | `/organizations` | `get_audit_organizations` | 846 |
| `GET` | `/actions` | `get_audit_actions` | 878 |
| `GET` | `/users` | `get_user_audit_activity` | 951 |
| `GET` | `/users/summary` | `get_user_audit_summary` | 1106 |
| `GET` | `/users/{user_id}/activities` | `get_user_activity_details` | 1271 |
| `GET` | `/users/export` | `export_user_audit_data` | 1373 |

#### Database / Supabase Tables Detected

- `audit_logs`
- `auth`
- `customer_verifications`
- `database`
- `datetime`
- `fastapi`
- `first`
- `last`
- `message_activity_log`
- `messages`
- `notification_delivery_log`
- `notifications`
- `now`
- `organizations`
- `pydantic`
- `supabase`
- `typing`
- `verification_activity_log`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `json`
- `pydantic`
- `supabase`
- `traceback`
- `typing`

### 4.64 `backend/routes/admin/beta.py`

- **Module:** `backend.routes.admin.beta`
- **Package:** `backend.routes.admin`
- **Lines:** 500
- **Size:** 16,058 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `BetaCodeCreate` (line 21; bases: `BaseModel`)
- `BetaCodeUpdate` (line 26; bases: `BaseModel`)
- `BetaCodeValidate` (line 29; bases: `BaseModel`)
- `BetaUserCreate` (line 32; bases: `BaseModel`)
- `BetaUserUpdate` (line 37; bases: `BaseModel`)

#### Top-Level Functions

- `generate_beta_code()` (line 45)
- `async get_beta_codes()` (line 55)
- `async create_beta_code()` (line 97)
- `async update_beta_code_status()` (line 143)
- `async delete_beta_code()` (line 192)
- `async validate_beta_code()` (line 216)
- `async get_beta_users()` (line 286)
- `async create_beta_user()` (line 317)
- `async update_beta_user_access()` (line 384)
- `async delete_beta_user()` (line 428)
- `async get_beta_stats()` (line 452)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/codes` | `get_beta_codes` | 55 |
| `POST` | `/codes` | `create_beta_code` | 97 |
| `PUT` | `/codes/{code_id}/status` | `update_beta_code_status` | 143 |
| `DELETE` | `/codes/{code_id}` | `delete_beta_code` | 192 |
| `GET` | `/codes/validate/{code}` | `validate_beta_code` | 216 |
| `GET` | `/users` | `get_beta_users` | 286 |
| `POST` | `/users` | `create_beta_user` | 317 |
| `PUT` | `/users/{user_id}/access` | `update_beta_user_access` | 384 |
| `DELETE` | `/users/{user_id}` | `delete_beta_user` | 428 |
| `GET` | `/users/stats` | `get_beta_stats` | 452 |

#### Database / Supabase Tables Detected

- `auth`
- `beta`
- `beta_access_codes`
- `beta_users`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `secrets`
- `string`
- `typing`

### 4.65 `backend/routes/admin/bulk.py`

- **Module:** `backend.routes.admin.bulk`
- **Package:** `backend.routes.admin`
- **Lines:** 302
- **Size:** 11,068 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `BulkOrganizationStatusUpdate` (line 19; bases: `BaseModel`)
- `BulkOperationResult` (line 24; bases: `BaseModel`)

#### Top-Level Functions

- `async bulk_update_organization_status()` (line 35)
- `async bulk_update_document_status()` (line 131)
- `async bulk_delete_documents()` (line 219)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/organizations/status` | `bulk_update_organization_status` | 35 |
| `POST` | `/documents/status` | `bulk_update_document_status` | 131 |
| `DELETE` | `/documents/bulk` | `bulk_delete_documents` | 219 |

#### Database / Supabase Tables Detected

- `activity_logs`
- `auth`
- `completed`
- `database`
- `datetime`
- `document`
- `fastapi`
- `organization`
- `organization_files`
- `organizations`
- `pydantic`
- `status`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

### 4.66 `backend/routes/admin/dashboard.py`

- **Module:** `backend.routes.admin.dashboard`
- **Package:** `backend.routes.admin`
- **Lines:** 1579
- **Size:** 65,445 bytes
- **Categories:** API, Storage, authentication / security, database / repository, reporting
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `OverallStatsResponse` (line 20; bases: `BaseModel`)
- `DocumentOverviewResponse` (line 37; bases: `BaseModel`)
- `StaffPerformanceResponse` (line 50; bases: `BaseModel`)
- `OrganizationHealthResponse` (line 66; bases: `BaseModel`)
- `SLAComplianceResponse` (line 80; bases: `BaseModel`)
- `SystemHealthResponse` (line 92; bases: `BaseModel`)
- `QueueOverviewResponse` (line 109; bases: `BaseModel`)
- `ExportDashboardDataResponse` (line 123; bases: `BaseModel`)
- `AdminAlertResponse` (line 1050; bases: `BaseModel`)
- `AdminAlertSummaryResponse` (line 1068; bases: `BaseModel`)

#### Top-Level Functions

- `async get_overall_stats()` (line 138)
- `async get_document_overview()` (line 272)
- `async get_staff_performance()` (line 366)
- `async get_organization_health()` (line 441)
- `async get_sla_compliance()` (line 547)
- `async get_system_health()` (line 663)
- `async get_queue_overview()` (line 769)
- `async export_dashboard_data()` (line 899)
- `async get_document_type_dashboard()` (line 982)
- `async get_admin_alerts()` (line 1085)
- `async get_admin_alert_summary()` (line 1382)
- `async resolve_admin_alert()` (line 1440)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/stats` | `get_overall_stats` | 138 |
| `GET` | `/documents` | `get_document_overview` | 272 |
| `GET` | `/staff` | `get_staff_performance` | 366 |
| `GET` | `/organizations` | `get_organization_health` | 441 |
| `GET` | `/sla` | `get_sla_compliance` | 547 |
| `GET` | `/system` | `get_system_health` | 663 |
| `GET` | `/queue` | `get_queue_overview` | 769 |
| `GET` | `/export` | `export_dashboard_data` | 899 |
| `GET` | `/document-types` | `get_document_type_dashboard` | 982 |
| `GET` | `/alerts` | `get_admin_alerts` | 1085 |
| `GET` | `/alerts/summary` | `get_admin_alert_summary` | 1382 |
| `PUT` | `/alerts/{alert_id}/resolve` | `resolve_admin_alert` | 1440 |

#### Database / Supabase Tables Detected

- `ID`
- `a`
- `audit`
- `audit_logs`
- `auth`
- `customer_documents`
- `database`
- `datetime`
- `document_types`
- `emissions_logs`
- `fastapi`
- `get_admin_alerts`
- `manual_review_queue`
- `needed`
- `now`
- `organization_files`
- `organization_members`
- `organizations`
- `pydantic`
- `staff_profiles`
- `supabase`
- `the`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `json`
- `pydantic`
- `supabase`
- `traceback`
- `typing`

### 4.67 `backend/routes/admin/defra.py`

- **Module:** `backend.routes.admin.defra`
- **Package:** `backend.routes.admin`
- **Lines:** 613
- **Size:** 21,843 bytes
- **Categories:** API, authentication / security, database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `DEFRAFactorBase` (line 14; bases: `BaseModel`)
  - `validate_activity_type()` (line 21)
  - `Config()` (line 25)
- `DEFRAFactorCreate` (line 34; bases: `DEFRAFactorBase`)
- `DEFRAFactorUpdate` (line 38; bases: `BaseModel`)
  - `validate_activity_type()` (line 45)
  - `Config()` (line 51)
- `DEFRAFactorBulkCreate` (line 60; bases: `BaseModel`)
  - `Config()` (line 64)
- `DEFRAFactorResponse` (line 82; bases: `BaseModel`)
  - `Config()` (line 90)
- `DEFRAFactorListResponse` (line 101; bases: `BaseModel`)

#### Top-Level Functions

- `async get_available_years()` (line 112)
- `async get_available_activities()` (line 126)
- `async get_admin_defra_factors()` (line 144)
- `async get_defra_factor()` (line 200)
- `async create_defra_factor()` (line 242)
- `async create_defra_factors_bulk()` (line 301)
- `async update_defra_factor()` (line 365)
- `async delete_defra_factor()` (line 455)
- `async get_defra_years()` (line 513)
- `async get_defra_activities()` (line 538)
- `async validate_defra_factor()` (line 573)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/factors` | `get_admin_defra_factors` | 144 |
| `GET` | `/factors/{factor_id}` | `get_defra_factor` | 200 |
| `POST` | `/factors` | `create_defra_factor` | 242 |
| `POST` | `/factors/bulk` | `create_defra_factors_bulk` | 301 |
| `PUT` | `/factors/{factor_id}` | `update_defra_factor` | 365 |
| `DELETE` | `/factors/{factor_id}` | `delete_defra_factor` | 455 |
| `GET` | `/years` | `get_defra_years` | 513 |
| `GET` | `/activities` | `get_defra_activities` | 538 |
| `GET` | `/validate` | `validate_defra_factor` | 573 |

#### Database / Supabase Tables Detected

- `DEFRA`
- `a`
- `auth`
- `database`
- `datetime`
- `defra_conversion_factors`
- `dict`
- `emissions_logs`
- `factor`
- `fastapi`
- `pydantic`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `traceback`
- `typing`

### 4.68 `backend/routes/admin/document-types.py`

- **Module:** `backend.routes.admin.document-types`
- **Package:** `backend.routes.admin`
- **Lines:** 808
- **Size:** 32,003 bytes
- **Categories:** API, authentication / security, database / repository, document processing
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `DocumentTypeCreate` (line 15; bases: `BaseModel`)
- `DocumentTypeUpdate` (line 27; bases: `BaseModel`)
- `DocumentTypeResponse` (line 39; bases: `BaseModel`)

#### Top-Level Functions

- `async get_document_types()` (line 60)
- `async create_document_type()` (line 85)
- `async update_document_type()` (line 133)
- `async delete_document_type()` (line 179)
- `async get_document_type_categories()` (line 206)
- `async seed_default_document_types()` (line 225)
- `async get_document_type_by_id()` (line 337)
- `async bulk_create_document_types()` (line 366)
- `async bulk_update_document_types()` (line 430)
- `async get_document_type_mappings()` (line 501)
- `async update_document_type_mappings()` (line 543)
- `async get_extraction_templates()` (line 603)
- `async create_extraction_template()` (line 656)
- `async update_extraction_template()` (line 727)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/` | `get_document_types` | 60 |
| `POST` | `/` | `create_document_type` | 85 |
| `PUT` | `/{type_id}` | `update_document_type` | 133 |
| `DELETE` | `/{type_id}` | `delete_document_type` | 179 |
| `GET` | `/categories` | `get_document_type_categories` | 206 |
| `POST` | `/seed-defaults` | `seed_default_document_types` | 225 |
| `GET` | `/{type_id}` | `get_document_type_by_id` | 337 |
| `POST` | `/bulk-create` | `bulk_create_document_types` | 366 |
| `PUT` | `/bulk-update` | `bulk_update_document_types` | 430 |
| `GET` | `/mapping` | `get_document_type_mappings` | 501 |
| `PUT` | `/mapping` | `update_document_type_mappings` | 543 |
| `GET` | `/extraction-templates` | `get_extraction_templates` | 603 |
| `POST` | `/extraction-templates` | `create_extraction_template` | 656 |
| `PUT` | `/extraction-templates/{template_id}` | `update_extraction_template` | 727 |

#### Database / Supabase Tables Detected

- `ERP`
- `a`
- `accounting`
- `an`
- `auth`
- `data`
- `database`
- `datetime`
- `document`
- `document_types`
- `extraction`
- `fastapi`
- `in`
- `mappings`
- `metadata`
- `pydantic`
- `suppliers`
- `template`
- `typing`
- `update`
- `utility`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

### 4.69 `backend/routes/admin/email_templates.py`

- **Module:** `backend.routes.admin.email_templates`
- **Package:** `backend.routes.admin`
- **Lines:** 670
- **Size:** 25,484 bytes
- **Categories:** AI extraction, API, authentication / security, database / repository
- **V3 impact:** **NO CHANGE**

#### Classes

- `EmailTemplateCreate` (line 20; bases: `BaseModel`)
- `EmailTemplateUpdate` (line 30; bases: `BaseModel`)
- `EmailTemplatePreview` (line 40; bases: `BaseModel`)
- `EmailTemplateResponse` (line 44; bases: `BaseModel`)

#### Top-Level Functions

- `async get_default_templates()` (line 305)
- `async get_email_templates()` (line 339)
- `async get_email_template()` (line 387)
- `async create_email_template()` (line 420)
- `async update_email_template()` (line 452)
- `async delete_email_template()` (line 500)
- `async preview_email_template()` (line 542)
- `async reset_to_default_templates()` (line 593)
- `async get_template_types()` (line 640)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `UNKNOWN` | `get_email_templates` | 339 |
| `GET` | `/{template_id}` | `get_email_template` | 387 |
| `POST` | `UNKNOWN` | `create_email_template` | 420 |
| `PUT` | `/{template_id}` | `update_email_template` | 452 |
| `DELETE` | `/{template_id}` | `delete_email_template` | 500 |
| `POST` | `/{template_id}/preview` | `preview_email_template` | 542 |
| `POST` | `/reset-defaults` | `reset_to_default_templates` | 593 |
| `GET` | `/types` | `get_template_types` | 640 |

#### Database / Supabase Tables Detected

- `Beta`
- `CarbonTally`
- `an`
- `auth`
- `database`
- `datetime`
- `email`
- `email_templates`
- `fastapi`
- `pydantic`
- `the`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

### 4.70 `backend/routes/admin/extraction.py`

- **Module:** `backend.routes.admin.extraction`
- **Package:** `backend.routes.admin`
- **Lines:** 511
- **Size:** 19,379 bytes
- **Categories:** AI extraction, API, authentication / security, database / repository
- **V3 impact:** **NO CHANGE**

#### Classes

- `ExtractionApprovalRequest` (line 15; bases: `BaseModel`)
  - `Config()` (line 23)
- `ManualReviewNoteRequest` (line 38; bases: `BaseModel`)
  - `Config()` (line 43)
- `BatchApprovalRequest` (line 51; bases: `BaseModel`)
  - `Config()` (line 57)
- `ExtractionApprovalResponse` (line 68; bases: `BaseModel`)

#### Top-Level Functions

- `async calculate_emissions_with_defra()` (line 81)
- `async approve_extraction()` (line 126)
- `async add_manual_review_note()` (line 267)
- `async approve_pdf_batch()` (line 338)
- `async get_pending_reviews()` (line 472)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/approve` | `approve_extraction` | 126 |
| `POST` | `/manual-review-note` | `add_manual_review_note` | 267 |
| `POST` | `/batch/approve` | `approve_pdf_batch` | 338 |
| `GET` | `/reviews/pending` | `get_pending_reviews` | 472 |

#### Database / Supabase Tables Detected

- `asset_name`
- `assets`
- `auth`
- `batch`
- `database`
- `datetime`
- `defra_conversion_factors`
- `emissions_logs`
- `extraction`
- `fastapi`
- `main`
- `manual_review_queue`
- `pydantic`
- `request`
- `review`
- `start_date`
- `the`
- `typing`
- `upload_batches`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `main`
- `pydantic`
- `traceback`
- `typing`

### 4.71 `backend/routes/admin/logs.py`

- **Module:** `backend.routes.admin.logs`
- **Package:** `backend.routes.admin`
- **Lines:** 350
- **Size:** 11,629 bytes
- **Categories:** API, audit / logging, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async get_email_logs()` (line 20)
- `async get_email_log_detail()` (line 63)
- `async get_email_stats()` (line 93)
- `async get_email_logs_by_email()` (line 155)
- `async get_processing_logs()` (line 188)
- `async get_processing_log_detail()` (line 231)
- `async get_processing_logs_by_file()` (line 261)
- `async get_processing_stats()` (line 290)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/email` | `get_email_logs` | 20 |
| `GET` | `/email/{log_id}` | `get_email_log_detail` | 63 |
| `GET` | `/email/stats` | `get_email_stats` | 93 |
| `GET` | `/email/email/{email_address}` | `get_email_logs_by_email` | 155 |
| `GET` | `/processing` | `get_processing_logs` | 188 |
| `GET` | `/processing/{log_id}` | `get_processing_log_detail` | 231 |
| `GET` | `/processing/file/{file_id}` | `get_processing_logs_by_file` | 261 |
| `GET` | `/processing/stats` | `get_processing_stats` | 290 |

#### Database / Supabase Tables Detected

- `auth`
- `database`
- `datetime`
- `email_logs`
- `fastapi`
- `processing_logs`
- `pydantic`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

### 4.72 `backend/routes/admin/permissions.py`

- **Module:** `backend.routes.admin.permissions`
- **Package:** `backend.routes.admin`
- **Lines:** 585
- **Size:** 19,904 bytes
- **Categories:** API, RBAC, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `PermissionBase` (line 20; bases: `BaseModel`)
- `RoleCreate` (line 26; bases: `BaseModel`)
- `RoleUpdate` (line 32; bases: `BaseModel`)
- `RoleResponse` (line 38; bases: `BaseModel`)
- `RoleListResponse` (line 48; bases: `BaseModel`)

#### Top-Level Functions

- `async get_role_by_id()` (line 58)
- `async get_staff_count_for_role()` (line 70)
- `async get_roles()` (line 85)
- `async get_role()` (line 150)
- `async create_role()` (line 188)
- `async update_role()` (line 253)
- `async delete_role()` (line 343)
- `async list_available_permissions()` (line 396)
- `async setup_default_roles()` (line 463)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/roles` | `get_roles` | 85 |
| `GET` | `/roles/{role_id}` | `get_role` | 150 |
| `POST` | `/roles` | `create_role` | 188 |
| `PUT` | `/roles/{role_id}` | `update_role` | 253 |
| `DELETE` | `/roles/{role_id}` | `delete_role` | 343 |
| `GET` | `/permissions/list` | `list_available_permissions` | 396 |
| `POST` | `/setup-defaults` | `setup_default_roles` | 463 |

#### Database / Supabase Tables Detected

- `a`
- `auth`
- `database`
- `datetime`
- `dict`
- `documents`
- `fastapi`
- `pydantic`
- `role`
- `roles`
- `staff_profiles`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `traceback`
- `typing`

### 4.73 `backend/routes/admin/review_history.py`

- **Module:** `backend.routes.admin.review_history`
- **Package:** `backend.routes.admin`
- **Lines:** 212
- **Size:** 7,405 bytes
- **Categories:** API, CSV / Excel, authentication / security, database / repository, validation / QA
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `async get_review_history()` (line 15)
- `async get_all_review_history()` (line 44)
- `async get_staff_assignment_history()` (line 85)
- `async get_review_audit_trail()` (line 114)
- `async export_review_audit_trail()` (line 146)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/{review_id}/history` | `get_review_history` | 15 |
| `GET` | `/history` | `get_all_review_history` | 44 |
| `GET` | `/history/staff/{staff_id}` | `get_staff_assignment_history` | 85 |
| `GET` | `/history/audit` | `get_review_audit_trail` | 114 |
| `GET` | `/history/audit/export` | `export_review_audit_trail` | 146 |

#### Database / Supabase Tables Detected

- `auth`
- `database`
- `datetime`
- `fastapi`
- `review_assignment_history`
- `review_audit_trail`
- `typing`

#### Imports

- `auth`
- `csv`
- `database`
- `datetime`
- `fastapi`
- `fastapi.responses`
- `io`
- `json`
- `typing`

### 4.74 `backend/routes/admin/reviews.py`

- **Module:** `backend.routes.admin.reviews`
- **Package:** `backend.routes.admin`
- **Lines:** 1300
- **Size:** 48,641 bytes
- **Categories:** API, authentication / security, database / repository, validation / QA
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `AssignRequest` (line 17; bases: `BaseModel`)
- `CompleteRequest` (line 21; bases: `BaseModel`)
- `QueueFilterParams` (line 25; bases: `BaseModel`)

#### Top-Level Functions

- `async update_staff_workload()` (line 38)
- `async get_staff_workload()` (line 61)
- `async get_review_queue()` (line 87)
- `async get_review_details()` (line 254)
- `async assign_review()` (line 367)
- `async start_review()` (line 498)
- `async complete_review()` (line 610)
- `async reject_review()` (line 751)
- `async get_my_review_queue()` (line 835)
- `async get_staff_queue_stats()` (line 971)
- `async get_priority_queue()` (line 1024)
- `async reorder_queue()` (line 1053)
- `async get_detailed_queue_stats()` (line 1117)
- `async escalate_review()` (line 1195)
- `async get_sla_monitor()` (line 1244)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/queue` | `get_review_queue` | 87 |
| `GET` | `/{review_id}` | `get_review_details` | 254 |
| `POST` | `/{review_id}/assign` | `assign_review` | 367 |
| `POST` | `/my-queue/{review_id}/start` | `start_review` | 498 |
| `POST` | `/{review_id}/complete` | `complete_review` | 610 |
| `POST` | `/{review_id}/reject` | `reject_review` | 751 |
| `GET` | `/my-queue` | `get_my_review_queue` | 835 |
| `GET` | `/queue/priority` | `get_priority_queue` | 1024 |
| `POST` | `/queue/reorder` | `reorder_queue` | 1053 |
| `GET` | `/queue/stats/detailed` | `get_detailed_queue_stats` | 1117 |
| `POST` | `/queue/escalate` | `escalate_review` | 1195 |
| `GET` | `/queue/sla-monitor` | `get_sla_monitor` | 1244 |

#### Database / Supabase Tables Detected

- `auth`
- `database`
- `datetime`
- `document`
- `document_activity_log`
- `escalation`
- `fastapi`
- `manual_review_queue`
- `or`
- `organization_files`
- `priority`
- `pydantic`
- `request`
- `review`
- `review_assignment_history`
- `staff`
- `staff_profiles`
- `staff_workload`
- `typing`
- `upload_batches`
- `utils`

#### Imports

- `.workload`
- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `traceback`
- `typing`
- `utils`

### 4.75 `backend/routes/admin/settings.py`

- **Module:** `backend.routes.admin.settings`
- **Package:** `backend.routes.admin`
- **Lines:** 167
- **Size:** 5,785 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `SettingsUpdate` (line 20; bases: `BaseModel`)
- `SettingsReset` (line 31; bases: `BaseModel`)

#### Top-Level Functions

- `async get_settings_history()` (line 39)
- `async validate_settings()` (line 70)
- `async reset_settings()` (line 120)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/settings-history` | `get_settings_history` | 39 |
| `POST` | `/validate` | `validate_settings` | 70 |
| `POST` | `/reset` | `reset_settings` | 120 |

#### Database / Supabase Tables Detected

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `settings`
- `system_settings`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

### 4.76 `backend/routes/admin/staff.py`

- **Module:** `backend.routes.admin.staff`
- **Package:** `backend.routes.admin`
- **Lines:** 1879
- **Size:** 73,308 bytes
- **Categories:** AI extraction, API, CSV / Excel, Storage, authentication / security, database / repository
- **V3 impact:** **NO CHANGE**

#### Classes

- `StaffCreate` (line 20; bases: `BaseModel`)
  - `Config()` (line 27)
- `StaffUpdate` (line 37; bases: `BaseModel`)
  - `Config()` (line 45)
- `StaffResponse` (line 54; bases: `BaseModel`)
  - `Config()` (line 75)
- `StaffListResponse` (line 99; bases: `BaseModel`)
- `StaffPerformanceDashboardResponse` (line 1368; bases: `BaseModel`)
- `StaffPerformanceMetrics` (line 1379; bases: `BaseModel`)

#### Top-Level Functions

- `validate_staff_role()` (line 109)
- `async get_user_from_auth()` (line 114)
- `async create_auth_user()` (line 136)
- `async get_all_staff()` (line 174)
- `async get_staff_performance()` (line 299)
- `async get_my_staff_profile()` (line 417)
- `async get_staff_activity()` (line 496)
- `async export_staff_performance()` (line 604)
- `async get_staff_member()` (line 712)
- `async create_staff_member()` (line 799)
- `async update_staff_member()` (line 903)
- `async delete_staff_member()` (line 1003)
- `async update_staff_role()` (line 1082)
- `async get_staff_activity_log()` (line 1173)
- `async get_staff_performance_history()` (line 1241)
- `async reset_staff_password()` (line 1321)
- `async get_staff_performance_dashboard()` (line 1401)
- `async export_staff_performance()` (line 1729)
- `async compare_staff_performance()` (line 1782)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `UNKNOWN` | `get_all_staff` | 174 |
| `GET` | `/performance` | `get_staff_performance` | 299 |
| `GET` | `/me` | `get_my_staff_profile` | 417 |
| `GET` | `/activity` | `get_staff_activity` | 496 |
| `GET` | `/performance/export` | `export_staff_performance` | 604 |
| `GET` | `/{staff_id}` | `get_staff_member` | 712 |
| `POST` | `/` | `create_staff_member` | 799 |
| `PUT` | `/{staff_id}` | `update_staff_member` | 903 |
| `DELETE` | `/{staff_id}` | `delete_staff_member` | 1003 |
| `PUT` | `/{staff_id}/role` | `update_staff_role` | 1082 |
| `GET` | `/{staff_id}/activity-log` | `get_staff_activity_log` | 1173 |
| `GET` | `/{staff_id}/performance-history` | `get_staff_performance_history` | 1241 |
| `POST` | `/{staff_id}/reset-password` | `reset_staff_password` | 1321 |
| `GET` | `/performance/dashboard` | `get_staff_performance_dashboard` | 1401 |
| `GET` | `/performance/export` | `export_staff_performance` | 1729 |
| `GET` | `/performance/compare` | `compare_staff_performance` | 1782 |

#### Database / Supabase Tables Detected

- `a`
- `auth`
- `database`
- `datetime`
- `fastapi`
- `manual_review_queue`
- `pydantic`
- `review_assignment_history`
- `reviews_completed`
- `roles`
- `seconds`
- `staff`
- `staff_profiles`
- `staff_result`
- `staff_workload`
- `supabase`
- `typing`
- `utils`

#### Imports

- `auth`
- `csv`
- `database`
- `datetime`
- `fastapi`
- `fastapi.responses`
- `io`
- `os`
- `pydantic`
- `secrets`
- `string`
- `supabase`
- `traceback`
- `typing`
- `utils.email`

### 4.77 `backend/routes/admin/workload.py`

- **Module:** `backend.routes.admin.workload`
- **Package:** `backend.routes.admin`
- **Lines:** 896
- **Size:** 36,208 bytes
- **Categories:** API, Storage, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `WorkloadSettingsUpdate` (line 20; bases: `BaseModel`)
- `ReassignRequest` (line 27; bases: `BaseModel`)
- `WorkloadForecastResponse` (line 327; bases: `BaseModel`)
- `StaffWorkloadForecast` (line 338; bases: `BaseModel`)

#### Top-Level Functions

- `async get_staff_workload_endpoint()` (line 37)
- `async get_staff_workload_detail()` (line 61)
- `async get_queue_settings()` (line 100)
- `async update_queue_settings()` (line 133)
- `async get_queue_stats()` (line 178)
- `async reassign_review()` (line 233)
- `async get_workload_forecast()` (line 357)
- `async get_workload_forecast_summary()` (line 705)
- `async export_workload_forecast()` (line 761)
- `async get_workload_scenarios()` (line 831)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/staff/workload` | `get_staff_workload_endpoint` | 37 |
| `GET` | `/staff/workload/{staff_id}` | `get_staff_workload_detail` | 61 |
| `GET` | `/queue/settings` | `get_queue_settings` | 100 |
| `PUT` | `/queue/settings` | `update_queue_settings` | 133 |
| `GET` | `/queue/stats` | `get_queue_stats` | 178 |
| `POST` | `/queue/reassign` | `reassign_review` | 233 |
| `GET` | `/forecast` | `get_workload_forecast` | 357 |
| `GET` | `/forecast/summary` | `get_workload_forecast_summary` | 705 |
| `GET` | `/forecast/export` | `export_workload_forecast` | 761 |
| `GET` | `/forecast/scenarios` | `get_workload_scenarios` | 831 |

#### Database / Supabase Tables Detected

- `auth`
- `collections`
- `customer_documents`
- `database`
- `datetime`
- `fastapi`
- `manual_review_queue`
- `pydantic`
- `queue`
- `queue_settings`
- `review`
- `review_assignment_history`
- `staff_profiles`
- `staff_workload`
- `supabase`
- `typing`
- `utils`

#### Imports

- `auth`
- `collections`
- `database`
- `datetime`
- `fastapi`
- `numpy`
- `pydantic`
- `supabase`
- `traceback`
- `typing`
- `utils`

### 4.78 `backend/routes/communication.py`

- **Module:** `backend.routes.communication`
- **Package:** `backend.routes`
- **Lines:** 2326
- **Size:** 87,792 bytes
- **Categories:** API, Realtime / communication, Storage, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `MessageCreate` (line 20; bases: `BaseModel`)
  - `validate_content()` (line 30)
- `ConversationCreate` (line 38; bases: `BaseModel`)
  - `validate_participants()` (line 49)
- `MessageUpdateReadRequest` (line 57; bases: `BaseModel`)
- `MessageResponse` (line 62; bases: `BaseModel`)
- `ConversationResponse` (line 82; bases: `BaseModel`)
- `NotificationResponse` (line 101; bases: `BaseModel`)
- `MessagesListResponse` (line 116; bases: `BaseModel`)
- `DeleteMessageResponse` (line 125; bases: `BaseModel`)
- `MarkAllReadResponse` (line 132; bases: `BaseModel`)
- `AttachmentCreate` (line 1470; bases: `BaseModel`)
- `AttachmentResponse` (line 1479; bases: `BaseModel`)
- `ParticipantCreate` (line 1493; bases: `BaseModel`)
- `ParticipantRemove` (line 1498; bases: `BaseModel`)
- `ParticipantResponse` (line 1503; bases: `BaseModel`)
- `MessageSearchResponse` (line 1512; bases: `BaseModel`)
- `ReplyCreate` (line 1521; bases: `BaseModel`)
  - `validate_content()` (line 1528)

#### Top-Level Functions

- `async send_message()` (line 144)
- `async get_messages()` (line 318)
- `async get_message_detail()` (line 441)
- `async mark_message_read()` (line 531)
- `async delete_message()` (line 598)
- `async get_conversations()` (line 666)
- `async get_conversation()` (line 830)
- `async start_conversation()` (line 987)
- `async close_conversation()` (line 1097)
- `async archive_conversation()` (line 1175)
- `async get_notifications()` (line 1254)
- `async get_unread_notification_count()` (line 1306)
- `async mark_notification_read()` (line 1334)
- `async mark_all_notifications_read()` (line 1401)
- `async get_unread_message_count()` (line 1441)
- `async add_message_attachment()` (line 1541)
- `async get_message_attachments()` (line 1650)
- `async get_conversation_participants()` (line 1727)
- `async update_conversation_participants()` (line 1823)
- `async search_messages()` (line 1959)
- `async get_message_replies()` (line 2095)
- `async reply_to_message()` (line 2198)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/messages` | `send_message` | 144 |
| `GET` | `/messages` | `get_messages` | 318 |
| `GET` | `/messages/{message_id}` | `get_message_detail` | 441 |
| `PUT` | `/messages/{message_id}/read` | `mark_message_read` | 531 |
| `DELETE` | `/messages/{message_id}` | `delete_message` | 598 |
| `GET` | `/conversations` | `get_conversations` | 666 |
| `GET` | `/conversations/{conversation_id}` | `get_conversation` | 830 |
| `POST` | `/conversations` | `start_conversation` | 987 |
| `PUT` | `/conversations/{conversation_id}/close` | `close_conversation` | 1097 |
| `PUT` | `/conversations/{conversation_id}/archive` | `archive_conversation` | 1175 |
| `GET` | `/notifications` | `get_notifications` | 1254 |
| `GET` | `/notifications/unread` | `get_unread_notification_count` | 1306 |
| `PUT` | `/notifications/{notification_id}/read` | `mark_notification_read` | 1334 |
| `PUT` | `/notifications/mark-all-read` | `mark_all_notifications_read` | 1401 |
| `GET` | `/unread/messages` | `get_unread_message_count` | 1441 |
| `POST` | `/messages/{message_id}/attachments` | `add_message_attachment` | 1541 |
| `GET` | `/messages/{message_id}/attachments` | `get_message_attachments` | 1650 |
| `GET` | `/conversations/{conversation_id}/participants` | `get_conversation_participants` | 1727 |
| `PUT` | `/conversations/{conversation_id}/participants` | `update_conversation_participants` | 1823 |
| `GET` | `/messages/search` | `search_messages` | 1959 |
| `GET` | `/messages/{message_id}/replies` | `get_message_replies` | 2095 |
| `POST` | `/messages/{message_id}/reply` | `reply_to_message` | 2198 |

#### Database / Supabase Tables Detected

- `a`
- `all`
- `auth`
- `conversation`
- `conversations`
- `database`
- `datetime`
- `fastapi`
- `message`
- `messages`
- `notification`
- `notifications`
- `organization_members`
- `participants`
- `pydantic`
- `staff_profiles`
- `supabase`
- `times`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `supabase`
- `traceback`
- `typing`
- `uuid`

### 4.79 `backend/routes/customer_dashboard.py`

- **Module:** `backend.routes.customer_dashboard`
- **Package:** `backend.routes`
- **Lines:** 1239
- **Size:** 46,524 bytes
- **Categories:** API, Storage, authentication / security, database / repository, reporting
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `DashboardStatsResponse` (line 19; bases: `BaseModel`)
- `DocumentStatusOverviewResponse` (line 31; bases: `BaseModel`)
- `AssetPerformanceResponse` (line 39; bases: `BaseModel`)
- `EmissionsOverviewResponse` (line 51; bases: `BaseModel`)
- `PendingActionResponse` (line 60; bases: `BaseModel`)
- `ActivityResponse` (line 67; bases: `BaseModel`)
- `NotificationResponse` (line 79; bases: `BaseModel`)
- `DashboardTrendsResponse` (line 679; bases: `BaseModel`)
- `DashboardAlertResponse` (line 689; bases: `BaseModel`)

#### Top-Level Functions

- `async get_dashboard_stats()` (line 95)
- `async get_document_status_overview()` (line 183)
- `async get_asset_performance()` (line 255)
- `async get_emissions_overview()` (line 340)
- `async get_pending_actions()` (line 460)
- `async get_recent_activity()` (line 578)
- `async get_notifications()` (line 640)
- `async get_dashboard_trends()` (line 708)
- `async get_dashboard_alerts()` (line 895)
- `aggregate_by_interval()` (line 1008)
- `get_interval_delta()` (line 1064)
- `calculate_growth_rate()` (line 1076)
- `async get_alert_summary()` (line 1105)
- `async dismiss_alert()` (line 1154)
- `async clear_all_alerts()` (line 1202)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/stats` | `get_dashboard_stats` | 95 |
| `GET` | `/documents` | `get_document_status_overview` | 183 |
| `GET` | `/assets` | `get_asset_performance` | 255 |
| `GET` | `/emissions` | `get_emissions_overview` | 340 |
| `GET` | `/pending` | `get_pending_actions` | 460 |
| `GET` | `/activity` | `get_recent_activity` | 578 |
| `GET` | `/notifications` | `get_notifications` | 640 |
| `GET` | `/trends` | `get_dashboard_trends` | 708 |
| `GET` | `/alerts` | `get_dashboard_alerts` | 895 |
| `GET` | `/alerts/summary` | `get_alert_summary` | 1105 |
| `PUT` | `/alerts/{alert_id}/dismiss` | `dismiss_alert` | 1154 |
| `DELETE` | `/alerts/clear-all` | `clear_all_alerts` | 1202 |

#### Database / Supabase Tables Detected

- `assets`
- `audit`
- `audit_logs`
- `auth`
- `customer_documents`
- `customer_verifications`
- `database`
- `datetime`
- `emissions_logs`
- `fastapi`
- `manual_review_queue`
- `notifications`
- `organization_members`
- `priority`
- `pydantic`
- `supabase`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `supabase`
- `traceback`
- `typing`

### 4.80 `backend/routes/customer_documents.py`

- **Module:** `backend.routes.customer_documents`
- **Package:** `backend.routes`
- **Lines:** 2109
- **Size:** 82,636 bytes
- **Categories:** API, Storage, authentication / security, database / repository, document processing
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `DocumentStatsResponse` (line 21; bases: `BaseModel`)
- `PendingDocumentResponse` (line 32; bases: `BaseModel`)
- `AssetDocumentsResponse` (line 49; bases: `BaseModel`)
- `ExtractionDataResponse` (line 55; bases: `BaseModel`)
- `VerificationRequest` (line 67; bases: `BaseModel`)
  - `validate_status()` (line 74)
- `ReviewRequestResponse` (line 79; bases: `BaseModel`)
- `ManualReviewRequest` (line 85; bases: `BaseModel`)
- `DocumentHistoryResponse` (line 1174; bases: `BaseModel`)
- `DocumentNoteCreate` (line 1190; bases: `BaseModel`)
  - `validate_content()` (line 1197)
- `DocumentNoteResponse` (line 1205; bases: `BaseModel`)
- `DocumentVersionResponse` (line 1218; bases: `BaseModel`)
- `DocumentVersionCreate` (line 1232; bases: `BaseModel`)
- `DetailedStatsResponse` (line 1240; bases: `BaseModel`)

#### Top-Level Functions

- `async get_document_statistics()` (line 95)
- `async get_pending_documents()` (line 191)
- `async get_customer_documents()` (line 273)
- `async get_documents_for_asset()` (line 433)
- `async get_customer_document()` (line 527)
- `async get_extraction_details()` (line 651)
- `async verify_document()` (line 744)
- `async request_staff_review()` (line 850)
- `async organize_document_for_customer()` (line 1006)
- `async create_extraction_task()` (line 1122)
- `async download_document()` (line 1255)
- `async get_document_history()` (line 1335)
- `async get_document_notes()` (line 1441)
- `async add_document_note()` (line 1548)
- `async get_document_versions()` (line 1669)
- `async create_document_version()` (line 1769)
- `async get_detailed_document_stats()` (line 1909)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/stats/{org_id}` | `get_document_statistics` | 95 |
| `GET` | `/pending/{org_id}` | `get_pending_documents` | 191 |
| `GET` | `/documents/{org_id}` | `get_customer_documents` | 273 |
| `GET` | `/assets/{asset_id}` | `get_documents_for_asset` | 433 |
| `GET` | `/{document_id}` | `get_customer_document` | 527 |
| `GET` | `/{document_id}/extraction` | `get_extraction_details` | 651 |
| `POST` | `/{document_id}/verify` | `verify_document` | 744 |
| `POST` | `/{document_id}/request-review` | `request_staff_review` | 850 |
| `POST` | `/staff/organize/{document_id}` | `organize_document_for_customer` | 1006 |
| `GET` | `/{document_id}/download` | `download_document` | 1255 |
| `GET` | `/{document_id}/history` | `get_document_history` | 1335 |
| `GET` | `/{document_id}/notes` | `get_document_notes` | 1441 |
| `POST` | `/{document_id}/notes` | `add_document_note` | 1548 |
| `GET` | `/{document_id}/versions` | `get_document_versions` | 1669 |
| `POST` | `/{document_id}/versions` | `create_document_version` | 1769 |
| `GET` | `/stats/detailed` | `get_detailed_document_stats` | 1909 |

#### Database / Supabase Tables Detected

- `assets`
- `audit_logs`
- `auth`
- `customer_document`
- `customer_documents`
- `database`
- `datetime`
- `document`
- `document_types`
- `enum`
- `fastapi`
- `manual_review_queue`
- `metadata`
- `organization_members`
- `pydantic`
- `staff_profiles`
- `supabase`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `enum`
- `fastapi`
- `pydantic`
- `supabase`
- `traceback`
- `typing`
- `uuid`

### 4.81 `backend/routes/customer_verifications.py`

- **Module:** `backend.routes.customer_verifications`
- **Package:** `backend.routes`
- **Lines:** 1928
- **Size:** 76,525 bytes
- **Categories:** API, Storage, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `VerificationStatus` (line 20; bases: `str`)
- `VerificationCreate` (line 31; bases: `BaseModel`)
- `VerificationUpdateRequest` (line 38; bases: `BaseModel`)
- `VerificationResponse` (line 45; bases: `BaseModel`)
- `VerificationsListResponse` (line 79; bases: `BaseModel`)
- `VerificationActionResponse` (line 88; bases: `BaseModel`)
- `VerificationHistoryResponse` (line 1048; bases: `BaseModel`)
- `BulkVerificationCreate` (line 1063; bases: `BaseModel`)
- `BulkVerificationAction` (line 1070; bases: `BaseModel`)
- `BulkVerificationResponse` (line 1077; bases: `BaseModel`)
- `VerificationTimelineResponse` (line 1087; bases: `BaseModel`)
- `DetailedVerificationStatsResponse` (line 1098; bases: `BaseModel`)

#### Top-Level Functions

- `async list_verifications()` (line 103)
- `async get_verification_detail()` (line 297)
- `async submit_verification()` (line 428)
- `async approve_verification()` (line 554)
- `async reject_verification()` (line 686)
- `async request_revision()` (line 817)
- `async get_verification_statuses()` (line 958)
- `async get_verification_stats()` (line 976)
- `async get_verification_history()` (line 1114)
- `async bulk_submit_verifications()` (line 1342)
- `async bulk_approve_verifications()` (line 1472)
- `async get_verification_timeline()` (line 1588)
- `async get_detailed_verification_stats()` (line 1677)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/` | `list_verifications` | 103 |
| `GET` | `/{verification_id}` | `get_verification_detail` | 297 |
| `POST` | `/` | `submit_verification` | 428 |
| `PUT` | `/{verification_id}/approve` | `approve_verification` | 554 |
| `PUT` | `/{verification_id}/reject` | `reject_verification` | 686 |
| `PUT` | `/{verification_id}/revision` | `request_revision` | 817 |
| `GET` | `/statuses` | `get_verification_statuses` | 958 |
| `GET` | `/stats` | `get_verification_stats` | 976 |
| `GET` | `/{verification_id}/history` | `get_verification_history` | 1114 |
| `POST` | `/bulk` | `bulk_submit_verifications` | 1342 |
| `POST` | `/bulk/approve` | `bulk_approve_verifications` | 1472 |
| `GET` | `/timeline` | `get_verification_timeline` | 1588 |
| `GET` | `/stats/detailed` | `get_detailed_verification_stats` | 1677 |

#### Database / Supabase Tables Detected

- `action_details`
- `audit_logs`
- `auth`
- `customer_documents`
- `customer_verifications`
- `database`
- `datetime`
- `document`
- `fastapi`
- `organization_members`
- `organizations`
- `pydantic`
- `supabase`
- `typing`
- `verification`
- `verification_activity_log`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `supabase`
- `traceback`
- `typing`
- `uuid`

### 4.82 `backend/routes/document_activity.py`

- **Module:** `backend.routes.document_activity`
- **Package:** `backend.routes`
- **Lines:** 338
- **Size:** 11,794 bytes
- **Categories:** API, CSV / Excel, authentication / security, database / repository, document processing
- **V3 impact:** **NO CHANGE**

#### Classes

- `CustomerReviewResponse` (line 21; bases: `BaseModel`)

#### Top-Level Functions

- `async get_document_activity()` (line 30)
- `async export_document_activity()` (line 90)
- `async get_document_reviews()` (line 153)
- `async respond_to_review()` (line 198)
- `async get_organization_document_activity()` (line 280)
- `async get_customer_reviews_admin()` (line 309)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/{file_id}/activity` | `get_document_activity` | 30 |
| `GET` | `/{file_id}/activity/export` | `export_document_activity` | 90 |
| `GET` | `/{file_id}/reviews` | `get_document_reviews` | 153 |
| `POST` | `/{file_id}/review/response` | `respond_to_review` | 198 |
| `GET` | `/organizations/{org_id}/documents/activity` | `get_organization_document_activity` | 280 |
| `GET` | `/admin/reviews/customer` | `get_customer_reviews_admin` | 309 |

#### Database / Supabase Tables Detected

- `auth`
- `customer_review_log`
- `database`
- `datetime`
- `document`
- `document_activity_log`
- `fastapi`
- `organization_files`
- `organization_members`
- `pydantic`
- `typing`

#### Imports

- `auth`
- `csv`
- `database`
- `datetime`
- `fastapi`
- `fastapi.responses`
- `io`
- `json`
- `pydantic`
- `typing`

### 4.83 `backend/routes/documents/__init__.py`

- **Module:** `backend.routes.documents`
- **Package:** `backend.routes`
- **Lines:** 13
- **Size:** 259 bytes
- **Categories:** API, document processing
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.`

### 4.84 `backend/routes/documents_main.py`

- **Module:** `backend.routes.documents_main`
- **Package:** `backend.routes`
- **Lines:** 780
- **Size:** 31,047 bytes
- **Categories:** AI extraction, API, authentication / security, database / repository, document processing
- **V3 impact:** **NO CHANGE**

#### Classes

- `CustomerReviewRequest` (line 16; bases: `BaseModel`)
- `DocumentStatusUpdateRequest` (line 21; bases: `BaseModel`)

#### Top-Level Functions

- `async get_document_stats()` (line 31)
- `async get_documents()` (line 101)
- `async get_document_status()` (line 300)
- `async customer_review_document()` (line 389)
- `async update_document_status()` (line 599)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/stats/{org_id}` | `get_document_stats` | 31 |
| `GET` | `/{org_id}` | `get_documents` | 101 |
| `GET` | `/{org_id}/{file_id}/status` | `get_document_status` | 300 |
| `POST` | `/{org_id}/{file_id}/review` | `customer_review_document` | 389 |
| `POST` | `/{org_id}/admin/{file_id}/status` | `update_document_status` | 599 |

#### Database / Supabase Tables Detected

- `assets`
- `auth`
- `customer_documents`
- `customer_review_log`
- `data`
- `database`
- `datetime`
- `defra_conversion_factors`
- `document`
- `document_activity_log`
- `emissions_logs`
- `fastapi`
- `manual_review_queue`
- `metadata`
- `organization_files`
- `organization_members`
- `pydantic`
- `the`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `traceback`
- `typing`

### 4.85 `backend/routes/drafts.py`

- **Module:** `backend.routes.drafts`
- **Package:** `backend.routes`
- **Lines:** 474
- **Size:** 16,023 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `DraftSaveRequest` (line 15; bases: `BaseModel`)
- `DraftResponse` (line 21; bases: `BaseModel`)
- `DraftListResponse` (line 32; bases: `BaseModel`)

#### Top-Level Functions

- `async save_draft()` (line 42)
- `async get_drafts()` (line 127)
- `async get_draft()` (line 218)
- `async delete_draft()` (line 288)
- `async submit_draft()` (line 341)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/save` | `save_draft` | 42 |
| `GET` | `/` | `get_drafts` | 127 |
| `GET` | `/{draft_id}` | `get_draft` | 218 |
| `DELETE` | `/{draft_id}` | `delete_draft` | 288 |
| `POST` | `/{draft_id}/submit` | `submit_draft` | 341 |

#### Database / Supabase Tables Detected

- `a`
- `assets`
- `auth`
- `database`
- `datetime`
- `defra_conversion_factors`
- `document`
- `draft_entries`
- `emissions_logs`
- `existing`
- `fastapi`
- `organization_files`
- `pydantic`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `traceback`
- `typing`

### 4.86 `backend/routes/drafts_enhanced.py`

- **Module:** `backend.routes.drafts_enhanced`
- **Package:** `backend.routes`
- **Lines:** 410
- **Size:** 14,085 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `SectionUpdate` (line 19; bases: `BaseModel`)
- `SectionProgress` (line 24; bases: `BaseModel`)

#### Top-Level Functions

- `async get_draft_sections()` (line 34)
- `async update_draft_section()` (line 109)
- `async delete_draft_section()` (line 185)
- `async get_draft_progress()` (line 252)
- `async validate_draft()` (line 295)
- `async publish_draft()` (line 354)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/{draft_id}/sections` | `get_draft_sections` | 34 |
| `POST` | `/{draft_id}/sections/{section_id}` | `update_draft_section` | 109 |
| `DELETE` | `/{draft_id}/sections/{section_id}` | `delete_draft_section` | 185 |
| `GET` | `/{draft_id}/progress` | `get_draft_progress` | 252 |
| `POST` | `/{draft_id}/validate` | `validate_draft` | 295 |
| `POST` | `/{draft_id}/publish` | `publish_draft` | 354 |

#### Database / Supabase Tables Detected

- `a`
- `auth`
- `database`
- `datetime`
- `draft`
- `draft_entries`
- `fastapi`
- `organization_members`
- `progress`
- `pydantic`
- `section`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

### 4.87 `backend/routes/emissions.py`

- **Module:** `backend.routes.emissions`
- **Package:** `backend.routes`
- **Lines:** 1509
- **Size:** 56,853 bytes
- **Categories:** API, CSV / Excel, Storage, authentication / security, calculation, database / repository
- **V3 impact:** **NO CHANGE**

#### Classes

- `EmissionCreate` (line 15; bases: `BaseModel`)
- `EmissionUpdate` (line 323; bases: `BaseModel`)
- `BulkEmissionCreate` (line 330; bases: `BaseModel`)
- `EmissionsByDocumentTypeResponse` (line 688; bases: `BaseModel`)
- `VerificationHistoryResponse` (line 698; bases: `BaseModel`)
- `BulkEmissionsAction` (line 714; bases: `BaseModel`)
- `BulkEmissionsResponse` (line 721; bases: `BaseModel`)

#### Top-Level Functions

- `async create_emission_record()` (line 30)
- `async get_emissions_for_organization()` (line 104)
- `async delete_emission_record()` (line 269)
- `async update_emission_record()` (line 334)
- `async bulk_create_emissions()` (line 395)
- `async get_emission_stats()` (line 476)
- `async export_emissions()` (line 537)
- `async verify_emissions()` (line 619)
- `async get_emissions_by_document_type()` (line 736)
- `async get_emissions_verification_history()` (line 844)
- `async bulk_approve_emissions()` (line 977)
- `async bulk_reject_emissions()` (line 1113)
- `async get_emissions_summary()` (line 1253)
- `async get_emissions_by_asset()` (line 1353)
- `async get_pending_emissions_verifications()` (line 1439)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/emissions` | `create_emission_record` | 30 |
| `GET` | `/{org_id}/emissions` | `get_emissions_for_organization` | 104 |
| `DELETE` | `/emissions/{record_id}` | `delete_emission_record` | 269 |
| `PUT` | `/emissions/{record_id}` | `update_emission_record` | 334 |
| `POST` | `/emissions/bulk` | `bulk_create_emissions` | 395 |
| `GET` | `/emissions/stats` | `get_emission_stats` | 476 |
| `GET` | `/emissions/export` | `export_emissions` | 537 |
| `POST` | `/emissions/verify` | `verify_emissions` | 619 |
| `GET` | `/by-document-type` | `get_emissions_by_document_type` | 736 |
| `GET` | `/{record_id}/verification-history` | `get_emissions_verification_history` | 844 |
| `POST` | `/bulk/approve` | `bulk_approve_emissions` | 977 |
| `POST` | `/bulk/reject` | `bulk_reject_emissions` | 1113 |
| `GET` | `/stats/summary` | `get_emissions_summary` | 1253 |
| `GET` | `/by-asset` | `get_emissions_by_asset` | 1353 |
| `GET` | `/verification-pending` | `get_pending_emissions_verifications` | 1439 |

#### Database / Supabase Tables Detected

- `Endpoints`
- `an`
- `audit_logs`
- `auth`
- `customer_documents`
- `database`
- `datetime`
- `emission`
- `emissions_logs`
- `fastapi`
- `organization_members`
- `pydantic`
- `record`
- `supabase`
- `this`
- `typing`
- `verification_activity_log`

#### Imports

- `auth`
- `csv`
- `database`
- `datetime`
- `fastapi`
- `fastapi.responses`
- `io`
- `pydantic`
- `supabase`
- `traceback`
- `typing`

### 4.88 `backend/routes/feedback.py`

- **Module:** `backend.routes.feedback`
- **Package:** `backend.routes`
- **Lines:** 289
- **Size:** 9,661 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `FeedbackCreate` (line 19; bases: `BaseModel`)
- `FeedbackUpdate` (line 31; bases: `BaseModel`)

#### Top-Level Functions

- `async submit_feedback()` (line 42)
- `async get_user_feedback()` (line 87)
- `async get_feedback_detail()` (line 125)
- `async update_feedback_status()` (line 162)
- `async get_pending_feedback()` (line 209)
- `async get_feedback_stats()` (line 239)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `UNKNOWN` | `submit_feedback` | 42 |
| `GET` | `UNKNOWN` | `get_user_feedback` | 87 |
| `GET` | `/{feedback_id}` | `get_feedback_detail` | 125 |
| `PUT` | `/{feedback_id}` | `update_feedback_status` | 162 |
| `GET` | `/admin/feedback/pending` | `get_pending_feedback` | 209 |
| `GET` | `/admin/feedback/stats` | `get_feedback_stats` | 239 |

#### Database / Supabase Tables Detected

- `auth`
- `database`
- `datetime`
- `fastapi`
- `feedback`
- `pydantic`
- `typing`
- `user_feedback`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

### 4.89 `backend/routes/glossary.py`

- **Module:** `backend.routes.glossary`
- **Package:** `backend.routes`
- **Lines:** 606
- **Size:** 20,786 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `GlossaryTermCreate` (line 21; bases: `BaseModel`)
  - `Config()` (line 29)
- `GlossaryTermUpdate` (line 40; bases: `BaseModel`)
  - `Config()` (line 48)
- `GlossaryTermResponse` (line 56; bases: `BaseModel`)
  - `Config()` (line 68)
- `GlossaryListResponse` (line 83; bases: `BaseModel`)

#### Top-Level Functions

- `async get_available_categories()` (line 94)
- `async get_glossary()` (line 113)
- `async get_glossary_categories()` (line 192)
- `async search_glossary()` (line 215)
- `async get_glossary_term()` (line 260)
- `async create_glossary_term()` (line 308)
- `async update_glossary_term()` (line 397)
- `async delete_glossary_term()` (line 493)
- `async restore_glossary_term()` (line 558)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/` | `get_glossary` | 113 |
| `GET` | `/categories` | `get_glossary_categories` | 192 |
| `GET` | `/search` | `search_glossary` | 215 |
| `GET` | `/{term_id}` | `get_glossary_term` | 260 |
| `POST` | `/` | `create_glossary_term` | 308 |
| `PUT` | `/{term_id}` | `update_glossary_term` | 397 |
| `DELETE` | `/{term_id}` | `delete_glossary_term` | 493 |
| `POST` | `/{term_id}/restore` | `restore_glossary_term` | 558 |

#### Database / Supabase Tables Detected

- `a`
- `auth`
- `database`
- `datetime`
- `dict`
- `fastapi`
- `glossary`
- `pydantic`
- `term`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `traceback`
- `typing`

### 4.90 `backend/routes/logs.py`

- **Module:** `backend.routes.logs`
- **Package:** `backend.routes`
- **Lines:** 388
- **Size:** 12,814 bytes
- **Categories:** API, audit / logging, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `LogEntry` (line 15; bases: `BaseModel`)

#### Top-Level Functions

- `async create_log()` (line 27)
- `async get_logs()` (line 84)
- `async get_document_logs()` (line 165)
- `async get_log_stats()` (line 201)
- `async get_error_logs()` (line 279)
- `async get_user_activity()` (line 312)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/` | `create_log` | 27 |
| `GET` | `/` | `get_logs` | 84 |
| `GET` | `/documents/{file_id}` | `get_document_logs` | 165 |
| `GET` | `/analytics/stats` | `get_log_stats` | 201 |
| `GET` | `/analytics/errors` | `get_error_logs` | 279 |
| `GET` | `/analytics/users` | `get_user_activity` | 312 |

#### Database / Supabase Tables Detected

- `activity_logs`
- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `request`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `traceback`
- `typing`

### 4.91 `backend/routes/notifications.py`

- **Module:** `backend.routes.notifications`
- **Package:** `backend.routes`
- **Lines:** 565
- **Size:** 23,295 bytes
- **Categories:** API, Realtime / communication, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `CustomerManualExtractionRequest` (line 17; bases: `BaseModel`)
  - `Config()` (line 24)
- `BatchCompletionRequest` (line 33; bases: `BaseModel`)
  - `Config()` (line 39)
- `StaffNotificationRequest` (line 47; bases: `BaseModel`)
  - `Config()` (line 54)
- `NotificationResponse` (line 63; bases: `BaseModel`)

#### Top-Level Functions

- `send_email()` (line 75)
- `async get_customer_email()` (line 100)
- `async get_staff_emails()` (line 130)
- `get_manual_extraction_email_html()` (line 148)
- `get_batch_completion_email_html()` (line 199)
- `async notify_customer_manual_extraction()` (line 255)
- `async notify_batch_completion()` (line 339)
- `async notify_staff()` (line 439)
- `async get_notification_templates()` (line 536)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/customer/manual-extraction` | `notify_customer_manual_extraction` | 255 |
| `POST` | `/batch/completion` | `notify_batch_completion` | 339 |
| `POST` | `/staff` | `notify_staff` | 439 |
| `GET` | `/templates` | `get_notification_templates` | 536 |

#### Database / Supabase Tables Detected

- `auth`
- `batch`
- `database`
- `datetime`
- `fastapi`
- `manual_review_queue`
- `organization`
- `organization_members`
- `organizations`
- `pydantic`
- `review`
- `staff_profiles`
- `typing`
- `upload_batches`
- `your`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `os`
- `pydantic`
- `resend`
- `typing`

### 4.92 `backend/routes/organizations/__init__.py`

- **Module:** `backend.routes.organizations`
- **Package:** `backend.routes`
- **Lines:** 31
- **Size:** 701 bytes
- **Categories:** API
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.`

### 4.93 `backend/routes/organizations/analytics.py`

- **Module:** `backend.routes.organizations.analytics`
- **Package:** `backend.routes.organizations`
- **Lines:** 503
- **Size:** 18,430 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `EmissionsTrendPoint` (line 16; bases: `BaseModel`)
- `EmissionsTrendResponse` (line 23; bases: `BaseModel`)
- `ScopeComparisonResponse` (line 31; bases: `BaseModel`)
- `AssetPerformanceResponse` (line 40; bases: `BaseModel`)
- `AssetPerformanceListResponse` (line 51; bases: `BaseModel`)

#### Top-Level Functions

- `get_quarter()` (line 61)
- `get_month()` (line 70)
- `async get_emissions_trend()` (line 82)
- `get_month()` (line 137)
- `get_quarter()` (line 143)
- `get_year()` (line 151)
- `async get_scope_comparison()` (line 219)
- `async get_asset_performance()` (line 310)
- `async get_analytics_summary()` (line 424)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/emissions-trend` | `get_emissions_trend` | 82 |
| `GET` | `/scope-comparison` | `get_scope_comparison` | 219 |
| `GET` | `/asset-performance` | `get_asset_performance` | 310 |
| `GET` | `/summary` | `get_analytics_summary` | 424 |

#### Database / Supabase Tables Detected

- `assets`
- `auth`
- `database`
- `date`
- `datetime`
- `emissions_logs`
- `facilities`
- `fastapi`
- `pydantic`
- `typing`

#### Imports

- `.management`
- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `traceback`
- `typing`

### 4.94 `backend/routes/organizations/assets.py`

- **Module:** `backend.routes.organizations.assets`
- **Package:** `backend.routes.organizations`
- **Lines:** 1050
- **Size:** 38,437 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `FacilityCreate` (line 21; bases: `BaseModel`)
  - `Config()` (line 36)
- `FacilityUpdate` (line 48; bases: `BaseModel`)
- `FacilityResponse` (line 64; bases: `BaseModel`)
- `AssetCreate` (line 88; bases: `BaseModel`)
- `AssetUpdate` (line 100; bases: `BaseModel`)
- `AssetResponse` (line 113; bases: `BaseModel`)
- `AssetBulkUpdate` (line 133; bases: `BaseModel`)
- `AssetListResponse` (line 138; bases: `BaseModel`)
- `FacilityListResponse` (line 142; bases: `BaseModel`)

#### Top-Level Functions

- `format_address()` (line 150)
- `async get_facility_by_id()` (line 167)
- `async get_facilities()` (line 216)
- `async create_facility()` (line 332)
- `async update_facility()` (line 387)
- `async patch_facility()` (line 442)
- `async delete_facility()` (line 453)
- `async get_facility_stats_endpoint()` (line 521)
- `async get_assets()` (line 590)
- `async create_asset()` (line 713)
- `async update_asset()` (line 820)
- `async delete_asset()` (line 888)
- `async get_asset_stats_endpoint()` (line 969)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/{org_id}/facilities` | `get_facilities` | 216 |
| `POST` | `/{org_id}/facilities` | `create_facility` | 332 |
| `PUT` | `/{org_id}/facilities/{facility_id}` | `update_facility` | 387 |
| `PATCH` | `/{org_id}/facilities/{facility_id}` | `patch_facility` | 442 |
| `DELETE` | `/{org_id}/facilities/{facility_id}` | `delete_facility` | 453 |
| `GET` | `/{org_id}/facilities/stats` | `get_facility_stats_endpoint` | 521 |
| `GET` | `/{org_id}/assets` | `get_assets` | 590 |
| `POST` | `/{org_id}/assets` | `create_asset` | 713 |
| `PUT` | `/{org_id}/assets/{asset_id}` | `update_asset` | 820 |
| `DELETE` | `/{org_id}/assets/{asset_id}` | `delete_asset` | 888 |
| `GET` | `/{org_id}/assets/stats` | `get_asset_stats_endpoint` | 969 |

#### Database / Supabase Tables Detected

- `a`
- `an`
- `asset`
- `assets`
- `auth`
- `database`
- `datetime`
- `emissions_logs`
- `facilities`
- `facility`
- `fastapi`
- `organization_members`
- `pydantic`
- `typing`
- `utils`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `traceback`
- `typing`
- `utils`

### 4.95 `backend/routes/organizations/bulk.py`

- **Module:** `backend.routes.organizations.bulk`
- **Package:** `backend.routes.organizations`
- **Lines:** 270
- **Size:** 9,538 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `BulkMemberInvite` (line 19; bases: `BaseModel`)
- `BulkMemberInviteRequest` (line 23; bases: `BaseModel`)
- `BulkAssetCreate` (line 27; bases: `BaseModel`)
- `BulkAssetCreateRequest` (line 38; bases: `BaseModel`)
- `BulkOperationResult` (line 41; bases: `BaseModel`)

#### Top-Level Functions

- `async bulk_invite_members()` (line 52)
- `async bulk_create_assets()` (line 168)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/{org_id}/members/bulk/invite` | `bulk_invite_members` | 52 |
| `POST` | `/{org_id}/assets/bulk/create` | `bulk_create_assets` | 168 |

#### Database / Supabase Tables Detected

- `assets`
- `auth`
- `database`
- `datetime`
- `facilities`
- `fastapi`
- `organization_members`
- `organizations`
- `pydantic`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

### 4.96 `backend/routes/organizations/dashboard.py`

- **Module:** `backend.routes.organizations.dashboard`
- **Package:** `backend.routes.organizations`
- **Lines:** 272
- **Size:** 10,288 bytes
- **Categories:** API, authentication / security, database / repository, reporting
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async get_dashboard_summary()` (line 15)
- `async get_organization_activity()` (line 167)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/{org_id}/dashboard-summary` | `get_dashboard_summary` | 15 |
| `GET` | `/{org_id}/organization-activity` | `get_organization_activity` | 167 |

#### Database / Supabase Tables Detected

- `auth`
- `database`
- `datetime`
- `emissions_logs`
- `fastapi`
- `organization_members`
- `organizations`
- `path`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `traceback`
- `typing`

### 4.97 `backend/routes/organizations/data.py`

- **Module:** `backend.routes.organizations.data`
- **Package:** `backend.routes.organizations`
- **Lines:** 415
- **Size:** 14,908 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `EmissionsRecord` (line 17; bases: `BaseModel`)
- `EmissionsSummary` (line 29; bases: `BaseModel`)
- `EmissionsResponse` (line 38; bases: `BaseModel`)

#### Top-Level Functions

- `calculate_emissions_summary()` (line 51)
- `async get_organization_emissions()` (line 89)
- `async export_emissions_csv()` (line 200)
- `async get_organization_assets()` (line 281)
- `async get_organization_defra_factors()` (line 364)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/{org_id}/emissions-data` | `get_organization_emissions` | 89 |
| `GET` | `/{org_id}/emissions/export-csv` | `export_emissions_csv` | 200 |
| `GET` | `/organizations/{org_id}/assets ` | `get_organization_assets` | 281 |
| `GET` | `/{org_id}/defra-factors` | `get_organization_defra_factors` | 364 |

#### Database / Supabase Tables Detected

- `assets`
- `auth`
- `database`
- `datetime`
- `defra_conversion_factors`
- `emissions`
- `emissions_logs`
- `facilities`
- `fastapi`
- `organization_members`
- `organizations`
- `path`
- `pydantic`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `fastapi.responses`
- `io`
- `pandas`
- `pydantic`
- `traceback`
- `typing`

### 4.98 `backend/routes/organizations/exports.py`

- **Module:** `backend.routes.organizations.exports`
- **Package:** `backend.routes.organizations`
- **Lines:** 260
- **Size:** 8,483 bytes
- **Categories:** API, CSV / Excel, authentication / security, database / repository
- **V3 impact:** **NO CHANGE**

#### Classes

- `ExportRequest` (line 23; bases: `BaseModel`)
- `ExportResponse` (line 30; bases: `BaseModel`)

#### Top-Level Functions

- `async export_emissions_data()` (line 45)
- `async get_exports()` (line 129)
- `async download_export()` (line 157)
- `async delete_export()` (line 207)
- `generate_csv_export()` (line 236)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/exports/emissions` | `export_emissions_data` | 45 |
| `GET` | `UNKNOWN` | `get_exports` | 129 |
| `GET` | `/{export_id}/download` | `download_export` | 157 |
| `DELETE` | `/{export_id}` | `delete_export` | 207 |

#### Database / Supabase Tables Detected

- `auth`
- `data`
- `database`
- `datetime`
- `emissions_logs`
- `export_history`
- `fastapi`
- `first`
- `pydantic`
- `storage`
- `typing`
- `uuid`

#### Imports

- `auth`
- `csv`
- `database`
- `datetime`
- `fastapi`
- `io`
- `json`
- `pydantic`
- `typing`
- `uuid`

### 4.99 `backend/routes/organizations/files.py`

- **Module:** `backend.routes.organizations.files`
- **Package:** `backend.routes.organizations`
- **Lines:** 1838
- **Size:** 66,094 bytes
- **Categories:** API, Storage, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `FileResponse` (line 19; bases: `BaseModel`)
  - `Config()` (line 36)
- `FileListResponse` (line 56; bases: `BaseModel`)
- `FileUploadResponse` (line 63; bases: `BaseModel`)
- `FileStatsResponse` (line 74; bases: `BaseModel`)
- `FileVersionResponse` (line 1059; bases: `BaseModel`)
- `FileVersionCreate` (line 1075; bases: `BaseModel`)
- `FileCommentCreate` (line 1084; bases: `BaseModel`)
  - `validate_content()` (line 1091)
- `FileCommentUpdate` (line 1099; bases: `BaseModel`)
  - `validate_content()` (line 1105)
- `FileCommentResponse` (line 1113; bases: `BaseModel`)
- `FileVersionDetailResponse` (line 1128; bases: `BaseModel`)

#### Top-Level Functions

- `get_file_type()` (line 91)
- `async get_organization_upload_path()` (line 108)
- `async get_user_name()` (line 124)
- `async get_file_download_url()` (line 139)
- `async get_organization_files()` (line 160)
- `apply_filters()` (line 183)
- `async download_file()` (line 284)
- `async get_file_download_url_endpoint()` (line 366)
- `async delete_file()` (line 430)
- `async upload_file()` (line 509)
- `async get_file_stats()` (line 699)
- `async bulk_upload_files()` (line 777)
- `async archive_file()` (line 919)
- `async restore_file()` (line 967)
- `async get_archived_files()` (line 999)
- `async permanent_delete_file()` (line 1030)
- `async verify_file_access()` (line 1150)
- `async get_file_versions()` (line 1201)
- `async create_file_version()` (line 1278)
- `async get_file_version_detail()` (line 1396)
- `async add_file_comment()` (line 1473)
- `async get_file_comments()` (line 1560)
- `async update_file_comment()` (line 1646)
- `async delete_file_comment()` (line 1754)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/` | `get_organization_files` | 160 |
| `GET` | `/{file_id}/download` | `download_file` | 284 |
| `GET` | `/{file_id}/url` | `get_file_download_url_endpoint` | 366 |
| `DELETE` | `/{file_id}` | `delete_file` | 430 |
| `POST` | `/api/organizations/{org_id}/files/upload` | `upload_file` | 509 |
| `GET` | `/organizations/{org_id}/files/stats` | `get_file_stats` | 699 |
| `POST` | `/bulk-upload` | `bulk_upload_files` | 777 |
| `POST` | `/{org_id}/files/{file_id}/archive` | `archive_file` | 919 |
| `POST` | `/{org_id}/files/{file_id}/restore` | `restore_file` | 967 |
| `GET` | `/{org_id}/files/archived` | `get_archived_files` | 999 |
| `DELETE` | `/{org_id}/files/{file_id}/permanent` | `permanent_delete_file` | 1030 |
| `GET` | `/{org_id}/files/{file_id}/versions` | `get_file_versions` | 1201 |
| `POST` | `/{org_id}/files/{file_id}/versions` | `create_file_version` | 1278 |
| `GET` | `/{org_id}/files/{file_id}/versions/{version_id}` | `get_file_version_detail` | 1396 |
| `POST` | `/{org_id}/files/{file_id}/comments` | `add_file_comment` | 1473 |
| `GET` | `/{org_id}/files/{file_id}/comments` | `get_file_comments` | 1560 |
| `PUT` | `/{org_id}/files/{file_id}/comments/{comment_id}` | `update_file_comment` | 1646 |
| `DELETE` | `/{org_id}/files/{file_id}/comments/{comment_id}` | `delete_file_comment` | 1754 |

#### Database / Supabase Tables Detected

- `Supabase`
- `a`
- `asset`
- `assets`
- `audit_logs`
- `auth`
- `comment`
- `customer_documents`
- `database`
- `datetime`
- `fastapi`
- `file`
- `filename`
- `last`
- `metadata`
- `organization_files`
- `organization_members`
- `pydantic`
- `staff_profiles`
- `storage`
- `supabase`
- `the`
- `this`
- `typing`
- `utils`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `fastapi.responses`
- `io`
- `json`
- `mimetypes`
- `pydantic`
- `supabase`
- `traceback`
- `typing`
- `utils`

### 4.100 `backend/routes/organizations/management.py`

- **Module:** `backend.routes.organizations.management`
- **Package:** `backend.routes.organizations`
- **Lines:** 1243
- **Size:** 45,323 bytes
- **Categories:** API, Storage, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `OrganizationCreate` (line 17; bases: `BaseModel`)
- `OrganizationUpdate` (line 38; bases: `BaseModel`)
- `OrganizationResponse` (line 59; bases: `BaseModel`)
- `OrganizationStats` (line 90; bases: `BaseModel`)
- `EmployeeMetadataUpdate` (line 103; bases: `BaseModel`)
- `FinancialMetadataUpdate` (line 110; bases: `BaseModel`)
- `SustainabilityMetadataUpdate` (line 117; bases: `BaseModel`)
- `ContactMetadataUpdate` (line 123; bases: `BaseModel`)
- `IndustryMetadataUpdate` (line 130; bases: `BaseModel`)
- `CustomMetricsUpdate` (line 135; bases: `BaseModel`)
- `OrganizationMetadataUpdate` (line 138; bases: `BaseModel`)

#### Top-Level Functions

- `async get_organization_name()` (line 170)
- `async get_organization()` (line 187)
- `async create_organization()` (line 253)
- `async update_organization()` (line 305)
- `async delete_organization()` (line 367)
- `async get_organization_stats_endpoint()` (line 434)
- `async get_all_metadata()` (line 485)
- `async get_employee_metadata()` (line 526)
- `async update_employee_metadata()` (line 566)
- `async get_financial_metadata()` (line 623)
- `async update_financial_metadata()` (line 663)
- `async get_sustainability_metadata()` (line 720)
- `async update_sustainability_metadata()` (line 760)
- `async get_contact_metadata()` (line 817)
- `async update_contact_metadata()` (line 857)
- `async get_industry_metadata()` (line 914)
- `async update_industry_metadata()` (line 954)
- `async get_custom_metrics()` (line 1011)
- `async update_custom_metrics()` (line 1051)
- `async validate_metadata()` (line 1112)
- `async get_required_metadata_fields()` (line 1202)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/{org_id}` | `get_organization` | 187 |
| `POST` | `/` | `create_organization` | 253 |
| `PUT` | `/{org_id}` | `update_organization` | 305 |
| `DELETE` | `/{org_id}` | `delete_organization` | 367 |
| `GET` | `/{org_id}/stats` | `get_organization_stats_endpoint` | 434 |
| `GET` | `/{org_id}/metadata/all` | `get_all_metadata` | 485 |
| `GET` | `/{org_id}/metadata/employees` | `get_employee_metadata` | 526 |
| `PUT` | `/{org_id}/metadata/employees` | `update_employee_metadata` | 566 |
| `GET` | `/{org_id}/metadata/financials` | `get_financial_metadata` | 623 |
| `PUT` | `/{org_id}/metadata/financials` | `update_financial_metadata` | 663 |
| `GET` | `/{org_id}/metadata/sustainability` | `get_sustainability_metadata` | 720 |
| `PUT` | `/{org_id}/metadata/sustainability` | `update_sustainability_metadata` | 760 |
| `GET` | `/{org_id}/metadata/contacts` | `get_contact_metadata` | 817 |
| `PUT` | `/{org_id}/metadata/contacts` | `update_contact_metadata` | 857 |
| `GET` | `/{org_id}/metadata/industry` | `get_industry_metadata` | 914 |
| `PUT` | `/{org_id}/metadata/industry` | `update_industry_metadata` | 954 |
| `GET` | `/{org_id}/metadata/custom-metrics` | `get_custom_metrics` | 1011 |
| `PUT` | `/{org_id}/metadata/custom-metrics` | `update_custom_metrics` | 1051 |
| `POST` | `/{org_id}/metadata/validate` | `validate_metadata` | 1112 |
| `GET` | `/{org_id}/metadata/required-fields` | `get_required_metadata_fields` | 1202 |

#### Database / Supabase Tables Detected

- `an`
- `auth`
- `contact`
- `custom`
- `database`
- `datetime`
- `employee`
- `fastapi`
- `financial`
- `industry`
- `organization`
- `organization_members`
- `organization_metadata`
- `organizations`
- `pydantic`
- `supabase`
- `sustainability`
- `typing`
- `utils`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `supabase`
- `typing`
- `utils.organization_utils`

### 4.101 `backend/routes/organizations/members.py`

- **Module:** `backend.routes.organizations.members`
- **Package:** `backend.routes.organizations`
- **Lines:** 971
- **Size:** 35,544 bytes
- **Categories:** AI extraction, API, Storage, authentication / security, database / repository
- **V3 impact:** **NO CHANGE**

#### Classes

- `OrganizationMemberCreate` (line 18; bases: `BaseModel`)
  - `Config()` (line 24)
- `OrganizationMemberUpdate` (line 33; bases: `BaseModel`)
  - `Config()` (line 38)
- `OrganizationMemberResponse` (line 46; bases: `BaseModel`)
- `OrganizationMemberListResponse` (line 59; bases: `BaseModel`)
- `BulkMemberUpdate` (line 718; bases: `BaseModel`)

#### Top-Level Functions

- `async get_organization_by_user()` (line 72)
- `validate_role()` (line 142)
- `get_member_details()` (line 147)
- `async check_user_exists()` (line 188)
- `async get_organization_members()` (line 212)
- `async invite_organization_member()` (line 300)
- `async update_organization_member()` (line 430)
- `async remove_organization_member()` (line 533)
- `async resend_invitation()` (line 621)
- `async bulk_update_members()` (line 723)
- `async bulk_remove_members()` (line 812)
- `async get_member_stats()` (line 901)
- `async get_member_roles()` (line 950)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/user/{user_id}` | `get_organization_by_user` | 72 |
| `GET` | `/` | `get_organization_members` | 212 |
| `POST` | `/invite` | `invite_organization_member` | 300 |
| `PUT` | `/{member_id}` | `update_organization_member` | 430 |
| `DELETE` | `/{member_id}` | `remove_organization_member` | 533 |
| `POST` | `/{member_id}/resend-invite` | `resend_invitation` | 621 |
| `POST` | `/{org_id}/members/bulk/update` | `bulk_update_members` | 723 |
| `POST` | `/{org_id}/members/bulk/remove` | `bulk_remove_members` | 812 |
| `GET` | `/{org_id}/members/stats` | `get_member_stats` | 901 |
| `GET` | `/{org_id}/members/roles` | `get_member_roles` | 950 |

#### Database / Supabase Tables Detected

- `a`
- `auth`
- `completed`
- `database`
- `datetime`
- `dict`
- `existing`
- `fastapi`
- `member`
- `members`
- `organization`
- `organization_members`
- `organizations`
- `our`
- `pydantic`
- `supabase`
- `the`
- `token`
- `typing`
- `user_invitations`
- `utils`
- `your`
- `yourself`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `secrets`
- `supabase`
- `typing`
- `utils.email`

### 4.102 `backend/routes/organizations/metadata.py`

- **Module:** `backend.routes.organizations.metadata`
- **Package:** `backend.routes.organizations`
- **Lines:** 569
- **Size:** 21,177 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `FinancialMetadataUpdate` (line 20; bases: `BaseModel`)
- `EmployeeMetadataUpdate` (line 27; bases: `BaseModel`)
- `SustainabilityMetadataUpdate` (line 34; bases: `BaseModel`)
- `ContactMetadataUpdate` (line 40; bases: `BaseModel`)
- `IndustryMetadataUpdate` (line 47; bases: `BaseModel`)
- `CustomMetricsUpdate` (line 52; bases: `BaseModel`)

#### Top-Level Functions

- `async get_financial_metadata()` (line 60)
- `async update_financial_metadata()` (line 81)
- `async get_employee_metadata()` (line 125)
- `async update_employee_metadata()` (line 146)
- `async get_sustainability_metadata()` (line 189)
- `async update_sustainability_metadata()` (line 210)
- `async get_contact_metadata()` (line 253)
- `async update_contact_metadata()` (line 274)
- `async get_industry_metadata()` (line 317)
- `async update_industry_metadata()` (line 338)
- `async get_custom_metrics()` (line 381)
- `async update_custom_metrics()` (line 402)
- `async get_all_metadata()` (line 445)
- `async validate_metadata()` (line 471)
- `async get_required_metadata_fields()` (line 546)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/{org_id}/metadata/financials` | `get_financial_metadata` | 60 |
| `PUT` | `/{org_id}/metadata/financials` | `update_financial_metadata` | 81 |
| `GET` | `/{org_id}/metadata/employees` | `get_employee_metadata` | 125 |
| `PUT` | `/{org_id}/metadata/employees` | `update_employee_metadata` | 146 |
| `GET` | `/{org_id}/metadata/sustainability` | `get_sustainability_metadata` | 189 |
| `PUT` | `/{org_id}/metadata/sustainability` | `update_sustainability_metadata` | 210 |
| `GET` | `/{org_id}/metadata/contacts` | `get_contact_metadata` | 253 |
| `PUT` | `/{org_id}/metadata/contacts` | `update_contact_metadata` | 274 |
| `GET` | `/{org_id}/metadata/industry` | `get_industry_metadata` | 317 |
| `PUT` | `/{org_id}/metadata/industry` | `update_industry_metadata` | 338 |
| `GET` | `/{org_id}/metadata/custom-metrics` | `get_custom_metrics` | 381 |
| `PUT` | `/{org_id}/metadata/custom-metrics` | `update_custom_metrics` | 402 |
| `GET` | `/{org_id}/metadata/all` | `get_all_metadata` | 445 |
| `POST` | `/{org_id}/metadata/validate` | `validate_metadata` | 471 |
| `GET` | `/{org_id}/metadata/required-fields` | `get_required_metadata_fields` | 546 |

#### Database / Supabase Tables Detected

- `auth`
- `contact`
- `custom`
- `database`
- `datetime`
- `employee`
- `fastapi`
- `financial`
- `industry`
- `organization_metadata`
- `pydantic`
- `sustainability`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `typing`

### 4.103 `backend/routes/organizations/team.py`

- **Module:** `backend.routes.organizations.team`
- **Package:** `backend.routes.organizations`
- **Lines:** 285
- **Size:** 10,092 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `MemberUpdate` (line 12; bases: `BaseModel`)

#### Top-Level Functions

- `async get_team_members()` (line 16)
- `async invite_team_member()` (line 98)
- `async update_member_role()` (line 170)
- `async remove_member()` (line 230)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/{org_id}/members` | `get_team_members` | 16 |
| `POST` | `/{org_id}/invite` | `invite_team_member` | 98 |
| `PATCH` | `/{org_id}/members/{member_id}` | `update_member_role` | 170 |
| `DELETE` | `/{org_id}/members/{member_id}` | `remove_member` | 230 |

#### Database / Supabase Tables Detected

- `a`
- `auth`
- `database`
- `fastapi`
- `member`
- `organization_members`
- `pydantic`
- `role`
- `the`
- `typing`

#### Imports

- `auth`
- `database`
- `fastapi`
- `os`
- `pydantic`
- `traceback`
- `typing`

### 4.104 `backend/routes/reference.py`

- **Module:** `backend.routes.reference`
- **Package:** `backend.routes`
- **Lines:** 201
- **Size:** 6,579 bytes
- **Categories:** API, authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async get_units()` (line 19)
- `async get_fuel_types()` (line 50)
- `async get_reference_categories()` (line 85)
- `async get_facilities_list()` (line 121)
- `async get_assets_list()` (line 153)
- `async get_facility_types()` (line 186)
- `async get_asset_types()` (line 195)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/units` | `get_units` | 19 |
| `GET` | `/fuel-types` | `get_fuel_types` | 50 |
| `GET` | `/categories` | `get_reference_categories` | 85 |
| `GET` | `/facilities` | `get_facilities_list` | 121 |
| `GET` | `/assets` | `get_assets_list` | 153 |
| `GET` | `/facility-types` | `get_facility_types` | 186 |
| `GET` | `/asset-types` | `get_asset_types` | 195 |

#### Database / Supabase Tables Detected

- `activity_categories`
- `auth`
- `database`
- `defra_conversion_factors`
- `fastapi`
- `typing`
- `units`

#### Imports

- `auth`
- `database`
- `fastapi`
- `typing`

### 4.105 `backend/routes/reports.py`

- **Module:** `backend.routes.reports`
- **Package:** `backend.routes`
- **Lines:** 2098
- **Size:** 84,164 bytes
- **Categories:** API, Storage, authentication / security, database / repository, reporting
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `CustomerSummaryReportResponse` (line 36; bases: `BaseModel`)
- `StaffPerformanceReportResponse` (line 52; bases: `BaseModel`)
- `OrganizationComparisonReportResponse` (line 70; bases: `BaseModel`)
- `EmissionsTrendReportResponse` (line 77; bases: `BaseModel`)
- `GenerateReportRequest` (line 90; bases: `BaseModel`)
- `GenerateReportResponse` (line 100; bases: `BaseModel`)
- `ReportScheduleCreate` (line 110; bases: `BaseModel`)
- `ReportScheduleResponse` (line 123; bases: `BaseModel`)
- `ReportTemplateCreate` (line 144; bases: `BaseModel`)
- `ReportTemplateUpdate` (line 153; bases: `BaseModel`)
- `ReportTemplateResponse` (line 161; bases: `BaseModel`)
- `ReportShareCreate` (line 176; bases: `BaseModel`)
- `ReportShareResponse` (line 182; bases: `BaseModel`)

#### Top-Level Functions

- `async verify_org_access()` (line 200)
- `async report_service_status()` (line 227)
- `async get_defra_mapping()` (line 244)
- `async get_defra_factors_by_year()` (line 272)
- `async get_customer_summary_report()` (line 302)
- `async get_staff_performance_report()` (line 504)
- `async get_organization_comparison_report()` (line 644)
- `async get_emissions_trend_report()` (line 775)
- `async generate_custom_report()` (line 990)
- `async get_report_types()` (line 1158)
- `async get_available_metrics()` (line 1175)
- `async get_schedule_frequencies()` (line 1195)
- `async get_template_categories()` (line 1210)
- `async import_defra_factors()` (line 1239)
- `async generate_enhanced_sustainability_report()` (line 1288)
- `async create_report_schedule()` (line 1328)
- `async get_report_schedules()` (line 1429)
- `async delete_report_schedule()` (line 1490)
- `async get_report_templates()` (line 1536)
- `async create_report_template()` (line 1605)
- `async update_report_template()` (line 1679)
- `async delete_report_template()` (line 1788)
- `async share_report()` (line 1843)
- `async get_shared_reports()` (line 1962)
- `calculate_next_run()` (line 2034)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `GET` | `/report_status` | `report_service_status` | 227 |
| `GET` | `/defra-mapping` | `get_defra_mapping` | 244 |
| `GET` | `/defra-factors/{reporting_year}` | `get_defra_factors_by_year` | 272 |
| `GET` | `/customer/summary` | `get_customer_summary_report` | 302 |
| `GET` | `/admin/staff-performance` | `get_staff_performance_report` | 504 |
| `GET` | `/admin/organization-comparison` | `get_organization_comparison_report` | 644 |
| `GET` | `/emissions/trend` | `get_emissions_trend_report` | 775 |
| `POST` | `/generate` | `generate_custom_report` | 990 |
| `GET` | `/types` | `get_report_types` | 1158 |
| `GET` | `/metrics` | `get_available_metrics` | 1175 |
| `GET` | `/schedule/frequencies` | `get_schedule_frequencies` | 1195 |
| `GET` | `/templates/categories` | `get_template_categories` | 1210 |
| `POST` | `/admin/import-defra-factors` | `import_defra_factors` | 1239 |
| `POST` | `/generate-enhanced-report` | `generate_enhanced_sustainability_report` | 1288 |
| `POST` | `/schedule` | `create_report_schedule` | 1328 |
| `GET` | `/schedule` | `get_report_schedules` | 1429 |
| `DELETE` | `/schedule/{schedule_id}` | `delete_report_schedule` | 1490 |
| `GET` | `/templates` | `get_report_templates` | 1536 |
| `POST` | `/templates` | `create_report_template` | 1605 |
| `PUT` | `/templates/{template_id}` | `update_report_template` | 1679 |
| `DELETE` | `/templates/{template_id}` | `delete_report_template` | 1788 |
| `POST` | `/{report_id}/share` | `share_report` | 1843 |
| `GET` | `/shared` | `get_shared_reports` | 1962 |

#### Database / Supabase Tables Detected

- `a`
- `audit_logs`
- `auth`
- `customer_documents`
- `database`
- `datetime`
- `defra_conversion_factors`
- `emissions_logs`
- `fastapi`
- `manual_review_queue`
- `metadata`
- `now`
- `organization_members`
- `organizations`
- `pydantic`
- `report`
- `report_generator`
- `report_history`
- `report_schedules`
- `report_templates`
- `staff_profiles`
- `supabase`
- `this`
- `typing`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `fastapi.responses`
- `io`
- `pandas`
- `pydantic`
- `report_generator`
- `supabase`
- `traceback`
- `typing`
- `uuid`

### 4.106 `backend/routes/upload.py`

- **Module:** `backend.routes.upload`
- **Package:** `backend.routes`
- **Lines:** 1014
- **Size:** 38,489 bytes
- **Categories:** AI extraction, API, authentication / security, calculation, database / repository, reporting
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `async get_system_settings()` (line 34)
- `async validate_file_upload()` (line 78)
- `async test_upload()` (line 108)
- `async upload_csv()` (line 124)
- `async upload_pdf()` (line 185)
- `async upload_batch()` (line 273)
- `async repair_pdf()` (line 302)
- `has_low_confidence()` (line 431)
- `extract_issues_from_result()` (line 439)
- `async upload_document()` (line 553)
- `async get_batch_status()` (line 788)
- `async get_batch_progress()` (line 849)
- `async cancel_batch()` (line 892)
- `async get_batch_stats()` (line 957)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/test-upload` | `test_upload` | 108 |
| `POST` | `/upload-csv` | `upload_csv` | 124 |
| `POST` | `/upload-pdf` | `upload_pdf` | 185 |
| `POST` | `/upload-batch` | `upload_batch` | 273 |
| `POST` | `/repair-pdf` | `repair_pdf` | 302 |
| `POST` | `/upload` | `upload_document` | 553 |
| `GET` | `/batches/{batch_id}/status` | `get_batch_status` | 788 |
| `GET` | `/batches/{batch_id}/progress` | `get_batch_progress` | 849 |
| `POST` | `/batches/{batch_id}/cancel` | `cancel_batch` | 892 |
| `GET` | `/batches/stats` | `get_batch_stats` | 957 |

#### Database / Supabase Tables Detected

- `PIL`
- `assets`
- `auth`
- `batch`
- `database`
- `datetime`
- `documents`
- `fastapi`
- `file`
- `main`
- `manual_review_queue`
- `organization_files`
- `organization_members`
- `pdf2image`
- `pdf_engine`
- `pypdf`
- `reportlab`
- `summary`
- `system_settings`
- `the`
- `typing`
- `upload_batches`
- `utils`
- `validation`

#### Imports

- `PIL`
- `auth`
- `database`
- `datetime`
- `fastapi`
- `io`
- `main`
- `numpy`
- `pandas`
- `pdf2image`
- `pdf_engine`
- `pypdf`
- `pytesseract`
- `reportlab.lib.pagesizes`
- `reportlab.lib.units`
- `reportlab.lib.utils`
- `reportlab.pdfgen`
- `traceback`
- `typing`
- `utils.emissions`

### 4.107 `backend/routes/users.py`

- **Module:** `backend.routes.users`
- **Package:** `backend.routes`
- **Lines:** 349
- **Size:** 12,426 bytes
- **Categories:** AI extraction, API, Storage, authentication / security, database / repository
- **V3 impact:** **NO CHANGE**

#### Classes

- `PasswordResetRequest` (line 16; bases: `BaseModel`)
- `PasswordResetConfirm` (line 19; bases: `BaseModel`)
- `PasswordChangeRequest` (line 23; bases: `BaseModel`)
- `ProfileUpdate` (line 27; bases: `BaseModel`)
- `UserProfileResponse` (line 33; bases: `BaseModel`)

#### Top-Level Functions

- `async request_password_reset()` (line 53)
- `async confirm_password_reset()` (line 115)
- `async get_user_profile()` (line 184)
- `async update_user_profile()` (line 228)
- `async change_password()` (line 292)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/password-reset` | `request_password_reset` | 53 |
| `POST` | `/password-reset/confirm` | `confirm_password_reset` | 115 |
| `GET` | `/profile` | `get_user_profile` | 184 |
| `PUT` | `/profile` | `update_user_profile` | 228 |
| `POST` | `/change-password` | `change_password` | 292 |

#### Database / Supabase Tables Detected

- `auth`
- `current`
- `database`
- `datetime`
- `email`
- `fastapi`
- `organizations`
- `password`
- `password_reset_tokens`
- `profile`
- `pydantic`
- `staff`
- `staff_profiles`
- `supabase`
- `typing`
- `user`
- `utils`

#### Imports

- `auth`
- `database`
- `datetime`
- `fastapi`
- `pydantic`
- `secrets`
- `supabase`
- `typing`
- `utils.email`

### 4.108 `backend/routes/waitlist.py`

- **Module:** `backend.routes.waitlist`
- **Package:** `backend.routes`
- **Lines:** 24
- **Size:** 706 bytes
- **Categories:** AI extraction, API, database / repository
- **V3 impact:** **NO CHANGE**

#### Classes

- `WaitlistRequest` (line 8; bases: `BaseModel`)

#### Top-Level Functions

- `async add_to_waitlist()` (line 17)
- `async get_waitlist()` (line 22)

#### API Routes

| Method | Path | Function | Line |
|---|---|---|---:|
| `POST` | `/` | `add_to_waitlist` | 17 |
| `GET` | `/` | `get_waitlist` | 22 |

#### Database / Supabase Tables Detected

- `database`
- `datetime`
- `fastapi`
- `pydantic`

#### Imports

- `database`
- `datetime`
- `fastapi`
- `pydantic`

### 4.109 `backend/services/email_service.py`

- **Module:** `backend.services.email_service`
- **Package:** `backend.services`
- **Lines:** 346
- **Size:** 12,643 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Parse Status

⚠️ `SyntaxError: unexpected indent at line 18`

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `datetime`
- `email_logs`
- `supabase`
- `typing`

#### Imports

- None detected.

### 4.110 `backend/tests/__init__.py`

- **Module:** `backend.tests`
- **Package:** `backend`
- **Lines:** 2
- **Size:** 65 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.111 `backend/tests/audit_code.py`

- **Module:** `backend.tests.audit_code`
- **Package:** `backend.tests`
- **Lines:** 364
- **Size:** 14,473 bytes
- **Categories:** audit / logging
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `CodeAuditor` (line 14; bases: `-`)
  - `__init__()` (line 15)
  - `audit_all()` (line 24)
  - `check_duplicate_functions()` (line 39)
  - `check_missing_imports()` (line 84)
  - `check_duplicate_endpoints()` (line 146)
  - `check_supabase_queries()` (line 193)
  - `check_error_handling()` (line 238)
  - `check_import_organization()` (line 279)
  - `print_summary()` (line 325)

#### Top-Level Functions

- `main()` (line 348)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `auth`
- `collections`
- `pathlib`
- `tests`
- `the`
- `typing`

#### Imports

- `ast`
- `collections`
- `os`
- `pathlib`
- `re`
- `typing`

### 4.112 `backend/tests/auth_helper.py`

- **Module:** `backend.tests.auth_helper`
- **Package:** `backend.tests`
- **Lines:** 129
- **Size:** 4,479 bytes
- **Categories:** authentication / security
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `AuthHelper` (line 11; bases: `-`)
  - `__init__()` (line 12)
  - `async login()` (line 18)
  - `get_headers()` (line 43)
  - `async refresh_token()` (line 54)
- `TestUser` (line 75; bases: `-`)
  - `__init__()` (line 76)
  - `async authenticate()` (line 85)
  - `get_headers()` (line 94)

#### Top-Level Functions

- `async create_test_users()` (line 101)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `datetime`
- `typing`

#### Imports

- `datetime`
- `httpx`
- `json`
- `typing`

### 4.113 `backend/tests/check_imports.py`

- **Module:** `backend.tests.check_imports`
- **Package:** `backend.tests`
- **Lines:** 63
- **Size:** 2,044 bytes
- **Categories:** CSV / Excel
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `check_imports()` (line 6)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `auth`
- `pathlib`

#### Imports

- `os`
- `pathlib`
- `re`

### 4.114 `backend/tests/config.py`

- **Module:** `backend.tests.config`
- **Package:** `backend.tests`
- **Lines:** 28
- **Size:** 921 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `TestConfig` (line 11; bases: `-`)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `dotenv`

#### Imports

- `dotenv`
- `os`

### 4.115 `backend/tests/create_test_users.py`

- **Module:** `backend.tests.create_test_users`
- **Package:** `backend.tests`
- **Lines:** 197
- **Size:** 6,687 bytes
- **Categories:** authentication / security, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async create_test_users()` (line 49)
- `async create_test_organization()` (line 116)
- `async main()` (line 174)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `auth`
- `database`
- `dotenv`
- `organization_members`
- `organizations`
- `pathlib`
- `staff_profiles`

#### Imports

- `asyncio`
- `auth`
- `database`
- `dotenv`
- `os`
- `pathlib`
- `sys`
- `traceback`

### 4.116 `backend/tests/export_postman.py`

- **Module:** `backend.tests.export_postman`
- **Package:** `backend.tests`
- **Lines:** 61
- **Size:** 1,896 bytes
- **Categories:** CSV / Excel
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `export_to_postman()` (line 9)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `pathlib`

#### Imports

- `json`
- `pathlib`

### 4.117 `backend/tests/fix_imports.py`

- **Module:** `backend.tests.fix_imports`
- **Package:** `backend.tests`
- **Lines:** 57
- **Size:** 1,981 bytes
- **Categories:** CSV / Excel
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `fix_auth_imports()` (line 6)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `auth`
- `pathlib`

#### Imports

- `os`
- `pathlib`
- `re`

### 4.118 `backend/tests/integration/__init__.py`

- **Module:** `backend.tests.integration`
- **Package:** `backend.tests`
- **Lines:** 6
- **Size:** 223 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.119 `backend/tests/integration/conftest.py`

- **Module:** `backend.tests.integration.conftest`
- **Package:** `backend.tests.integration`
- **Lines:** 182
- **Size:** 6,358 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `async pool()` (line 67)
- `new_id()` (line 80)
- `async _seed_system_member()` (line 85)
- `async make_org()` (line 120)
- `async make_user()` (line 139)
- `async make_snapshot()` (line 151)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `datetime`
- `domain`
- `public`

#### Imports

- `__future__`
- `asyncpg`
- `data.organizations`
- `datetime`
- `domain.organization`
- `os`
- `pytest`
- `uuid`

### 4.120 `backend/tests/integration/test_ai_extraction.py`

- **Module:** `backend.tests.integration.test_ai_extraction`
- **Package:** `backend.tests.integration`
- **Lines:** 106
- **Size:** 3,521 bytes
- **Categories:** AI extraction, audit / logging, document processing, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `_LlmHandler` (line 35; bases: `BaseHTTPRequestHandler`)
  - `do_POST()` (line 36)
  - `log_message()` (line 47)

#### Top-Level Functions

- `_serve()` (line 51)
- `async test_ai_extraction_end_to_end()` (line 60)
- `async persist()` (line 68)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `domain`
- `engines`
- `http`
- `infra`
- `tests`
- `typing`

#### Imports

- `__future__`
- `asyncpg`
- `data.documents`
- `data.events`
- `domain.workflow`
- `engines.ai_extraction`
- `http.server`
- `infra.event_bus`
- `infra.llm_client`
- `json`
- `pytest`
- `tests.integration.conftest`
- `threading`
- `typing`

### 4.121 `backend/tests/integration/test_audit.py`

- **Module:** `backend.tests.integration.test_audit`
- **Package:** `backend.tests.integration`
- **Lines:** 103
- **Size:** 3,585 bytes
- **Categories:** AI extraction, audit / logging
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_entry()` (line 16)
- `async test_record_and_get_round_trip()` (line 34)
- `async test_query_filters()` (line 50)
- `async test_get_by_correlation()` (line 76)
- `async test_export_csv()` (line 85)
- `async test_save_and_delete()` (line 95)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `datetime`
- `domain`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `data.audit`
- `datetime`
- `domain.audit`
- `pytest`
- `tests.integration.conftest`

### 4.122 `backend/tests/integration/test_audit_logger.py`

- **Module:** `backend.tests.integration.test_audit_logger`
- **Package:** `backend.tests.integration`
- **Lines:** 99
- **Size:** 3,171 bytes
- **Categories:** AI extraction, audit / logging
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_make_logger()` (line 20)
- `async test_log_action_and_query_round_trip()` (line 24)
- `async test_audit_decorator_records_success()` (line 49)
- `async process()` (line 61)
- `async test_audit_decorator_records_failure_and_reraises()` (line 74)
- `async run_import()` (line 87)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `domain`
- `infra`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `data.audit`
- `domain.audit`
- `infra.audit_logger`
- `pytest`
- `tests.integration.conftest`

### 4.123 `backend/tests/integration/test_calculation.py`

- **Module:** `backend.tests.integration.test_calculation`
- **Package:** `backend.tests.integration`
- **Lines:** 278
- **Size:** 9,418 bytes
- **Categories:** AI extraction, audit / logging, calculation, emission factors, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `async _seed_factor()` (line 34)
- `_request()` (line 51)
- `async _delete_snapshot()` (line 75)
- `async _cleanup()` (line 83)
- `async test_calculate_produces_correct_co2e_and_persists_snapshot()` (line 98)
- `async test_content_hash_is_verifiable()` (line 137)
- `async test_calculate_updates_existing_log()` (line 158)
- `async test_calculate_publishes_and_persists_events()` (line 209)
- `async persist()` (line 216)
- `async test_calculate_records_audit_entry()` (line 235)
- `async test_unit_mismatch_is_rejected_without_persistence()` (line 257)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `data`
- `datetime`
- `decimal`
- `domain`
- `engines`
- `infra`
- `public`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `core.exceptions`
- `data.audit`
- `data.emission_factors`
- `data.emissions_logs`
- `data.events`
- `datetime`
- `decimal`
- `domain.calculation`
- `domain.factor`
- `domain.workflow`
- `engines.calculation`
- `infra.audit_logger`
- `infra.event_bus`
- `pytest`
- `tests.integration.conftest`

### 4.124 `backend/tests/integration/test_config.py`

- **Module:** `backend.tests.integration.test_config`
- **Package:** `backend.tests.integration`
- **Lines:** 47
- **Size:** 1,428 bytes
- **Categories:** Storage
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `_fresh_config()` (line 19)
- `test_config_agrees_with_infra_supabase()` (line 25)
- `test_config_is_singleton()` (line 34)
- `test_config_defaults_are_valid()` (line 38)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `collections`
- `infra`

#### Imports

- `__future__`
- `collections.abc`
- `infra.config`
- `infra.supabase`
- `pytest`

### 4.125 `backend/tests/integration/test_documents.py`

- **Module:** `backend.tests.integration.test_documents`
- **Package:** `backend.tests.integration`
- **Lines:** 93
- **Size:** 3,251 bytes
- **Categories:** document processing
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async test_create_from_upload_and_get()` (line 13)
- `async test_update_status()` (line 32)
- `async test_get_pending_extraction()` (line 45)
- `async test_get_by_org()` (line 59)
- `async test_save_updates_document()` (line 73)
- `async test_delete()` (line 86)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `dataclasses`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `data.documents`
- `dataclasses`
- `pytest`
- `tests.integration.conftest`

### 4.126 `backend/tests/integration/test_emission_factors.py`

- **Module:** `backend.tests.integration.test_emission_factors`
- **Package:** `backend.tests.integration`
- **Lines:** 230
- **Size:** 7,414 bytes
- **Categories:** AI extraction, CSV / Excel, calculation, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_factor()` (line 17)
- `async _repo()` (line 41)
- `async test_save_and_get_round_trip()` (line 45)
- `async test_get_missing_returns_none()` (line 66)
- `async test_save_updates_existing_by_natural_key()` (line 71)
- `async test_find_by_natural_key_exact()` (line 87)
- `async test_find_by_natural_key_null_unit_scope()` (line 100)
- `async test_find_by_activity_keyword_and_filters()` (line 112)
- `async test_bulk_upsert_counts_and_idempotency()` (line 131)
- `async test_get_active_set_and_deactivate_by_batch()` (line 161)
- `async test_count_by_provider()` (line 194)
- `async test_load_all_for_index()` (line 213)
- `async test_delete()` (line 224)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `decimal`
- `domain`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `data.emission_factors`
- `data.imports`
- `decimal`
- `domain.factor`
- `pytest`
- `tests.integration.conftest`

### 4.127 `backend/tests/integration/test_emissions_logs.py`

- **Module:** `backend.tests.integration.test_emissions_logs`
- **Package:** `backend.tests.integration`
- **Lines:** 149
- **Size:** 5,221 bytes
- **Categories:** AI extraction, audit / logging, calculation, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `async _seed_factor()` (line 19)
- `async test_create_and_get_round_trip()` (line 39)
- `async test_save_updates_calculated_value()` (line 68)
- `async test_find_by_org_period_filter()` (line 91)
- `async test_aggregate_and_count_by_scope()` (line 113)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `data`
- `dataclasses`
- `datetime`
- `decimal`
- `domain`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `core.types`
- `data.emission_factors`
- `data.emissions_logs`
- `dataclasses`
- `datetime`
- `decimal`
- `domain.factor`
- `pytest`
- `tests.integration.conftest`

### 4.128 `backend/tests/integration/test_event_bus.py`

- **Module:** `backend.tests.integration.test_event_bus`
- **Package:** `backend.tests.integration`
- **Lines:** 104
- **Size:** 3,152 bytes
- **Categories:** AI extraction, audit / logging, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_document_event()` (line 22)
- `async test_bus_persists_events_via_handler()` (line 33)
- `async persist()` (line 39)
- `async test_bus_background_publish_then_drain()` (line 57)
- `async persist()` (line 62)
- `async test_bus_wildcard_handler_and_failing_handler_isolated()` (line 83)
- `async failing()` (line 90)
- `async persist()` (line 93)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `datetime`
- `domain`
- `infra`
- `tests`
- `typing`

#### Imports

- `__future__`
- `asyncpg`
- `data.events`
- `datetime`
- `domain.workflow`
- `infra.event_bus`
- `pytest`
- `tests.integration.conftest`
- `typing`

### 4.129 `backend/tests/integration/test_events.py`

- **Module:** `backend.tests.integration.test_events`
- **Package:** `backend.tests.integration`
- **Lines:** 111
- **Size:** 3,465 bytes
- **Categories:** AI extraction, audit / logging, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `async test_store_and_reconstruct_typed_event()` (line 22)
- `async test_decimal_event_round_trip()` (line 44)
- `async test_tuple_field_event_round_trip()` (line 60)
- `async test_get_by_correlation_and_replay()` (line 76)
- `async test_delete()` (line 100)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `datetime`
- `decimal`
- `domain`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `data.events`
- `datetime`
- `decimal`
- `domain.workflow`
- `pytest`
- `tests.integration.conftest`

### 4.130 `backend/tests/integration/test_extraction.py`

- **Module:** `backend.tests.integration.test_extraction`
- **Package:** `backend.tests.integration`
- **Lines:** 81
- **Size:** 2,622 bytes
- **Categories:** AI extraction, audit / logging, document processing, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `async test_extraction_updates_document_and_persists_events()` (line 22)
- `async persist()` (line 30)
- `async test_failed_extraction_marks_document_failed()` (line 63)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `data`
- `domain`
- `engines`
- `infra`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `core.exceptions`
- `data.documents`
- `data.events`
- `domain.workflow`
- `engines.extraction`
- `infra.event_bus`
- `pytest`
- `tests.integration.conftest`

### 4.131 `backend/tests/integration/test_factor_aliases.py`

- **Module:** `backend.tests.integration.test_factor_aliases`
- **Package:** `backend.tests.integration`
- **Lines:** 95
- **Size:** 3,455 bytes
- **Categories:** AI extraction, emission factors, factor matching
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_alias()` (line 14)
- `async test_save_global_alias_and_get()` (line 25)
- `async test_find_by_alias_org_scoped_then_global()` (line 36)
- `async test_global_and_org_alias_lists()` (line 60)
- `async test_save_updates_existing_alias()` (line 76)
- `async test_delete()` (line 90)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `dataclasses`
- `domain`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `data.factor_aliases`
- `dataclasses`
- `domain.matching`
- `pytest`
- `tests.integration.conftest`

### 4.132 `backend/tests/integration/test_factor_matching.py`

- **Module:** `backend.tests.integration.test_factor_matching`
- **Package:** `backend.tests.integration`
- **Lines:** 330
- **Size:** 12,777 bytes
- **Categories:** AI extraction, audit / logging, calculation, emission factors, factor matching, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `_Seeded` (line 68; bases: `-`)
  - `__init__()` (line 69)

#### Top-Level Functions

- `_factor()` (line 44)
- `async seeded()` (line 91)
- `_engine()` (line 150)
- `_request()` (line 169)
- `async test_pipeline_query()` (line 224)
- `async test_no_match_suggestions_are_ranked_candidates()` (line 265)
- `async test_no_match_without_candidates_has_no_suggestions()` (line 274)
- `async test_max_stages_limits_executed_pipeline()` (line 282)
- `async test_engine_publishes_and_persists_factor_matched()` (line 291)
- `async persist()` (line 295)
- `async test_engine_audits_every_outcome()` (line 314)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `datetime`
- `decimal`
- `domain`
- `engines`
- `infra`
- `tests`
- `the`
- `typing`

#### Imports

- `__future__`
- `asyncpg`
- `data.audit`
- `data.emission_factors`
- `data.events`
- `data.factor_aliases`
- `datetime`
- `decimal`
- `domain.audit`
- `domain.factor`
- `domain.matching`
- `domain.workflow`
- `engines.factor_matching`
- `engines.matching_stages`
- `infra.audit_logger`
- `infra.event_bus`
- `infra.search_index`
- `pytest`
- `tests.integration.conftest`
- `typing`

### 4.133 `backend/tests/integration/test_imports.py`

- **Module:** `backend.tests.integration.test_imports`
- **Package:** `backend.tests.integration`
- **Lines:** 129
- **Size:** 4,484 bytes
- **Categories:** AI extraction, CSV / Excel, factor provider
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `async test_create_batch_round_trip()` (line 14)
- `async test_complete_and_fail_batch()` (line 35)
- `async test_activation_single_active_invariant()` (line 58)
- `async test_rollback_and_history()` (line 81)
- `async test_deactivate_batch()` (line 102)
- `async test_save_updates_batch_fields()` (line 114)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `dataclasses`
- `domain`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `data.imports`
- `dataclasses`
- `domain.provider`
- `pytest`
- `tests.integration.conftest`

### 4.134 `backend/tests/integration/test_infra.py`

- **Module:** `backend.tests.integration.test_infra`
- **Package:** `backend.tests.integration`
- **Lines:** 34
- **Size:** 780 bytes
- **Categories:** Storage
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `test_service_client_is_singleton()` (line 13)
- `test_create_service_client_fresh()` (line 21)
- `test_get_service_client_after_reset()` (line 28)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `infra`

#### Imports

- `__future__`
- `infra.supabase`
- `pytest`

### 4.135 `backend/tests/integration/test_llm_client.py`

- **Module:** `backend.tests.integration.test_llm_client`
- **Package:** `backend.tests.integration`
- **Lines:** 111
- **Size:** 3,496 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- `_OkHandler` (line 22; bases: `BaseHTTPRequestHandler`)
  - `do_POST()` (line 23)
  - `log_message()` (line 34)
- `_ErrorHandler` (line 38; bases: `BaseHTTPRequestHandler`)
  - `do_POST()` (line 39)
  - `log_message()` (line 47)
- `_MalformedHandler` (line 51; bases: `BaseHTTPRequestHandler`)
  - `do_POST()` (line 52)
  - `log_message()` (line 61)

#### Top-Level Functions

- `_serve()` (line 65)
- `_client()` (line 74)
- `async test_complete_against_real_server()` (line 83)
- `async test_http_error_maps_to_aiextraction_failed()` (line 93)
- `async test_malformed_body_maps_to_aiextraction_failed()` (line 103)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `http`
- `infra`
- `server`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `http.server`
- `infra.llm_client`
- `json`
- `pytest`
- `threading`
- `typing`

### 4.136 `backend/tests/integration/test_organizations.py`

- **Module:** `backend.tests.integration.test_organizations`
- **Package:** `backend.tests.integration`
- **Lines:** 166
- **Size:** 5,075 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `async _org()` (line 16)
- `async _insert_member()` (line 26)
- `async _insert_facility()` (line 44)
- `async _insert_asset()` (line 59)
- `async test_save_and_get_round_trip()` (line 75)
- `async test_get_missing_returns_none()` (line 88)
- `async test_get_members()` (line 93)
- `async test_metadata_upsert()` (line 107)
- `async test_get_facilities_and_assets()` (line 139)
- `async test_delete()` (line 160)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `datetime`
- `domain`
- `public`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `data.organizations`
- `datetime`
- `domain.organization`
- `pytest`
- `tests.integration.conftest`

### 4.137 `backend/tests/integration/test_reports.py`

- **Module:** `backend.tests.integration.test_reports`
- **Package:** `backend.tests.integration`
- **Lines:** 87
- **Size:** 2,977 bytes
- **Categories:** database / repository, reporting
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async test_create_generation_request()` (line 13)
- `async test_complete_generation()` (line 27)
- `async test_get_by_org()` (line 49)
- `async test_save_updates_report()` (line 66)
- `async test_delete()` (line 80)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `dataclasses`
- `tests`

#### Imports

- `__future__`
- `asyncpg`
- `data.reports`
- `dataclasses`
- `pytest`
- `tests.integration.conftest`

### 4.138 `backend/tests/integration/test_search_index.py`

- **Module:** `backend.tests.integration.test_search_index`
- **Package:** `backend.tests.integration`
- **Lines:** 78
- **Size:** 2,807 bytes
- **Categories:** AI extraction, calculation, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_factor()` (line 22)
- `async test_index_loads_from_real_repository_data()` (line 39)
- `async test_exact_natural_key_miss_returns_none()` (line 69)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `data`
- `decimal`
- `domain`
- `infra`
- `tests`
- `the`

#### Imports

- `__future__`
- `asyncpg`
- `data.emission_factors`
- `decimal`
- `domain.factor`
- `infra.search_index`
- `pytest`
- `tests.integration.conftest`

### 4.139 `backend/tests/integration/test_workflow.py`

- **Module:** `backend.tests.integration.test_workflow`
- **Package:** `backend.tests.integration`
- **Lines:** 466
- **Size:** 16,179 bytes
- **Categories:** AI extraction, audit / logging, calculation, document processing, emission factors, factor matching, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `_LlmHandler` (line 64; bases: `BaseHTTPRequestHandler`)
  - `do_POST()` (line 69)
  - `log_message()` (line 80)

#### Top-Level Functions

- `_serve()` (line 84)
- `_llm_fields()` (line 93)
- `async _seed_factor()` (line 103)
- `_matching_engine()` (line 123)
- `async _cleanup()` (line 138)
- `async _wire()` (line 176)
- `async persist()` (line 198)
- `async _fetch_events()` (line 234)
- `async test_workflow_end_to_end_completes_with_persisted_state()` (line 261)
- `async test_low_ai_confidence_routes_to_manual_review()` (line 333)
- `async test_workflow_failure_marks_document_failed_and_raises()` (line 379)
- `async test_registered_handlers_drive_submitted_pipeline()` (line 421)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `data`
- `decimal`
- `domain`
- `engines`
- `http`
- `infra`
- `public`
- `tests`
- `typing`

#### Imports

- `__future__`
- `asyncpg`
- `core.exceptions`
- `data.audit`
- `data.documents`
- `data.emission_factors`
- `data.emissions_logs`
- `data.events`
- `decimal`
- `domain.factor`
- `domain.matching`
- `domain.workflow`
- `engines.ai_extraction`
- `engines.calculation`
- `engines.extraction`
- `engines.factor_matching`
- `engines.workflow`
- `http.server`
- `infra.audit_logger`
- `infra.event_bus`
- `infra.llm_client`
- `infra.search_index`
- `json`
- `pytest`
- `tests.integration.conftest`
- `threading`
- `typing`

### 4.140 `backend/tests/setup_test_data.py`

- **Module:** `backend.tests.setup_test_data`
- **Package:** `backend.tests`
- **Lines:** 599
- **Size:** 20,208 bytes
- **Categories:** Storage, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `get_supabase_admin()` (line 94)
- `safe_execute()` (line 111)
- `async create_auth_user()` (line 130)
- `async create_staff_profile()` (line 208)
- `async create_organization()` (line 253)
- `async add_org_member()` (line 304)
- `async create_beta_code()` (line 353)
- `async setup_test_data()` (line 399)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `Supabase`
- `beta_access_codes`
- `database`
- `datetime`
- `dotenv`
- `organization_members`
- `organizations`
- `pathlib`
- `role`
- `staff_profiles`
- `supabase`

#### Imports

- `asyncio`
- `database`
- `datetime`
- `dotenv`
- `os`
- `pathlib`
- `secrets`
- `string`
- `supabase`
- `sys`
- `uuid`

### 4.141 `backend/tests/setup_test_orgs.py`

- **Module:** `backend.tests.setup_test_orgs`
- **Package:** `backend.tests`
- **Lines:** 393
- **Size:** 12,910 bytes
- **Categories:** Storage, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async create_auth_user()` (line 84)
- `async create_staff_profile()` (line 117)
- `async create_organization()` (line 160)
- `async add_org_member()` (line 212)
- `async setup_test_data()` (line 248)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `database`
- `datetime`
- `email`
- `organization_members`
- `organizations`
- `pathlib`
- `staff_profiles`
- `supabase`

#### Imports

- `asyncio`
- `database`
- `datetime`
- `os`
- `pathlib`
- `random`
- `string`
- `supabase`
- `sys`

### 4.142 `backend/tests/test_all_endpoints.py`

- **Module:** `backend.tests.test_all_endpoints`
- **Package:** `backend.tests`
- **Lines:** 743
- **Size:** 35,356 bytes
- **Categories:** API, Storage
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `TestResults` (line 47; bases: `-`)
  - `__init__()` (line 48)
  - `add_result()` (line 55)
  - `print_summary()` (line 71)
- `APITester` (line 107; bases: `-`)
  - `__init__()` (line 108)
  - `get_supabase_client()` (line 115)
  - `async login()` (line 120)
  - `async authenticate_all()` (line 136)
  - `get_headers()` (line 151)
  - `async test_endpoint()` (line 161)
  - `async run_tests()` (line 211)

#### Top-Level Functions

- `async main()` (line 721)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `datetime`
- `dotenv`
- `financial`
- `org`
- `organizations`
- `pathlib`
- `profile`
- `supabase`
- `typing`

#### Imports

- `asyncio`
- `datetime`
- `dotenv`
- `httpx`
- `json`
- `os`
- `pathlib`
- `random`
- `supabase`
- `sys`
- `typing`

### 4.143 `backend/tests/test_api.py`

- **Module:** `backend.tests.test_api`
- **Package:** `backend.tests`
- **Lines:** 761
- **Size:** 33,184 bytes
- **Categories:** API, authentication / security
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `APITester` (line 25; bases: `-`)
  - `__init__()` (line 26)
  - `async __aenter__()` (line 40)
  - `async __aexit__()` (line 43)
  - `async authenticate()` (line 46)
  - `set_auth_headers()` (line 64)
  - `set_admin_headers()` (line 72)
  - `async test_endpoint()` (line 80)
  - `async test_all_endpoints()` (line 158)
  - `print_summary()` (line 691)

#### Top-Level Functions

- `async main()` (line 722)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `asset`
- `contact`
- `datetime`
- `emission`
- `employee`
- `facility`
- `financial`
- `glossary`
- `industry`
- `organization`
- `pathlib`
- `profile`
- `sustainability`
- `term`
- `tests`
- `typing`
- `user`

#### Imports

- `asyncio`
- `datetime`
- `httpx`
- `json`
- `os`
- `pathlib`
- `random`
- `string`
- `sys`
- `tests.auth_helper`
- `tests.config`
- `typing`

### 4.144 `backend/tests/test_api_simple.py`

- **Module:** `backend.tests.test_api_simple`
- **Package:** `backend.tests`
- **Lines:** 473
- **Size:** 19,296 bytes
- **Categories:** API, Storage
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `APITester` (line 66; bases: `-`)
  - `__init__()` (line 67)
  - `get_supabase_client()` (line 74)
  - `async login()` (line 84)
  - `async authenticate_all()` (line 114)
  - `async test_endpoint()` (line 138)
  - `async run_tests()` (line 211)
  - `print_summary()` (line 401)

#### Top-Level Functions

- `async main()` (line 443)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `dotenv`
- `pathlib`
- `supabase`
- `typing`
- `user`

#### Imports

- `asyncio`
- `dotenv`
- `httpx`
- `json`
- `os`
- `pathlib`
- `random`
- `supabase`
- `sys`
- `typing`

### 4.145 `backend/tests/test_auth_simple.py`

- **Module:** `backend.tests.test_auth_simple`
- **Package:** `backend.tests`
- **Lines:** 56
- **Size:** 1,674 bytes
- **Categories:** authentication / security
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async test_auth()` (line 13)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `dotenv`

#### Imports

- `asyncio`
- `dotenv`
- `httpx`
- `os`

### 4.146 `backend/tests/test_failing_endpoints.py`

- **Module:** `backend.tests.test_failing_endpoints`
- **Package:** `backend.tests`
- **Lines:** 330
- **Size:** 12,773 bytes
- **Categories:** AI extraction, API, Storage
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestResults` (line 44; bases: `-`)
  - `__init__()` (line 45)
  - `add_result()` (line 51)
  - `print_summary()` (line 65)
- `FailingEndpointTester` (line 85; bases: `-`)
  - `__init__()` (line 86)
  - `async login()` (line 92)
  - `async authenticate_all()` (line 119)
  - `get_headers()` (line 137)
  - `async test_endpoint()` (line 147)
  - `async run_tests()` (line 200)

#### Top-Level Functions

- `async main()` (line 308)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `dotenv`
- `pathlib`
- `supabase`
- `typing`

#### Imports

- `asyncio`
- `dotenv`
- `httpx`
- `json`
- `os`
- `pathlib`
- `supabase`
- `sys`
- `typing`

### 4.147 `backend/tests/unit/__init__.py`

- **Module:** `backend.tests.unit`
- **Package:** `backend.tests`
- **Lines:** 2
- **Size:** 49 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.148 `backend/tests/unit/domain/__init__.py`

- **Module:** `backend.tests.unit.domain`
- **Package:** `backend.tests.unit`
- **Lines:** 2
- **Size:** 75 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.149 `backend/tests/unit/domain/test_audit.py`

- **Module:** `backend.tests.unit.domain.test_audit`
- **Package:** `backend.tests.unit.domain`
- **Lines:** 89
- **Size:** 2,783 bytes
- **Categories:** AI extraction, audit / logging
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestAuditEntry` (line 34; bases: `-`)
  - `test_constructs()` (line 35)
  - `test_defaults()` (line 41)
  - `test_is_immutable()` (line 46)
- `TestAuditTrail` (line 52; bases: `-`)
  - `test_constructs()` (line 53)
  - `test_rejects_mismatched_correlation()` (line 60)
  - `test_by_action()` (line 67)
  - `test_by_entity()` (line 79)

#### Top-Level Functions

- `make_entry()` (line 12)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `domain`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `domain.audit`
- `pytest`

### 4.150 `backend/tests/unit/domain/test_benchmarking.py`

- **Module:** `backend.tests.unit.domain.test_benchmarking`
- **Package:** `backend.tests.unit.domain`
- **Lines:** 164
- **Size:** 6,184 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestBenchmarkAvailability` (line 31; bases: `-`)
  - `test_values()` (line 32)
- `TestBenchmarkMetric` (line 42; bases: `-`)
  - `test_constructs()` (line 43)
  - `test_is_available()` (line 62)
  - `test_is_immutable()` (line 72)
  - `test_rejects_empty_key()` (line 76)
  - `test_rejects_empty_label()` (line 80)
- `TestBenchmarkRequest` (line 85; bases: `-`)
  - `test_constructs_defaults()` (line 86)
  - `test_accepts_explicit_config()` (line 95)
  - `test_rejects_empty_organization()` (line 109)
  - `test_rejects_implausible_year()` (line 113)
  - `test_rejects_empty_metrics()` (line 117)
  - `test_rejects_unsupported_metric()` (line 121)
  - `test_rejects_unsupported_group()` (line 127)
  - `test_rejects_compare_year_out_of_range()` (line 133)
  - `test_rejects_compare_year_equals_reporting_year()` (line 139)
- `TestBenchmarkResult` (line 146; bases: `-`)
  - `test_metric_lookup()` (line 147)
  - `test_defaults()` (line 157)

#### Top-Level Functions

- `make_metric()` (line 21)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `decimal`
- `domain`

#### Imports

- `__future__`
- `dataclasses`
- `decimal`
- `domain.benchmarking`
- `pytest`

### 4.151 `backend/tests/unit/domain/test_calculation.py`

- **Module:** `backend.tests.unit.domain.test_calculation`
- **Package:** `backend.tests.unit.domain`
- **Lines:** 115
- **Size:** 3,877 bytes
- **Categories:** AI extraction, calculation, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestCalculationSnapshot` (line 59; bases: `-`)
  - `test_constructs()` (line 60)
  - `test_is_immutable()` (line 64)
  - `test_build_content_hash_is_deterministic()` (line 69)
  - `test_build_content_hash_changes_with_inputs()` (line 75)
  - `test_verify_reproducibility()` (line 84)
- `TestCalculationResult` (line 91; bases: `-`)
  - `test_constructs()` (line 92)
- `TestVerificationResult` (line 107; bases: `-`)
  - `test_matching()` (line 108)
  - `test_discrepancy()` (line 111)

#### Top-Level Functions

- `make_snapshot()` (line 19)
- `make_factor()` (line 43)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `decimal`
- `domain`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `decimal`
- `domain.calculation`
- `domain.factor`
- `pytest`

### 4.152 `backend/tests/unit/domain/test_document.py`

- **Module:** `backend.tests.unit.domain.test_document`
- **Package:** `backend.tests.unit.domain`
- **Lines:** 87
- **Size:** 2,537 bytes
- **Categories:** AI extraction, document processing
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestDocument` (line 22; bases: `-`)
  - `test_constructs()` (line 23)
  - `test_is_immutable()` (line 36)
- `TestExtractionResult` (line 51; bases: `-`)
  - `_result()` (line 52)
  - `test_constructs()` (line 65)
  - `test_rejects_bad_aggregate_confidence()` (line 71)
  - `test_rejects_bad_page_confidence()` (line 75)
  - `test_extraction_field()` (line 82)

#### Top-Level Functions

- `utc_now()` (line 18)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `domain`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `domain.document`
- `pytest`

### 4.153 `backend/tests/unit/domain/test_factor.py`

- **Module:** `backend.tests.unit.domain.test_factor`
- **Package:** `backend.tests.unit.domain`
- **Lines:** 154
- **Size:** 5,571 bytes
- **Categories:** AI extraction, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestEmissionFactor` (line 40; bases: `-`)
  - `test_constructs()` (line 41)
  - `test_is_immutable()` (line 47)
  - `test_rejects_negative_multiplier()` (line 52)
  - `test_rejects_empty_id()` (line 56)
  - `test_rejects_empty_activity()` (line 60)
  - `test_rejects_implausible_year()` (line 64)
  - `test_calculate_emissions_matching_unit()` (line 68)
  - `test_calculate_emissions_rounds_to_six_dp()` (line 73)
  - `test_calculate_emissions_unitless_factor_accepts_any_unit()` (line 79)
  - `test_calculate_emissions_unit_mismatch_raises()` (line 84)
  - `test_calculate_emissions_rejects_negative_quantity()` (line 90)
  - `test_with_new_year_returns_copy()` (line 95)
- `TestFactorSet` (line 104; bases: `-`)
  - `_set()` (line 105)
  - `test_find_by_natural_key()` (line 133)
  - `test_find_by_natural_key_missing()` (line 141)
  - `test_search_by_activity_substring_case_insensitive()` (line 144)
  - `test_search_by_activity_with_unit_filter()` (line 149)

#### Top-Level Functions

- `make_factor()` (line 14)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `dataclasses`
- `datetime`
- `decimal`
- `domain`

#### Imports

- `__future__`
- `core.exceptions`
- `dataclasses`
- `datetime`
- `decimal`
- `domain.factor`
- `pytest`

### 4.154 `backend/tests/unit/domain/test_matching.py`

- **Module:** `backend.tests.unit.domain.test_matching`
- **Package:** `backend.tests.unit.domain`
- **Lines:** 169
- **Size:** 5,571 bytes
- **Categories:** AI extraction, emission factors, factor matching
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestMatchRequest` (line 38; bases: `-`)
  - `test_constructs()` (line 39)
  - `test_is_immutable()` (line 45)
  - `test_rejects_empty_activity()` (line 52)
  - `test_rejects_max_stages_below_one()` (line 56)
  - `test_rejects_implausible_year()` (line 62)
- `TestStageResult` (line 67; bases: `-`)
  - `test_matched_requires_factor()` (line 68)
  - `test_unmatched_must_not_have_factor()` (line 72)
  - `test_confidence_range()` (line 76)
  - `test_score_range()` (line 80)
  - `test_matched()` (line 84)
- `TestMatchResult` (line 99; bases: `-`)
  - `test_no_match_helper()` (line 100)
  - `test_matched_must_include_factor()` (line 113)
  - `test_invalid_status_rejected()` (line 117)
  - `test_is_immutable()` (line 121)
- `TestFactorAlias` (line 127; bases: `-`)
  - `test_constructs()` (line 128)
- `TestMatchingPipelineConfig` (line 141; bases: `-`)
  - `test_defaults()` (line 142)
  - `test_threshold_range()` (line 148)
  - `test_max_suggestions_range()` (line 152)
- `TestMatchingStageContract` (line 157; bases: `-`)
  - `test_protocol_shape()` (line 160)
  - `test_stage_is_abstract()` (line 166)

#### Top-Level Functions

- `make_factor()` (line 23)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `decimal`
- `domain`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `decimal`
- `domain.factor`
- `domain.matching`
- `pytest`

### 4.155 `backend/tests/unit/domain/test_organization.py`

- **Module:** `backend.tests.unit.domain.test_organization`
- **Package:** `backend.tests.unit.domain`
- **Lines:** 73
- **Size:** 1,978 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestOrganization` (line 16; bases: `-`)
  - `test_constructs()` (line 17)
  - `test_is_immutable()` (line 27)
- `TestFacility` (line 35; bases: `-`)
  - `test_constructs()` (line 36)
- `TestAsset` (line 47; bases: `-`)
  - `test_constructs()` (line 48)
- `TestOrganizationMetadata` (line 59; bases: `-`)
  - `test_defaults_are_none()` (line 60)
  - `test_constructs()` (line 65)

#### Top-Level Functions

- `utc_now()` (line 12)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `domain`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `domain.organization`
- `pytest`

### 4.156 `backend/tests/unit/domain/test_provider.py`

- **Module:** `backend.tests.unit.domain.test_provider`
- **Package:** `backend.tests.unit.domain`
- **Lines:** 199
- **Size:** 6,235 bytes
- **Categories:** AI extraction, factor provider
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestProviderInfo` (line 45; bases: `-`)
  - `test_constructs()` (line 46)
- `TestImportBatch` (line 62; bases: `-`)
  - `test_constructs()` (line 63)
  - `test_rejects_unknown_status()` (line 68)
  - `test_rejects_negative_row_count()` (line 72)
  - `test_activate_returns_active_copy()` (line 76)
  - `test_rollback_marks_rolled_back()` (line 84)
  - `test_is_immutable()` (line 92)
- `TestImportError` (line 98; bases: `-`)
  - `test_constructs()` (line 99)
  - `test_rejects_unknown_severity()` (line 103)
  - `test_rejects_row_zero()` (line 107)
- `TestDiscovery` (line 112; bases: `-`)
  - `test_discovery_requires_sheets()` (line 113)
  - `test_discovery_constructs()` (line 124)
  - `test_raw_row()` (line 143)
  - `test_normalised_factor()` (line 151)
  - `test_normalised_factor_rejects_negative_multiplier()` (line 161)
- `TestImportResult` (line 171; bases: `-`)
  - `test_constructs()` (line 172)
- `TestProviderVersion` (line 186; bases: `-`)
  - `test_constructs()` (line 187)

#### Top-Level Functions

- `make_batch()` (line 22)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `domain`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `domain.provider`
- `pytest`

### 4.157 `backend/tests/unit/domain/test_report.py`

- **Module:** `backend.tests.unit.domain.test_report`
- **Package:** `backend.tests.unit.domain`
- **Lines:** 101
- **Size:** 2,997 bytes
- **Categories:** AI extraction, database / repository, reporting
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestReportSection` (line 21; bases: `-`)
  - `test_constructs()` (line 22)
- `TestReportTemplate` (line 29; bases: `-`)
  - `test_constructs()` (line 30)
- `TestReportRequest` (line 42; bases: `-`)
  - `test_constructs()` (line 43)
  - `test_rejects_implausible_year()` (line 50)
  - `test_is_immutable()` (line 54)
- `TestGeneratedReport` (line 62; bases: `-`)
  - `test_constructs()` (line 63)
  - `test_rejects_negative_size()` (line 76)
  - `test_rejects_negative_page_count()` (line 89)

#### Top-Level Functions

- `utc_now()` (line 17)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `domain`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `domain.report`
- `pytest`

### 4.158 `backend/tests/unit/domain/test_validation.py`

- **Module:** `backend.tests.unit.domain.test_validation`
- **Package:** `backend.tests.unit.domain`
- **Lines:** 157
- **Size:** 5,279 bytes
- **Categories:** AI extraction, validation / QA
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestValidationSeverity` (line 29; bases: `-`)
  - `test_values()` (line 30)
- `TestValidationIssue` (line 36; bases: `-`)
  - `test_constructs()` (line 37)
  - `test_error_is_blocking()` (line 44)
  - `test_warning_is_not_blocking()` (line 47)
  - `test_is_immutable()` (line 51)
  - `test_rejects_empty_code()` (line 55)
  - `test_rejects_empty_message()` (line 59)
  - `test_rejects_empty_entity_type()` (line 69)
  - `test_rejects_empty_entity_id()` (line 79)
- `TestValidationReport` (line 84; bases: `-`)
  - `test_empty_report_is_ok()` (line 85)
  - `test_ok_false_with_error()` (line 94)
  - `test_ok_true_with_warnings_only()` (line 98)
  - `test_counts_by_severity()` (line 104)
  - `test_blocking_errors()` (line 114)
  - `test_merge_combines_issues()` (line 125)
  - `test_merge_is_immutable()` (line 131)
- `TestValidationRequest` (line 140; bases: `-`)
  - `test_constructs()` (line 141)
  - `test_rejects_empty_organization()` (line 150)
  - `test_rejects_implausible_year()` (line 154)

#### Top-Level Functions

- `make_issue()` (line 15)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `domain`

#### Imports

- `__future__`
- `dataclasses`
- `domain.validation`
- `pytest`

### 4.159 `backend/tests/unit/domain/test_workflow.py`

- **Module:** `backend.tests.unit.domain.test_workflow`
- **Package:** `backend.tests.unit.domain`
- **Lines:** 236
- **Size:** 7,971 bytes
- **Categories:** AI extraction, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestWorkflowDefinition` (line 40; bases: `-`)
  - `test_can_transition_allowed()` (line 41)
  - `test_can_transition_wildcard()` (line 50)
  - `test_validate_state()` (line 59)
  - `test_document_pipeline_is_well_formed()` (line 64)
  - `test_transition_record()` (line 76)
- `TestDocumentEvents` (line 101; bases: `-`)
  - `test_document_uploaded()` (line 102)
  - `test_extraction_requested()` (line 113)
  - `test_extraction_completed()` (line 118)
  - `test_fields_extracted()` (line 126)
- `TestCalculationEvents` (line 137; bases: `-`)
  - `test_calculation_requested()` (line 138)
  - `test_calculation_completed()` (line 145)
- `TestReportEvent` (line 155; bases: `-`)
  - `test_report_generated()` (line 156)
- `TestImportEvents` (line 167; bases: `-`)
  - `test_import_started()` (line 168)
  - `test_import_completed()` (line 173)
  - `test_import_rolled_back()` (line 179)
- `TestMatchEvents` (line 184; bases: `-`)
  - `test_factor_matched()` (line 185)
  - `test_factor_not_found()` (line 191)
- `TestStateChangeEvents` (line 196; bases: `-`)
  - `test_validation_failed()` (line 197)
  - `test_workflow_state_changed()` (line 207)
- `TestEventImmutability` (line 220; bases: `-`)
  - `test_events_are_frozen()` (line 221)
  - `test_events_are_keyword_only()` (line 226)
- `TestSaga` (line 231; bases: `-`)
  - `test_saga_is_abstract()` (line 232)

#### Top-Level Functions

- `utc_now()` (line 36)
- `make_event()` (line 87)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `datetime`
- `decimal`
- `domain`
- `typing`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `decimal`
- `domain.workflow`
- `pytest`
- `typing`

### 4.160 `backend/tests/unit/engines/__init__.py`

- **Module:** `backend.tests.unit.engines`
- **Package:** `backend.tests.unit`
- **Lines:** 2
- **Size:** 50 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.161 `backend/tests/unit/engines/test_ai_extraction.py`

- **Module:** `backend.tests.unit.engines.test_ai_extraction`
- **Package:** `backend.tests.unit.engines`
- **Lines:** 244
- **Size:** 9,080 bytes
- **Categories:** AI extraction, audit / logging, document processing, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `_MemoryDocSink` (line 34; bases: `-`)
  - `__init__()` (line 35)
  - `async update_status()` (line 38)
- `_AuditSink` (line 43; bases: `-`)
  - `__init__()` (line 44)
  - `async log_action()` (line 47)
- `TestExtractFields` (line 99; bases: `-`)
  - `async test_parses_fields_from_llm_json()` (line 100)
  - `async test_strips_code_fence()` (line 114)
  - `async test_missing_fields_are_omitted()` (line 124)
  - `async test_custom_fields_subset()` (line 130)
  - `async test_empty_text_raises_and_marks_failed()` (line 138)
  - `async test_status_transitions_on_success()` (line 147)
- `TestErrors` (line 159; bases: `-`)
  - `async test_invalid_json_raises_and_marks_failed()` (line 160)
  - `async test_non_object_response_raises()` (line 169)
  - `async test_malformed_field_raises()` (line 175)
  - `async test_confidence_out_of_range_raises()` (line 181)
  - `async test_confidence_not_a_number_raises()` (line 189)
- `TestSideEffects` (line 198; bases: `-`)
  - `async test_publishes_fields_extracted_event()` (line 199)
  - `async capture()` (line 203)
  - `async test_audits_extraction()` (line 219)
  - `async test_failing_event_bus_does_not_break_extraction()` (line 232)
  - `_BrokenBus()` (line 233)

#### Top-Level Functions

- `make_document()` (line 21)
- `_llm()` (line 79)
- `transport()` (line 80)
- `make_engine()` (line 91)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `datetime`
- `domain`
- `engines`
- `infra`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `datetime`
- `domain.audit`
- `domain.document`
- `domain.workflow`
- `engines.ai_extraction`
- `engines.extraction`
- `infra.event_bus`
- `infra.llm_client`
- `json`
- `pytest`
- `typing`
- `uuid`

### 4.162 `backend/tests/unit/engines/test_benchmarking.py`

- **Module:** `backend.tests.unit.engines.test_benchmarking`
- **Package:** `backend.tests.unit.engines`
- **Lines:** 731
- **Size:** 32,966 bytes
- **Categories:** AI extraction, audit / logging, calculation, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `_FakeLogs` (line 95; bases: `-`)
  - `__init__()` (line 98)
  - `_in_period()` (line 103)
  - `async find_by_org()` (line 110)
  - `async aggregate()` (line 114)
  - `_group_key()` (line 137)
- `_FakeOrgs` (line 151; bases: `-`)
  - `__init__()` (line 152)
  - `async get_metadata()` (line 160)
  - `async get_facilities()` (line 163)
- `_FakeFactors` (line 167; bases: `-`)
  - `__init__()` (line 168)
  - `async get()` (line 172)
- `_AuditSink` (line 177; bases: `-`)
  - `__init__()` (line 178)
  - `async log_action()` (line 181)
- `TestB1YearOverYear` (line 219; bases: `-`)
  - `async test_total_yoy_delta_and_pct()` (line 220)
  - `async test_decrease_yoy()` (line 244)
  - `async test_multiple_reporting_periods()` (line 260)
- `TestB2Facility` (line 279; bases: `-`)
  - `async test_facility_comparison_and_yoy()` (line 280)
  - `async test_facility_without_data()` (line 311)
  - `async test_facility_filter()` (line 329)
- `TestB3Scope` (line 350; bases: `-`)
  - `async test_scope_breakdown_and_yoy()` (line 351)
- `TestB4PerFte` (line 377; bases: `-`)
  - `async test_per_fte_normal()` (line 378)
- `TestB5PerArea` (line 396; bases: `-`)
  - `async test_per_area_normal()` (line 397)
- `TestB6PerRevenue` (line 413; bases: `-`)
  - `async test_per_revenue_normal()` (line 414)
- `TestB7ActivityIntensity` (line 430; bases: `-`)
  - `async test_activity_intensity_and_yoy()` (line 431)
  - `async test_activity_intensity_incompatible_units()` (line 455)
  - `async test_activity_intensity_zero_quantity()` (line 471)
- `TestB8InternalCapabilities` (line 486; bases: `-`)
  - `async test_month_grouping()` (line 487)
  - `async test_asset_grouping()` (line 502)
- `TestDenominatorRule` (line 518; bases: `-`)
  - `async test_missing_organization_metadata()` (line 519)
  - `async test_missing_specific_denominator()` (line 536)
  - `async test_zero_denominator()` (line 550)
  - `async test_invalid_negative_denominator()` (line 562)
- `TestInsufficientData` (line 575; bases: `-`)
  - `async test_empty_reporting_period_raises()` (line 576)
  - `async test_empty_baseline_year_noted()` (line 583)
  - `async test_no_facility_data_is_insufficient()` (line 598)
- `TestProvenance` (line 613; bases: `-`)
  - `async test_all_seai_is_co2()` (line 614)
  - `async test_all_defra_is_co2e()` (line 626)
  - `async test_mixed_provenance_is_not_silently_relabelled()` (line 637)
  - `async test_seai_per_fte_unit_preserves_co2()` (line 656)
- `TestNoCrossTenantLeakage` (line 669; bases: `-`)
  - `async test_org_a_benchmark_uses_only_org_a_data()` (line 670)
- `TestNoDatabaseSideEffects` (line 685; bases: `-`)
  - `async test_audits_benchmark()` (line 686)
  - `async test_read_only_repository_surface()` (line 707)

#### Top-Level Functions

- `make_factor()` (line 32)
- `make_seai()` (line 49)
- `make_log()` (line 64)
- `make_metadata()` (line 81)
- `make_facility()` (line 91)
- `status_of()` (line 213)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `datetime`
- `decimal`
- `domain`
- `the`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `core.types`
- `datetime`
- `decimal`
- `domain.audit`
- `domain.benchmarking`
- `domain.calculation`
- `domain.factor`
- `domain.organization`
- `engines.benchmarking`
- `pytest`
- `typing`
- `uuid`

### 4.163 `backend/tests/unit/engines/test_calculation.py`

- **Module:** `backend.tests.unit.engines.test_calculation`
- **Package:** `backend.tests.unit.engines`
- **Lines:** 451
- **Size:** 16,680 bytes
- **Categories:** AI extraction, audit / logging, calculation, emission factors, factor matching, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `_MemorySink` (line 79; bases: `-`)
  - `__init__()` (line 82)
  - `async save_snapshot()` (line 87)
  - `async create()` (line 104)
  - `async save()` (line 132)
- `_AuditSink` (line 137; bases: `-`)
  - `__init__()` (line 140)
  - `async log_action()` (line 143)
- `TestCalculationRequest` (line 175; bases: `-`)
  - `test_constructs()` (line 176)
  - `test_default_methodology_is_direct_multiply()` (line 181)
  - `test_rejects_empty_match_request_id()` (line 184)
  - `test_rejects_empty_organization()` (line 188)
  - `test_rejects_negative_quantity()` (line 192)
  - `test_rejects_empty_unit()` (line 196)
  - `test_rejects_implausible_year()` (line 200)
  - `test_rejects_unknown_methodology()` (line 204)
  - `test_from_match_result_builds_request()` (line 208)
  - `test_from_match_result_rejects_no_match()` (line 230)
- `TestCalculationEngine` (line 245; bases: `-`)
  - `async test_calculate_produces_correct_co2e()` (line 246)
  - `async test_calculate_rounds_to_result_precision()` (line 255)
  - `async test_snapshot_fields_populated()` (line 264)
  - `async test_calculate_persists_snapshot()` (line 284)
  - `async test_calculate_creates_log_when_no_log_id()` (line 292)
  - `async test_calculate_updates_existing_log()` (line 303)
  - `async test_unit_mismatch_raises()` (line 324)
  - `async test_negative_quantity_raises()` (line 331)
  - `async test_snapshot_persistence_failure_propagates()` (line 338)
  - `async test_custom_algorithm_version()` (line 345)
- `TestVerification` (line 353; bases: `-`)
  - `async test_verify_matches_computed_snapshot()` (line 354)
  - `async test_verify_detects_tampered_hash()` (line 363)
  - `async test_verify_detects_incorrect_result()` (line 373)
- `TestEngineSideEffects` (line 384; bases: `-`)
  - `async test_publishes_requested_and_completed_events()` (line 385)
  - `async capture()` (line 389)
  - `async test_audits_calculation()` (line 412)
  - `async test_failing_event_bus_does_not_break_calculation()` (line 430)
  - `_BrokenBus()` (line 431)
  - `async test_no_side_effects_when_unwired()` (line 443)

#### Top-Level Functions

- `make_factor()` (line 32)
- `make_request()` (line 55)
- `take()` (line 56)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `datetime`
- `decimal`
- `domain`
- `engines`
- `infra`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `dataclasses`
- `datetime`
- `decimal`
- `domain.audit`
- `domain.calculation`
- `domain.factor`
- `domain.matching`
- `domain.workflow`
- `engines.calculation`
- `infra.event_bus`
- `pytest`
- `typing`
- `uuid`

### 4.164 `backend/tests/unit/engines/test_extraction.py`

- **Module:** `backend.tests.unit.engines.test_extraction`
- **Package:** `backend.tests.unit.engines`
- **Lines:** 214
- **Size:** 7,737 bytes
- **Categories:** AI extraction, audit / logging, document processing, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `_MemoryDocSink` (line 37; bases: `-`)
  - `__init__()` (line 38)
  - `async update_status()` (line 41)
- `_AuditSink` (line 46; bases: `-`)
  - `__init__()` (line 47)
  - `async log_action()` (line 50)
- `TestExtract` (line 88; bases: `-`)
  - `async test_splits_pages()` (line 89)
  - `async test_single_page_without_separator()` (line 102)
  - `async test_extracts_fields()` (line 108)
  - `async test_extracts_tables()` (line 117)
  - `async test_empty_text_raises_and_marks_failed()` (line 126)
  - `async test_status_transitions_on_success()` (line 133)
  - `async test_custom_field_patterns_override_generic()` (line 142)
  - `async test_constructor_validation()` (line 156)
- `TestSideEffects` (line 165; bases: `-`)
  - `async test_publishes_extraction_events()` (line 166)
  - `async capture()` (line 170)
  - `async test_audits_extraction()` (line 194)
  - `async test_failing_event_bus_does_not_break_extraction()` (line 205)
  - `_BrokenBus()` (line 206)

#### Top-Level Functions

- `make_document()` (line 24)
- `make_engine()` (line 82)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `datetime`
- `domain`
- `engines`
- `infra`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `datetime`
- `domain.audit`
- `domain.document`
- `domain.workflow`
- `engines.extraction`
- `infra.event_bus`
- `pytest`
- `re`
- `typing`
- `uuid`

### 4.165 `backend/tests/unit/engines/test_factor_matching.py`

- **Module:** `backend.tests.unit.engines.test_factor_matching`
- **Package:** `backend.tests.unit.engines`
- **Lines:** 323
- **Size:** 11,579 bytes
- **Categories:** AI extraction, audit / logging, emission factors, factor matching, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestPipelineBuilder` (line 95; bases: `-`)
  - `test_builds_default_stage_order()` (line 96)
  - `test_unknown_stage_raises()` (line 107)
  - `test_custom_stage_order()` (line 112)
  - `test_semantic_enabled_propagates()` (line 117)
- `TestEngineMatchFlow` (line 125; bases: `-`)
  - `async test_exact_match_short_circuits()` (line 126)
  - `async test_natural_key_match()` (line 138)
  - `async test_keyword_fallback_after_exact_miss()` (line 152)
  - `async test_no_match_returns_suggestions()` (line 160)
  - `async test_ambiguous_exact_returns_ambiguous()` (line 176)
  - `async test_max_stages_limits_pipeline()` (line 188)
  - `async test_empty_stages_raise()` (line 197)
- `TestEngineSideEffects` (line 202; bases: `-`)
  - `async test_publishes_factor_matched_event()` (line 203)
  - `async capture()` (line 207)
  - `async test_publishes_factor_not_found_event()` (line 226)
  - `async capture()` (line 230)
  - `async test_audits_match_outcome()` (line 246)
  - `async test_failing_event_bus_does_not_break_match()` (line 263)
  - `_BrokenBus()` (line 264)
- `_MemorySink` (line 276; bases: `-`)
  - `__init__()` (line 279)
  - `async record()` (line 282)
  - `async query()` (line 286)
  - `async log_action()` (line 292)

#### Top-Level Functions

- `make_factor()` (line 24)
- `make_index()` (line 54)
- `make_request()` (line 60)
- `make_engine()` (line 74)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `datetime`
- `decimal`
- `domain`
- `engines`
- `infra`
- `typing`

#### Imports

- `__future__`
- `datetime`
- `decimal`
- `domain.audit`
- `domain.factor`
- `domain.matching`
- `domain.workflow`
- `engines.factor_matching`
- `engines.matching_stages`
- `infra.event_bus`
- `infra.search_index`
- `pytest`
- `typing`
- `uuid`

### 4.166 `backend/tests/unit/engines/test_matching_stages.py`

- **Module:** `backend.tests.unit.engines.test_matching_stages`
- **Package:** `backend.tests.unit.engines`
- **Lines:** 349
- **Size:** 12,561 bytes
- **Categories:** AI extraction, emission factors, factor matching
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestExactMatchStage` (line 77; bases: `-`)
  - `async test_exact_single_match()` (line 78)
  - `async test_exact_case_insensitive()` (line 89)
  - `async test_exact_no_match()` (line 97)
  - `async test_exact_ambiguous_without_unit()` (line 103)
  - `async test_unit_filter_resolves_ambiguity()` (line 116)
- `TestNaturalKeyStage` (line 132; bases: `-`)
  - `async test_natural_key_hit()` (line 133)
  - `async test_natural_key_miss()` (line 147)
  - `async test_natural_key_null_unit_scope()` (line 155)
- `TestKeywordSearchStage` (line 165; bases: `-`)
  - `async test_full_token_match()` (line 166)
  - `async test_below_threshold_is_not_matched()` (line 176)
  - `async test_unit_filter_limits_retrieval()` (line 184)
  - `test_min_confidence_validation()` (line 199)
- `TestAliasMatchStage` (line 204; bases: `-`)
  - `async _resolver()` (line 205)
  - `async resolve()` (line 206)
  - `async test_alias_match_is_definitive()` (line 213)
  - `async test_unresolved_alias()` (line 223)
  - `async test_no_resolver_configured()` (line 230)
  - `async test_repository_alias_resolver_adapts_repo()` (line 237)
  - `_StubRepo()` (line 247)
  - `async test_repository_alias_resolver_global_fallback()` (line 263)
  - `_StubRepo()` (line 272)
- `TestFuzzyMatchStage` (line 289; bases: `-`)
  - `async test_high_similarity_matches()` (line 290)
  - `async test_low_similarity_does_not_match()` (line 301)
  - `test_threshold_validation()` (line 309)
- `TestSemanticMatchStage` (line 314; bases: `-`)
  - `async test_disabled_does_not_match()` (line 315)
  - `async test_enabled_without_scorer_does_not_match()` (line 322)
  - `async test_enabled_with_scorer_matches()` (line 329)
  - `scorer()` (line 330)
  - `async test_enabled_with_scorer_below_threshold()` (line 339)
  - `scorer()` (line 340)

#### Top-Level Functions

- `make_factor()` (line 25)
- `make_index()` (line 55)
- `make_request()` (line 61)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `datetime`
- `decimal`
- `domain`
- `engines`
- `infra`
- `typing`

#### Imports

- `__future__`
- `datetime`
- `decimal`
- `domain.factor`
- `domain.matching`
- `engines.matching_stages`
- `infra.search_index`
- `pytest`
- `typing`
- `uuid`

### 4.167 `backend/tests/unit/engines/test_validation.py`

- **Module:** `backend.tests.unit.engines.test_validation`
- **Package:** `backend.tests.unit.engines`
- **Lines:** 821
- **Size:** 33,229 bytes
- **Categories:** AI extraction, audit / logging, calculation, emission factors, factor matching, validation / QA, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `_FakeLogs` (line 162; bases: `-`)
  - `__init__()` (line 163)
  - `async find_by_org()` (line 166)
- `_FakeOrgs` (line 170; bases: `-`)
  - `__init__()` (line 171)
  - `async get()` (line 183)
  - `async get_metadata()` (line 186)
  - `async get_facilities()` (line 189)
  - `async get_assets()` (line 192)
- `_FakeFactors` (line 196; bases: `-`)
  - `__init__()` (line 197)
  - `async get()` (line 200)
- `_AuditSink` (line 204; bases: `-`)
  - `__init__()` (line 207)
  - `async log_action()` (line 210)
- `TestA1Input` (line 270; bases: `-`)
  - `test_valid_input()` (line 271)
  - `test_empty_activity_error()` (line 279)
  - `test_negative_quantity_error()` (line 287)
  - `test_implausible_year_error()` (line 295)
  - `test_missing_unit_when_factor_requires_error()` (line 303)
  - `test_seai_co2_only_input_valid()` (line 312)
- `TestA2Reproducibility` (line 322; bases: `-`)
  - `test_valid_snapshot_ok()` (line 323)
  - `test_co2e_mismatch_error()` (line 328)
  - `test_rounding_tolerance_warning()` (line 335)
  - `test_empty_hash_error()` (line 345)
  - `test_hash_mismatch_error()` (line 352)
- `TestA3Match` (line 360; bases: `-`)
  - `test_matched_correct_ok()` (line 361)
  - `test_incorrect_factor_country_error()` (line 369)
  - `test_incorrect_provider_error()` (line 378)
  - `test_unit_mismatch_error()` (line 388)
  - `test_no_match_warning()` (line 397)
  - `test_low_confidence_warning()` (line 404)
  - `test_matched_without_factor_error()` (line 414)
- `TestA4ScopeUnit` (line 423; bases: `-`)
  - `test_valid_log_ok()` (line 424)
  - `test_unit_mismatch_error()` (line 431)
  - `test_scope_mismatch_error()` (line 439)
  - `test_unknown_scope_error()` (line 447)
  - `test_missing_scope_warning()` (line 455)
  - `test_family_mismatch_warning()` (line 463)
  - `test_seai_electricity_scope2_has_no_family_warning()` (line 471)
- `TestA5SnapshotProvenance` (line 480; bases: `-`)
  - `test_seai_snapshot_with_provenance_ok()` (line 481)
  - `test_seai_snapshot_missing_provenance_warning()` (line 492)
  - `test_batch_mismatch_error()` (line 500)
  - `test_source_mismatch_error()` (line 508)
  - `test_provenance_context_carries_gas_coverage()` (line 520)
- `TestA6Integrity` (line 529; bases: `-`)
  - `test_valid_log_ok()` (line 530)
  - `test_negative_quantity_error()` (line 536)
  - `test_negative_co2e_error()` (line 543)
  - `test_snapshot_link_missing_warning()` (line 550)
  - `async test_orphan_factor_error()` (line 557)
- `TestA7Period` (line 566; bases: `-`)
  - `test_year_mismatch_warning()` (line 567)
  - `test_out_of_period_warning_when_not_strict()` (line 574)
  - `test_out_of_period_error_when_strict()` (line 582)
- `TestA8Org` (line 591; bases: `-`)
  - `async test_org_not_found_error()` (line 592)
  - `async test_inactive_org_error()` (line 598)
  - `async test_metadata_missing_warning()` (line 606)
  - `async test_metadata_present_no_warning()` (line 614)
  - `async test_entity_not_in_org_error()` (line 624)
- `TestA9Verify` (line 644; bases: `-`)
  - `async test_verify_valid_snapshots_ok()` (line 645)
  - `async test_verify_detects_tampered_snapshot()` (line 652)
- `TestGasCoverage` (line 661; bases: `-`)
  - `test_defra_is_co2e()` (line 662)
  - `test_seai_is_co2()` (line 665)
  - `test_co2_label_suffix_detected()` (line 668)
- `TestSeaiCo2` (line 673; bases: `-`)
  - `async test_valid_seai_calculation_validates_clean()` (line 674)
  - `async test_seai_ie_match_is_valid()` (line 699)
  - `async test_composite_validation_scope_filter()` (line 709)
- `TestStrictAndSideEffects` (line 729; bases: `-`)
  - `async test_strict_raises_validation_failed_error()` (line 730)
  - `async test_non_strict_returns_report()` (line 745)
  - `async test_publishes_validation_failed_event()` (line 761)
  - `async capture()` (line 766)
  - `async test_audits_validation()` (line 790)
  - `test_constructor_requires_repos()` (line 809)

#### Top-Level Functions

- `make_factor()` (line 35)
- `make_seai_factor()` (line 52)
- `make_log()` (line 67)
- `make_snapshot()` (line 84)
- `setattr_log()` (line 115)
- `make_org()` (line 128)
- `make_metadata()` (line 138)
- `make_facility()` (line 148)
- `make_asset()` (line 152)
- `codes()` (line 242)
- `make_match_request()` (line 246)
- `make_match_result()` (line 258)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `datetime`
- `decimal`
- `domain`
- `infra`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `core.types`
- `dataclasses`
- `datetime`
- `decimal`
- `domain.audit`
- `domain.calculation`
- `domain.factor`
- `domain.matching`
- `domain.organization`
- `domain.validation`
- `domain.workflow`
- `engines.validation`
- `infra.event_bus`
- `pytest`
- `typing`
- `uuid`

### 4.168 `backend/tests/unit/engines/test_workflow.py`

- **Module:** `backend.tests.unit.engines.test_workflow`
- **Package:** `backend.tests.unit.engines`
- **Lines:** 649
- **Size:** 23,298 bytes
- **Categories:** AI extraction, audit / logging, calculation, document processing, emission factors, factor matching, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `FakeDocumentRepo` (line 89; bases: `-`)
  - `__init__()` (line 90)
  - `async get()` (line 94)
  - `async update_status()` (line 97)
- `FakeEventRepo` (line 114; bases: `-`)
  - `__init__()` (line 115)
  - `async store()` (line 118)
- `FakeExtractionEngine` (line 123; bases: `-`)
  - `__init__()` (line 124)
  - `async extract()` (line 128)
- `FakeAIExtractionEngine` (line 141; bases: `-`)
  - `__init__()` (line 142)
  - `async extract_fields()` (line 152)
- `FakeMatchingEngine` (line 161; bases: `-`)
  - `__init__()` (line 162)
  - `async match()` (line 167)
- `FakeCalculationEngine` (line 187; bases: `-`)
  - `__init__()` (line 188)
  - `async calculate()` (line 192)
- `Harness` (line 223; bases: `-`)
  - `__init__()` (line 226)
  - `state_sequence()` (line 262)

#### Top-Level Functions

- `make_document()` (line 46)
- `make_factor()` (line 59)
- `ai_fields()` (line 74)
- `test_constructor_requires_all_dependencies()` (line 273)
- `test_register_handlers_requires_event_bus()` (line 315)
- `test_invoice_activity_resolver_maps_fields()` (line 334)
- `test_invoice_activity_resolver_uses_fallbacks()` (line 358)
- `test_invoice_activity_resolver_rejects_missing_activity()` (line 369)
- `async test_process_document_completes_full_pipeline()` (line 381)
- `async test_process_document_persists_ordered_state_sequence()` (line 406)
- `async test_submit_document_returns_early_when_unhandled()` (line 441)
- `async test_low_ai_confidence_routes_to_manual_review()` (line 459)
- `async test_missing_activity_routes_to_manual_review()` (line 474)
- `async test_no_match_routes_to_manual_review()` (line 492)
- `async test_auto_review_false_stops_at_customer_review()` (line 506)
- `async test_extraction_failure_is_retried_then_completes()` (line 524)
- `async test_exhausted_retries_fail_document_and_raise()` (line 535)
- `async test_ai_failure_is_retried_then_completes()` (line 549)
- `async test_resubmit_after_completion_is_idempotent()` (line 559)
- `async test_resubmit_while_active_raises()` (line 577)
- `async test_document_already_processed_cannot_restart()` (line 589)
- `async test_registered_handlers_drive_submitted_pipeline()` (line 603)
- `async test_register_handlers_is_idempotent()` (line 621)
- `async test_duplicate_fields_event_does_not_duplicate_calculation()` (line 628)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `datetime`
- `decimal`
- `domain`
- `engines`
- `infra`
- `typing`

#### Imports

- `__future__`
- `core.exceptions`
- `datetime`
- `decimal`
- `domain.calculation`
- `domain.document`
- `domain.factor`
- `domain.matching`
- `domain.workflow`
- `engines.calculation`
- `engines.workflow`
- `infra.event_bus`
- `pytest`
- `typing`
- `uuid`

### 4.169 `backend/tests/unit/infra/__init__.py`

- **Module:** `backend.tests.unit.infra`
- **Package:** `backend.tests.unit`
- **Lines:** 2
- **Size:** 57 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.170 `backend/tests/unit/infra/test_audit_logger.py`

- **Module:** `backend.tests.unit.infra.test_audit_logger`
- **Package:** `backend.tests.unit.infra`
- **Lines:** 276
- **Size:** 9,039 bytes
- **Categories:** AI extraction, audit / logging
- **V3 impact:** **NO CHANGE**

#### Classes

- `_MemorySink` (line 14; bases: `-`)
  - `__init__()` (line 17)
  - `async record()` (line 21)
  - `async query()` (line 41)
- `TestLogAction` (line 55; bases: `-`)
  - `async test_log_action_uses_default_actor()` (line 56)
  - `async test_log_action_explicit_actor_and_reason()` (line 69)
  - `async test_query_delegates_to_sink()` (line 88)
- `TestAuditDecoratorSuccess` (line 102; bases: `-`)
  - `async test_records_success_with_arg_resolution()` (line 103)
  - `async process()` (line 112)
  - `async test_action_defaults_to_function_name()` (line 125)
  - `async process_document()` (line 133)
  - `async test_record_result_captures_after()` (line 140)
  - `async calculate()` (line 150)
  - `async test_before_snapshot_from_callable()` (line 156)
  - `snapshot()` (line 159)
  - `async archive()` (line 169)
  - `async test_static_before_snapshot()` (line 178)
  - `async archive()` (line 188)
- `TestAuditDecoratorFailure` (line 195; bases: `-`)
  - `async test_failure_records_reason_and_reraises()` (line 196)
  - `async run_import()` (line 205)
  - `async test_record_failures_disabled()` (line 217)
  - `async run_import()` (line 227)
  - `async test_missing_entity_context_is_skipped()` (line 234)
  - `async op_without_context()` (line 241)
  - `async test_sink_failure_never_breaks_operation()` (line 248)
  - `async process()` (line 258)
- `TestSingleton` (line 264; bases: `-`)
  - `test_init_and_reset_audit_logger()` (line 265)

#### Top-Level Functions

- `_logger()` (line 50)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `domain`
- `infra`

#### Imports

- `__future__`
- `domain.audit`
- `infra.audit_logger`
- `pytest`

### 4.171 `backend/tests/unit/infra/test_config.py`

- **Module:** `backend.tests.unit.infra.test_config`
- **Package:** `backend.tests.unit.infra`
- **Lines:** 157
- **Size:** 5,296 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `TestParsers` (line 48; bases: `-`)
  - `test_parse_int_default_when_blank()` (line 49)
  - `test_parse_int_accepts_value()` (line 53)
  - `test_parse_int_rejects_non_numeric()` (line 56)
  - `test_parse_int_enforces_bounds()` (line 60)
  - `test_parse_bool()` (line 66)
  - `test_parse_log_level()` (line 74)
- `TestLoadConfig` (line 81; bases: `-`)
  - `test_defaults()` (line 82)
  - `test_env_overrides()` (line 94)
  - `test_invalid_numeric_value_raises()` (line 115)
  - `test_log_level_int()` (line 122)
  - `test_app_config_is_immutable()` (line 127)
- `TestSingleton` (line 144; bases: `-`)
  - `test_get_config_caches()` (line 145)
  - `test_reset_config_forces_reload()` (line 148)

#### Top-Level Functions

- `_neutral_env()` (line 39)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `collections`
- `infra`

#### Imports

- `__future__`
- `collections.abc`
- `infra.config`
- `pytest`

### 4.172 `backend/tests/unit/infra/test_event_bus.py`

- **Module:** `backend.tests.unit.infra.test_event_bus`
- **Package:** `backend.tests.unit.infra`
- **Lines:** 206
- **Size:** 7,180 bytes
- **Categories:** AI extraction, audit / logging, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestSubscribe` (line 25; bases: `-`)
  - `async test_sync_handler_receives_event()` (line 26)
  - `handler()` (line 30)
  - `async test_async_handler_receives_event()` (line 41)
  - `async handler()` (line 45)
  - `async test_wildcard_handler_receives_every_event()` (line 52)
  - `async handler()` (line 56)
  - `async test_only_matching_event_types_dispatch()` (line 75)
  - `async handler()` (line 79)
  - `test_duplicate_subscription_raises()` (line 86)
  - `test_max_handlers_limit_enforced()` (line 93)
  - `test_max_handlers_must_be_positive()` (line 100)
  - `async test_unsubscribe()` (line 104)
  - `async test_clear_drops_all_handlers()` (line 114)
  - `async test_subscriber_count()` (line 122)
- `TestPublish` (line 131; bases: `-`)
  - `async test_publish_schedules_background_tasks()` (line 132)
  - `async handler()` (line 136)
  - `async test_publish_returns_handler_count()` (line 146)
  - `async test_publish_with_no_handlers_returns_zero()` (line 153)
  - `async test_publish_and_wait_awaits_handlers_in_order()` (line 157)
  - `async first()` (line 161)
  - `async second()` (line 164)
  - `async test_failing_handler_is_isolated()` (line 172)
  - `async failing()` (line 176)
  - `async healthy()` (line 179)
- `TestSingleton` (line 188; bases: `-`)
  - `test_get_event_bus_is_singleton()` (line 189)
  - `test_reset_event_bus_replaces()` (line 196)

#### Top-Level Functions

- `_document_event()` (line 14)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `datetime`
- `domain`
- `infra`
- `typing`

#### Imports

- `__future__`
- `asyncio`
- `datetime`
- `domain.workflow`
- `infra.event_bus`
- `pytest`
- `typing`

### 4.173 `backend/tests/unit/infra/test_llm_client.py`

- **Module:** `backend.tests.unit.infra.test_llm_client`
- **Package:** `backend.tests.unit.infra`
- **Lines:** 111
- **Size:** 4,129 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestLLMClient` (line 10; bases: `-`)
  - `async test_complete_returns_transport_text()` (line 11)
  - `transport()` (line 12)
  - `async test_payload_shape()` (line 24)
  - `transport()` (line 27)
  - `async test_no_system_message_when_omitted()` (line 48)
  - `transport()` (line 51)
  - `async test_transport_aiextraction_error_propagates()` (line 66)
  - `transport()` (line 67)
  - `async test_transport_generic_error_is_wrapped()` (line 79)
  - `transport()` (line 80)
  - `test_constructor_validation()` (line 92)
  - `test_properties()` (line 102)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `infra`
- `llm`

#### Imports

- `__future__`
- `core.exceptions`
- `infra.llm_client`
- `pytest`

### 4.174 `backend/tests/unit/infra/test_search_index.py`

- **Module:** `backend.tests.unit.infra.test_search_index`
- **Package:** `backend.tests.unit.infra`
- **Lines:** 223
- **Size:** 7,775 bytes
- **Categories:** AI extraction, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `TestExactNaturalKey` (line 57; bases: `-`)
  - `test_hit()` (line 58)
  - `test_miss()` (line 66)
  - `test_blank_natural_key_is_ignored()` (line 71)
- `TestKeywordSearch` (line 85; bases: `-`)
  - `test_token_coverage_ranking()` (line 86)
  - `test_scores_are_descending()` (line 95)
  - `test_unit_filter()` (line 103)
  - `test_country_filter()` (line 109)
  - `test_provider_filter()` (line 115)
  - `test_limit()` (line 122)
  - `test_empty_query_returns_nothing()` (line 129)
  - `test_empty_index_returns_nothing()` (line 135)
  - `test_case_insensitive()` (line 139)
- `TestMutation` (line 145; bases: `-`)
  - `test_add_and_replace_by_id()` (line 146)
  - `test_remove()` (line 155)
  - `test_load_replaces_contents()` (line 163)
  - `test_rebuild_is_load()` (line 172)
  - `test_get_len_snapshot()` (line 178)
  - `test_default_limit_must_be_positive()` (line 185)
- `TestFromRepository` (line 190; bases: `-`)
  - `_StubSource()` (line 191)
  - `async test_loads_from_source()` (line 198)
- `TestSingleton` (line 205; bases: `-`)
  - `test_get_search_index_is_singleton()` (line 206)
  - `test_reset_search_index_replaces()` (line 213)

#### Top-Level Functions

- `_factor()` (line 17)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `decimal`
- `domain`
- `infra`
- `typing`

#### Imports

- `__future__`
- `decimal`
- `domain.factor`
- `infra.search_index`
- `pytest`
- `typing`

### 4.175 `backend/tests/unit/test_core.py`

- **Module:** `backend.tests.unit.test_core`
- **Package:** `backend.tests.unit`
- **Lines:** 123
- **Size:** 4,461 bytes
- **Categories:** audit / logging
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `TestErrorHierarchy` (line 29; bases: `-`)
  - `test_code_and_status()` (line 49)
  - `test_details_are_stored()` (line 59)
  - `test_str_is_message()` (line 63)
  - `test_default_details_is_empty_dict()` (line 67)
- `TestCoreTypes` (line 71; bases: `-`)
  - `test_country_values()` (line 72)
  - `test_scope_values()` (line 76)
  - `test_str_enums_are_str()` (line 81)
  - `test_unit_and_year_are_typed()` (line 85)
  - `test_date_range_contains()` (line 91)
  - `test_date_range_rejects_reversed()` (line 97)
  - `test_date_range_overlaps()` (line 101)
  - `test_date_range_is_immutable()` (line 108)
- `TestLogging` (line 114; bases: `-`)
  - `test_configure_logging_does_not_stack_handlers()` (line 115)
  - `test_get_logger_returns_named_logger()` (line 121)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `core`
- `dataclasses`
- `datetime`

#### Imports

- `__future__`
- `core`
- `core.exceptions`
- `core.types`
- `dataclasses`
- `datetime`
- `logging`
- `pytest`

### 4.176 `backend/tests/verify_setup.py`

- **Module:** `backend.tests.verify_setup`
- **Package:** `backend.tests`
- **Lines:** 113
- **Size:** 4,415 bytes
- **Categories:** database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async verify()` (line 13)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `auth`
- `beta_access_codes`
- `database`
- `organization_members`
- `organizations`
- `pathlib`
- `staff_profiles`

#### Imports

- `asyncio`
- `database`
- `os`
- `pathlib`
- `sys`

### 4.177 `backend/utils/__init__.py`

- **Module:** `backend.utils`
- **Package:** `backend`
- **Lines:** 113
- **Size:** 2,745 bytes
- **Categories:** AI extraction, calculation, document processing
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.document_classifier`
- `.email`
- `.emissions`
- `.organization_utils`
- `.staff_workload`

### 4.178 `backend/utils/audit_logger.py`

- **Module:** `backend.utils.audit_logger`
- **Package:** `backend.utils`
- **Lines:** 148
- **Size:** 4,579 bytes
- **Categories:** audit / logging, database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async log_audit()` (line 6)
- `async log_document_action()` (line 67)
- `async log_verification_action()` (line 89)
- `async log_message_action()` (line 116)
- `async log_notification_action()` (line 134)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `audit_logs`
- `database`
- `datetime`
- `typing`

#### Imports

- `database`
- `datetime`
- `typing`

### 4.179 `backend/utils/document_classifier.py`

- **Module:** `backend.utils.document_classifier`
- **Package:** `backend.utils`
- **Lines:** 145
- **Size:** 6,262 bytes
- **Categories:** database / repository, document processing
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async classify_document()` (line 27)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `database`
- `datetime`
- `document_types`
- `typing`

#### Imports

- `database`
- `datetime`
- `traceback`
- `typing`

### 4.180 `backend/utils/email.py`

- **Module:** `backend.utils.email`
- **Package:** `backend.utils`
- **Lines:** 651
- **Size:** 26,158 bytes
- **Categories:** AI extraction
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `async send_email()` (line 19)
- `render_template()` (line 44)
- `render_template_subject()` (line 53)
- `async send_email_from_db_template()` (line 66)
- `async send_invitation_email()` (line 114)
- `async send_welcome_email()` (line 191)
- `async send_password_reset_email()` (line 260)
- `async send_emission_report_email()` (line 317)
- `async send_beta_invite_email()` (line 378)
- `async send_feedback_acknowledgement_email()` (line 434)
- `async send_review_completion_email()` (line 484)
- `async send_bulk_invite_summary_email()` (line 544)
- `async log_email()` (line 614)
- `validate_email()` (line 645)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `Beta`
- `database`
- `datetime`
- `email_logs`
- `email_templates`
- `the`
- `typing`

#### Imports

- `datetime`
- `json`
- `os`
- `re`
- `resend`
- `typing`

### 4.181 `backend/utils/emissions.py`

- **Module:** `backend.utils.emissions`
- **Package:** `backend.utils`
- **Lines:** 499
- **Size:** 24,147 bytes
- **Categories:** calculation
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `get_emission_factor()` (line 45)
- `get_activity_category()` (line 112)
- `calculate_emissions_with_defra()` (line 144)
- `process_fuel_data()` (line 180)
- `normalize_fuel()` (line 193)
- `process_utility_data()` (line 243)
- `normalize_utility_type()` (line 261)
- `process_scope3_data()` (line 316)
- `normalize_scope3()` (line 334)
- `extract_issues_from_result()` (line 396)
- `has_low_confidence()` (line 493)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `activity_categories`
- `database`
- `datetime`
- `defra_conversion_factors`
- `the`
- `typing`

#### Imports

- `datetime`
- `numpy`
- `pandas`
- `typing`

### 4.182 `backend/utils/organization_utils.py`

- **Module:** `backend.utils.organization_utils`
- **Package:** `backend.utils`
- **Lines:** 235
- **Size:** 7,680 bytes
- **Categories:** Storage
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async get_organization_name()` (line 10)
- `async get_organization_by_id()` (line 31)
- `async get_organization_stats()` (line 51)
- `async get_facility_stats()` (line 131)
- `async get_organization_members()` (line 167)
- `async get_organization_assets()` (line 190)
- `async get_asset_stats()` (line 224)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `assets`
- `emissions_logs`
- `facilities`
- `organization_files`
- `organization_members`
- `organizations`
- `supabase`
- `typing`

#### Imports

- `supabase`
- `traceback`
- `typing`

### 4.183 `backend/utils/staff_workload.py`

- **Module:** `backend.utils.staff_workload`
- **Package:** `backend.utils`
- **Lines:** 171
- **Size:** 6,064 bytes
- **Categories:** database / repository
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `async get_staff_workload()` (line 11)
- `async get_all_staff_workload()` (line 78)
- `async get_staff_workload_from_table()` (line 130)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `database`
- `datetime`
- `manual_review_queue`
- `staff_profiles`
- `staff_workload`
- `table`
- `the`
- `typing`

#### Imports

- `database`
- `datetime`
- `typing`

### 4.184 `create_admin_dashboard.py`

- **Module:** `create_admin_dashboard`
- **Package:** `create_admin_dashboard`
- **Lines:** 547
- **Size:** 15,507 bytes
- **Categories:** reporting
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- `create_file_with_stub()` (line 440)
- `create_directory()` (line 458)
- `create_file()` (line 468)
- `build_structure()` (line 495)
- `main()` (line 511)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `filename`
- `organization_members`
- `pathlib`
- `staff_profiles`
- `with`

#### Imports

- `os`
- `pathlib`
- `sys`

### 4.185 `demodatagen/config.py`

- **Module:** `demodatagen.config`
- **Package:** `demodatagen`
- **Lines:** 158
- **Size:** 4,900 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `Config` (line 15; bases: `-`)
  - `get_country_config()` (line 135)
  - `get_company_size()` (line 144)
  - `get_random_country()` (line 149)
  - `get_random_industry()` (line 155)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `datetime`
- `pathlib`
- `typing`

#### Imports

- `datetime`
- `pathlib`
- `random`
- `typing`

### 4.186 `demodatagen/generators/__init__.py`

- **Module:** `demodatagen.generators`
- **Package:** `demodatagen`
- **Lines:** 1
- **Size:** 0 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.187 `demodatagen/generators/base_generator.py`

- **Module:** `demodatagen.generators.base_generator`
- **Package:** `demodatagen.generators`
- **Lines:** 260
- **Size:** 8,167 bytes
- **Categories:** CSV / Excel, audit / logging
- **V3 impact:** **NO CHANGE**

#### Classes

- `BaseGenerator` (line 31; bases: `ABC, Generic[T]`)
  - `__init__()` (line 39)
  - `_setup_logging()` (line 66)
  - `generate()` (line 79)
  - `to_csv_row()` (line 89)
  - `get_csv_fields()` (line 102)
  - `write_csv()` (line 111)
  - `generate_batch()` (line 154)
  - `validate_record()` (line 212)
  - `get_generated_count()` (line 249)
  - `get_error_count()` (line 253)
  - `reset_counts()` (line 257)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `abc`
- `config`
- `datetime`
- `pathlib`
- `tqdm`
- `typing`
- `utils`

#### Imports

- `abc`
- `config`
- `csv`
- `datetime`
- `json`
- `logging`
- `pathlib`
- `random`
- `sys`
- `tqdm`
- `typing`
- `utils`

### 4.188 `demodatagen/generators/carbon/generate_activity_categories.py`

- **Module:** `demodatagen.generators.carbon.generate_activity_categories`
- **Package:** `demodatagen.generators.carbon`
- **Lines:** 1
- **Size:** 0 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.189 `demodatagen/generators/carbon/generate_emissions_logs.py`

- **Module:** `demodatagen.generators.carbon.generate_emissions_logs`
- **Package:** `demodatagen.generators.carbon`
- **Lines:** 1
- **Size:** 0 bytes
- **Categories:** audit / logging, calculation
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.190 `demodatagen/generators/collaboration/generate_conversations.py`

- **Module:** `demodatagen.generators.collaboration.generate_conversations`
- **Package:** `demodatagen.generators.collaboration`
- **Lines:** 1
- **Size:** 0 bytes
- **Categories:** Realtime / communication
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.191 `demodatagen/generators/collaboration/generate_messages.py`

- **Module:** `demodatagen.generators.collaboration.generate_messages`
- **Package:** `demodatagen.generators.collaboration`
- **Lines:** 1
- **Size:** 0 bytes
- **Categories:** Realtime / communication
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.192 `demodatagen/generators/core/generate_organizations.py`

- **Module:** `demodatagen.generators.core.generate_organizations`
- **Package:** `demodatagen.generators.core`
- **Lines:** 632
- **Size:** 28,551 bytes
- **Categories:** factor provider
- **V3 impact:** **REVIEW — PROVIDER SEMANTICS**

#### Classes

- `Organization` (line 30; bases: `-`)
- `OrganizationGenerator` (line 94; bases: `BaseGenerator`)
  - `__init__()` (line 97)
  - `_load_country_data()` (line 116)
  - `_load_industry_data()` (line 177)
  - `generate()` (line 230)
  - `_generate_organization()` (line 242)
  - `_generate_name()` (line 369)
  - `_generate_address()` (line 399)
  - `_generate_contacts()` (line 434)
  - `_generate_website()` (line 470)
  - `_generate_domain()` (line 475)
  - `_generate_company_number()` (line 483)
  - `_generate_vat_number()` (line 491)
  - `_determine_size()` (line 495)
  - `_generate_update_date()` (line 502)
  - `_format_address()` (line 510)
  - `to_csv_row()` (line 523)
  - `get_csv_fields()` (line 588)

#### Top-Level Functions

- `main()` (line 611)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `a`
- `config`
- `dataclasses`
- `date`
- `datetime`
- `faker`
- `generators`
- `pathlib`
- `typing`
- `utils`

#### Imports

- `config`
- `dataclasses`
- `datetime`
- `faker`
- `faker.providers`
- `generators.base_generator`
- `pathlib`
- `random`
- `sys`
- `typing`
- `utils`
- `uuid`

### 4.193 `demodatagen/generators/core/generate_staff_profiles.py`

- **Module:** `demodatagen.generators.core.generate_staff_profiles`
- **Package:** `demodatagen.generators.core`
- **Lines:** 1
- **Size:** 0 bytes
- **Categories:** Storage
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.194 `demodatagen/generators/core/generate_users.py`

- **Module:** `demodatagen.generators.core.generate_users`
- **Package:** `demodatagen.generators.core`
- **Lines:** 1
- **Size:** 0 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.195 `demodatagen/generators/documents/generate_customer_documents.py`

- **Module:** `demodatagen.generators.documents.generate_customer_documents`
- **Package:** `demodatagen.generators.documents`
- **Lines:** 1
- **Size:** 0 bytes
- **Categories:** document processing
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.196 `demodatagen/generators/documents/generate_document_types.py`

- **Module:** `demodatagen.generators.documents.generate_document_types`
- **Package:** `demodatagen.generators.documents`
- **Lines:** 1
- **Size:** 0 bytes
- **Categories:** document processing
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.197 `demodatagen/generators/facilities/generate_assets.py`

- **Module:** `demodatagen.generators.facilities.generate_assets`
- **Package:** `demodatagen.generators.facilities`
- **Lines:** 1
- **Size:** 0 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.198 `demodatagen/generators/facilities/generate_facilities.py`

- **Module:** `demodatagen.generators.facilities.generate_facilities`
- **Package:** `demodatagen.generators.facilities`
- **Lines:** 1
- **Size:** 0 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.199 `demodatagen/organizations.py`

- **Module:** `demodatagen.organizations`
- **Package:** `demodatagen`
- **Lines:** 1043
- **Size:** 40,931 bytes
- **Categories:** CSV / Excel, factor provider
- **V3 impact:** **NO CHANGE**

#### Classes

- `Config` (line 31; bases: `-`)
- `Address` (line 127; bases: `-`)
  - `to_dict()` (line 137)
- `Organization` (line 151; bases: `-`)
  - `to_csv_row()` (line 249)
- `OrganizationGenerator` (line 319; bases: `-`)
  - `__init__()` (line 327)
  - `generate_organizations()` (line 358)
  - `_generate_single_organization()` (line 377)
  - `_generate_company_name()` (line 468)
  - `_generate_address()` (line 532)
  - `_generate_contact_info()` (line 623)
  - `_generate_email()` (line 681)
  - `_generate_website()` (line 717)
  - `_generate_domain()` (line 734)
  - `_generate_company_number()` (line 741)
  - `_generate_vat_number()` (line 765)
  - `_generate_sector()` (line 779)
  - `_determine_company_size()` (line 794)
  - `_generate_reporting_frequency()` (line 814)
  - `_generate_financial_year_end()` (line 818)
  - `_generate_vat_region()` (line 825)
  - `_generate_tax_rate()` (line 829)
  - `_generate_registration_number()` (line 846)
  - `_generate_business_structure()` (line 850)
  - `_generate_isin()` (line 864)
  - `_generate_sedol()` (line 880)
  - `_generate_lei()` (line 885)
  - `_generate_trial_start()` (line 890)
  - `_generate_trial_end()` (line 896)
  - `_generate_defra_version()` (line 903)
  - `_generate_metadata()` (line 907)
  - `_generate_random_timestamp()` (line 922)
  - `_generate_update_timestamp()` (line 929)
  - `_format_address()` (line 937)
- `CSVWriter` (line 955; bases: `-`)
  - `__init__()` (line 958)
  - `write_organizations()` (line 968)

#### Top-Level Functions

- `main()` (line 999)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `company`
- `dataclasses`
- `datetime`
- `faker`
- `pathlib`
- `the`
- `timestamp`
- `typing`

#### Imports

- `csv`
- `dataclasses`
- `datetime`
- `faker`
- `faker.providers`
- `json`
- `pathlib`
- `random`
- `typing`
- `uuid`

### 4.200 `demodatagen/scripts/export_to_sql.py`

- **Module:** `demodatagen.scripts.export_to_sql`
- **Package:** `demodatagen.scripts`
- **Lines:** 243
- **Size:** 8,196 bytes
- **Categories:** CSV / Excel
- **V3 impact:** **NO CHANGE**

#### Classes

- `SQLExporter` (line 23; bases: `-`)
  - `__init__()` (line 26)
  - `escape_value()` (line 70)
  - `csv_to_sql()` (line 98)
  - `convert_directory()` (line 169)

#### Top-Level Functions

- `main()` (line 227)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `config`
- `datetime`
- `filename`
- `pathlib`
- `typing`

#### Imports

- `config`
- `csv`
- `datetime`
- `json`
- `pathlib`
- `sys`
- `typing`

### 4.201 `demodatagen/scripts/run_all_generators.py`

- **Module:** `demodatagen.scripts.run_all_generators`
- **Package:** `demodatagen.scripts`
- **Lines:** 199
- **Size:** 6,566 bytes
- **Categories:** audit / logging
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `DataGeneratorRunner` (line 25; bases: `-`)
  - `__init__()` (line 28)
  - `run_module()` (line 63)
  - `run_all()` (line 124)
  - `_print_summary()` (line 159)

#### Top-Level Functions

- `main()` (line 189)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `config`
- `datetime`
- `generators`
- `pathlib`
- `typing`

#### Imports

- `config`
- `datetime`
- `generators.core.generate_organizations`
- `logging`
- `pathlib`
- `sys`
- `time`
- `traceback`
- `typing`

### 4.202 `demodatagen/scripts/validate_data.py`

- **Module:** `demodatagen.scripts.validate_data`
- **Package:** `demodatagen.scripts`
- **Lines:** 284
- **Size:** 10,669 bytes
- **Categories:** CSV / Excel, validation / QA
- **V3 impact:** **NO CHANGE**

#### Classes

- `DataValidatorCLI` (line 24; bases: `-`)
  - `__init__()` (line 27)
  - `validate_csv()` (line 34)
  - `_validate_organization()` (line 90)
  - `_validate_user()` (line 146)
  - `_validate_document()` (line 168)
  - `validate_directory()` (line 190)
  - `print_report()` (line 211)

#### Top-Level Functions

- `main()` (line 249)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `config`
- `datetime`
- `pathlib`
- `typing`
- `utils`

#### Imports

- `config`
- `csv`
- `datetime`
- `json`
- `pathlib`
- `sys`
- `typing`
- `utils.data_validators`

### 4.203 `demodatagen/utils/__init__.py`

- **Module:** `demodatagen.utils`
- **Package:** `demodatagen`
- **Lines:** 19
- **Size:** 409 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Parse Status

⚠️ `SyntaxError: invalid syntax at line 6`

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.204 `demodatagen/utils/data_validators.py`

- **Module:** `demodatagen.utils.data_validators`
- **Package:** `demodatagen.utils`
- **Lines:** 169
- **Size:** 6,001 bytes
- **Categories:** validation / QA
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- `DataValidator` (line 18; bases: `-`)
  - `is_valid_uuid()` (line 22)
  - `is_valid_email()` (line 31)
  - `is_valid_phone()` (line 37)
  - `is_valid_postcode()` (line 44)
  - `is_valid_vat_number()` (line 60)
  - `is_valid_date()` (line 76)
  - `is_valid_json()` (line 85)
  - `validate_required_fields()` (line 96)
  - `validate_data_types()` (line 105)
  - `sanitize_string()` (line 116)
  - `validate_referential_integrity()` (line 128)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `datetime`
- `typing`

#### Imports

- `datetime`
- `json`
- `re`
- `typing`
- `uuid`

### 4.205 `demodatagen/utils/date_utils.py`

- **Module:** `demodatagen.utils.date_utils`
- **Package:** `demodatagen.utils`
- **Lines:** 262
- **Size:** 8,564 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `DateUtils` (line 18; bases: `-`)
  - `random_date()` (line 22)
  - `random_date_business()` (line 55)
  - `random_date_range()` (line 80)
  - `random_quarter_end()` (line 105)
  - `random_financial_year_end()` (line 125)
  - `is_business_day()` (line 146)
  - `is_holiday()` (line 151)
  - `get_business_days_between()` (line 177)
  - `add_business_days()` (line 198)
  - `format_date()` (line 219)
  - `ensure_timezone()` (line 233)
  - `random_timestamp_in_range()` (line 244)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `datetime`
- `dateutil`
- `typing`

#### Imports

- `datetime`
- `dateutil.relativedelta`
- `pytz`
- `random`
- `typing`

### 4.206 `demodatagen/utils/id_generators.py`

- **Module:** `demodatagen.utils.id_generators`
- **Package:** `demodatagen.utils`
- **Lines:** 117
- **Size:** 4,789 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `IDGenerator` (line 17; bases: `-`)
  - `generate_uuid()` (line 21)
  - `generate_short_id()` (line 26)
  - `generate_company_number()` (line 32)
  - `generate_vat_number()` (line 46)
  - `generate_isin()` (line 60)
  - `generate_lei()` (line 71)
  - `generate_sedol()` (line 77)
  - `generate_eircode()` (line 83)
  - `generate_filename()` (line 93)
  - `generate_reference_number()` (line 103)
  - `generate_invoice_number()` (line 108)
  - `generate_batch_id()` (line 114)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `typing`

#### Imports

- `random`
- `string`
- `typing`
- `uuid`

### 4.207 `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/19fc925d-0962-8a3a-8000-0fb8fbe59ca5/scratch/postprocess.py`

- **Module:** `docs.Final_Kimi.Kimi_Agent_UK_IE_Compliance_Audit_Report.19fc925d-0962-8a3a-8000-0fb8fbe59ca5.scratch.postprocess`
- **Package:** `docs.Final_Kimi.Kimi_Agent_UK_IE_Compliance_Audit_Report.19fc925d-0962-8a3a-8000-0fb8fbe59ca5.scratch`
- **Lines:** 236
- **Size:** 7,693 bytes
- **Categories:** audit / logging, database / repository, reporting
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `set_style_color()` (line 37)
- `color_runs()` (line 49)
- `set_cell_shading()` (line 60)
- `table_borders()` (line 67)
- `set_table_width()` (line 81)
- `header_repeat()` (line 95)
- `add_bottom_rule()` (line 119)
- `add_field()` (line 130)
- `mk_run()` (line 131)
- `txt()` (line 164)
- `set_run_fonts()` (line 180)
- `split_glyph_runs()` (line 192)
- `all_paragraphs()` (line 222)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `docx`

#### Imports

- `copy`
- `docx`
- `docx.enum.section`
- `docx.enum.text`
- `docx.oxml`
- `docx.oxml.ns`
- `docx.shared`

### 4.208 `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/scratch_mm/style.py`

- **Module:** `docs.Final_Kimi.Kimi_Agent_UK_IE_Compliance_Audit_Report.scratch_mm.style`
- **Package:** `docs.Final_Kimi.Kimi_Agent_UK_IE_Compliance_Audit_Report.scratch_mm`
- **Lines:** 137
- **Size:** 4,954 bytes
- **Categories:** audit / logging, database / repository, reporting
- **V3 impact:** **EXTEND / REVIEW**

#### Classes

- None detected.

#### Top-Level Functions

- `set_cell_shading()` (line 58)
- `add_field()` (line 121)
- `style_run()` (line 127)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `docx`

#### Imports

- `docx`
- `docx.enum.table`
- `docx.enum.text`
- `docx.oxml`
- `docx.oxml.ns`
- `docx.shared`

### 4.209 `export_postman.py`

- **Module:** `export_postman`
- **Package:** `export_postman`
- **Lines:** 141
- **Size:** 4,969 bytes
- **Categories:** CSV / Excel
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `load_routes_from_markdown()` (line 13)
- `generate_postman_collection()` (line 50)
- `main()` (line 124)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `datetime`
- `pathlib`
- `typing`

#### Imports

- `datetime`
- `json`
- `pathlib`
- `re`
- `typing`

### 4.210 `generate_api_docs.py`

- **Module:** `generate_api_docs`
- **Package:** `generate_api_docs`
- **Lines:** 252
- **Size:** 9,694 bytes
- **Categories:** API
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- `generate_structured_docs()` (line 7)
- `create_summary_markdown()` (line 182)
- `main()` (line 217)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `collections`
- `existing`
- `list_endpoints`
- `pathlib`
- `the`
- `typing`

#### Imports

- `collections`
- `json`
- `list_endpoints`
- `pathlib`
- `typing`

### 4.211 `generate_backend_inventory.py`

- **Module:** `generate_backend_inventory`
- **Package:** `generate_backend_inventory`
- **Lines:** 1367
- **Size:** 33,106 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- `FunctionInfo` (line 70; bases: `-`)
- `ClassInfo` (line 78; bases: `-`)
- `RouteInfo` (line 86; bases: `-`)
- `ModuleInfo` (line 94; bases: `-`)
- `ModuleVisitor` (line 511; bases: `ast.NodeVisitor`)
  - `__init__()` (line 513)
  - `visit_Import()` (line 521)
  - `visit_ImportFrom()` (line 526)
  - `visit_ClassDef()` (line 536)
  - `_visit_function()` (line 560)
  - `visit_FunctionDef()` (line 585)
  - `visit_AsyncFunctionDef()` (line 588)

#### Top-Level Functions

- `normalize_path()` (line 119)
- `module_name_from_path()` (line 123)
- `package_from_module()` (line 133)
- `safe_unparse()` (line 139)
- `decorator_name()` (line 146)
- `extract_constant_string()` (line 152)
- `get_route_from_decorator()` (line 162)
- `classify_module()` (line 400)
- `infer_db_tables()` (line 447)
- `parse_python_file()` (line 592)
- `discover_python_files()` (line 653)
- `v3_impact()` (line 674)
- `md_escape()` (line 731)
- `generate_markdown()` (line 735)
- `main()` (line 1284)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `organizations`
- `pathlib`
- `the`
- `typing`

#### Imports

- `__future__`
- `ast`
- `dataclasses`
- `pathlib`
- `re`
- `sys`
- `typing`

### 4.212 `generate_messy_fuel_csv.py`

- **Module:** `generate_messy_fuel_csv`
- **Package:** `generate_messy_fuel_csv`
- **Lines:** 33
- **Size:** 1,451 bytes
- **Categories:** CSV / Excel
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `datetime`

#### Imports

- `datetime`
- `numpy`
- `pandas`

### 4.213 `generate_messy_utility_csv.py`

- **Module:** `generate_messy_utility_csv`
- **Package:** `generate_messy_utility_csv`
- **Lines:** 28
- **Size:** 1,360 bytes
- **Categories:** CSV / Excel
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `numpy`
- `pandas`

### 4.214 `list_endpoints.py`

- **Module:** `list_endpoints`
- **Package:** `list_endpoints`
- **Lines:** 347
- **Size:** 12,826 bytes
- **Categories:** API
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- `extract_fastapi_routes()` (line 8)
- `scan_directory_for_routes()` (line 75)
- `scan_all_routes()` (line 119)
- `print_endpoints()` (line 143)
- `export_to_markdown()` (line 213)
- `debug_scan_file()` (line 275)
- `main()` (line 307)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `file`
- `module`
- `pathlib`
- `the`
- `typing`

#### Imports

- `ast`
- `os`
- `pathlib`
- `re`
- `typing`

### 4.215 `quick_api_ref.py`

- **Module:** `quick_api_ref`
- **Package:** `quick_api_ref`
- **Lines:** 195
- **Size:** 7,611 bytes
- **Categories:** API
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- `load_routes_from_markdown()` (line 12)
- `search_endpoints()` (line 53)
- `print_results()` (line 71)
- `interactive_search()` (line 105)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `pathlib`
- `typing`

#### Imports

- `json`
- `pathlib`
- `re`
- `typing`

### 4.216 `src/__init__.py`

- **Module:** `src`
- **Package:** `src`
- **Lines:** 2
- **Size:** 35 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.217 `src/commands/__init__.py`

- **Module:** `src.commands`
- **Package:** `src`
- **Lines:** 2
- **Size:** 75 bytes
- **Categories:** Uncategorized
- **V3 impact:** **NO DIRECT V3 IMPACT**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.218 `src/commands/import_defra.py`

- **Module:** `src.commands.import_defra`
- **Package:** `src.commands`
- **Lines:** 270
- **Size:** 10,739 bytes
- **Categories:** CSV / Excel, audit / logging, database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `ProgressReporter` (line 57; bases: `-`)
  - `__init__()` (line 60)
  - `start_sheet()` (line 65)
  - `rows_done()` (line 69)
  - `finish_sheet()` (line 73)

#### Top-Level Functions

- `_parse_args()` (line 77)
- `_setup_logging()` (line 106)
- `main()` (line 125)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dotenv`
- `pathlib`
- `src`
- `the`

#### Imports

- `__future__`
- `argparse`
- `dotenv`
- `logging`
- `os`
- `pathlib`
- `src.providers.defra`
- `src.providers.defra.models`
- `sys`
- `time`

### 4.219 `src/commands/import_seai.py`

- **Module:** `src.commands.import_seai`
- **Package:** `src.commands`
- **Lines:** 161
- **Size:** 6,209 bytes
- **Categories:** AI extraction, CSV / Excel, audit / logging, database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_parse_args()` (line 55)
- `main()` (line 79)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `pathlib`
- `src`
- `the`

#### Imports

- `__future__`
- `argparse`
- `logging`
- `os`
- `pathlib`
- `src.providers.seai`
- `src.providers.seai.models`
- `sys`
- `time`

### 4.220 `src/providers/__init__.py`

- **Module:** `src.providers`
- **Package:** `src`
- **Lines:** 2
- **Size:** 46 bytes
- **Categories:** factor provider
- **V3 impact:** **REVIEW — PROVIDER SEMANTICS**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.221 `src/providers/defra/__init__.py`

- **Module:** `src.providers.defra`
- **Package:** `src.providers`
- **Lines:** 73
- **Size:** 1,808 bytes
- **Categories:** CSV / Excel, database / repository, factor provider, validation / QA
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.exporter`
- `.mapper`
- `.models`
- `.parser`
- `.validator`

### 4.222 `src/providers/defra/exporter.py`

- **Module:** `src.providers.defra.exporter`
- **Package:** `src.providers.defra`
- **Lines:** 504
- **Size:** 18,621 bytes
- **Categories:** CSV / Excel, Storage, audit / logging, database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_sanitize_dsn()` (line 37)
- `_sql_str()` (line 53)
- `_sql_nullable()` (line 57)
- `_sql_decimal()` (line 61)
- `generate_sql()` (line 68)
- `_insert_statement()` (line 95)
- `write_sql()` (line 149)
- `write_json()` (line 162)
- `_format_seconds()` (line 195)
- `write_summary()` (line 202)
- `write_statistics()` (line 276)
- `load_to_db()` (line 309)
- `load_with_psycopg2()` (line 337)
- `load_with_supabase()` (line 428)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `collections`
- `datetime`
- `decimal`
- `pathlib`
- `supabase`
- `typing`

#### Imports

- `.models`
- `__future__`
- `collections`
- `datetime`
- `decimal`
- `json`
- `logging`
- `pathlib`
- `psycopg2`
- `supabase`
- `typing`

### 4.223 `src/providers/defra/mapper.py`

- **Module:** `src.providers.defra.mapper`
- **Package:** `src.providers.defra`
- **Lines:** 212
- **Size:** 6,707 bytes
- **Categories:** database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `clean_text()` (line 25)
- `parse_decimal()` (line 33)
- `build_activity_type()` (line 57)
- `truncate_activity_type()` (line 86)
- `natural_key()` (line 100)
- `build_metadata()` (line 121)
- `map_row()` (line 139)
- `map_all()` (line 200)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `decimal`
- `the`
- `typing`

#### Imports

- `.models`
- `__future__`
- `decimal`
- `re`
- `typing`

### 4.224 `src/providers/defra/models.py`

- **Module:** `src.providers.defra.models`
- **Package:** `src.providers.defra`
- **Lines:** 382
- **Size:** 11,890 bytes
- **Categories:** database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `WorkbookMeta` (line 42; bases: `-`)
  - `as_dict()` (line 58)
- `WorksheetInfo` (line 78; bases: `-`)
  - `as_dict()` (line 91)
- `WorkbookAnalysis` (line 108; bases: `-`)
  - `as_dict()` (line 116)
- `ParsedRow` (line 130; bases: `-`)
  - `as_dict()` (line 146)
- `EmissionFactor` (line 166; bases: `-`)
  - `as_dict()` (line 201)
- `SkippedRow` (line 224; bases: `-`)
  - `as_dict()` (line 234)
- `DuplicateRow` (line 248; bases: `-`)
  - `as_dict()` (line 259)
- `ValidationIssue` (line 274; bases: `-`)
  - `as_dict()` (line 283)
- `ValidationReport` (line 296; bases: `-`)
  - `warnings()` (line 305)
  - `errors()` (line 309)
- `ImportStats` (line 316; bases: `-`)
  - `as_dict()` (line 339)
- `ImportResult` (line 345; bases: `-`)
  - `as_dict()` (line 356)
  - `as_dict()` (line 370)

#### Top-Level Functions

- `to_jsonable()` (line 21)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `a`
- `dataclasses`
- `datetime`
- `decimal`
- `typing`

#### Imports

- `__future__`
- `dataclasses`
- `datetime`
- `decimal`
- `typing`

### 4.225 `src/providers/defra/parser.py`

- **Module:** `src.providers.defra.parser`
- **Package:** `src.providers.defra`
- **Lines:** 374
- **Size:** 13,332 bytes
- **Categories:** database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `clean_cell()` (line 51)
- `open_workbook()` (line 62)
- `workbook_sha256()` (line 69)
- `_row_is_data_header()` (line 78)
- `detect_header_row()` (line 86)
- `parse_reporting_year()` (line 113)
- `_sheet_is_documentation()` (line 122)
- `scan_documentation_values()` (line 138)
- `analyze_workbook()` (line 166)
- `iter_data_rows()` (line 256)
- `parse_worksheet()` (line 271)
- `cell()` (line 287)
- `raw_cell()` (line 293)
- `sheet_dataframe()` (line 347)
- `pandas_sheet_stats()` (line 352)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `a`
- `openpyxl`
- `the`
- `typing`

#### Imports

- `.models`
- `__future__`
- `hashlib`
- `openpyxl`
- `openpyxl.workbook.workbook`
- `openpyxl.worksheet.worksheet`
- `os`
- `pandas`
- `re`
- `typing`

### 4.226 `src/providers/defra/validator.py`

- **Module:** `src.providers.defra.validator`
- **Package:** `src.providers.defra`
- **Lines:** 207
- **Size:** 7,496 bytes
- **Categories:** database / repository, factor provider, validation / QA
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_issue()` (line 36)
- `_skip()` (line 46)
- `_skip_detail()` (line 57)
- `validate_all()` (line 70)
- `build_stats()` (line 168)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `the`

#### Imports

- `.models`
- `__future__`

### 4.227 `src/providers/seai/__init__.py`

- **Module:** `src.providers.seai`
- **Package:** `src.providers`
- **Lines:** 65
- **Size:** 1,901 bytes
- **Categories:** AI extraction, CSV / Excel, database / repository, factor provider, validation / QA
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.exporter`
- `.mapper`
- `.models`
- `.parser`
- `.validator`

### 4.228 `src/providers/seai/exporter.py`

- **Module:** `src.providers.seai.exporter`
- **Package:** `src.providers.seai`
- **Lines:** 370
- **Size:** 13,604 bytes
- **Categories:** AI extraction, CSV / Excel, audit / logging, database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_sql_str()` (line 47)
- `_sql_nullable()` (line 51)
- `_sql_decimal()` (line 55)
- `generate_sql()` (line 61)
- `_insert_statement()` (line 85)
- `write_sql()` (line 122)
- `write_json()` (line 130)
- `write_summary()` (line 141)
- `write_statistics()` (line 183)
- `_sanitize_dsn()` (line 211)
- `load_to_db()` (line 228)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `decimal`
- `pathlib`
- `public`
- `typing`

#### Imports

- `.models`
- `__future__`
- `decimal`
- `json`
- `logging`
- `pathlib`
- `psycopg2`
- `typing`
- `uuid`

### 4.229 `src/providers/seai/mapper.py`

- **Module:** `src.providers.seai.mapper`
- **Package:** `src.providers.seai`
- **Lines:** 164
- **Size:** 5,937 bytes
- **Categories:** AI extraction, database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_natural_key()` (line 59)
- `_canonical_label()` (line 70)
- `_skip()` (line 74)
- `_multiplier_for()` (line 84)
- `map_row()` (line 110)
- `map_all()` (line 153)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `decimal`
- `section`
- `the`
- `typing`

#### Imports

- `.models`
- `__future__`
- `decimal`
- `typing`

### 4.230 `src/providers/seai/models.py`

- **Module:** `src.providers.seai.models`
- **Package:** `src.providers.seai`
- **Lines:** 378
- **Size:** 12,640 bytes
- **Categories:** AI extraction, database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `SeaiWorkbookMeta` (line 91; bases: `-`)
  - `as_dict()` (line 106)
- `SeaiWorksheetInfo` (line 125; bases: `-`)
  - `as_dict()` (line 134)
- `SeaiWorkbookData` (line 147; bases: `-`)
  - `as_dict()` (line 155)
- `SeaiParsedRow` (line 191; bases: `-`)
  - `has_numeric_emission_factor()` (line 214)
  - `as_dict()` (line 222)
- `SeaiFactor` (line 250; bases: `-`)
  - `as_dict()` (line 272)
- `SeaiSkip` (line 296; bases: `-`)
  - `as_dict()` (line 305)
- `SeaiValidationIssue` (line 318; bases: `-`)
- `SeaiValidationReport` (line 326; bases: `-`)
  - `warnings()` (line 335)
  - `errors()` (line 339)
  - `ok()` (line 343)
- `SeaiImportResult` (line 348; bases: `-`)
  - `as_dict()` (line 357)

#### Top-Level Functions

- `to_jsonable()` (line 73)
- `_dec()` (line 171)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `dataclasses`
- `decimal`
- `the`
- `typing`

#### Imports

- `__future__`
- `dataclasses`
- `decimal`
- `typing`

### 4.231 `src/providers/seai/parser.py`

- **Module:** `src.providers.seai.parser`
- **Package:** `src.providers.seai`
- **Lines:** 225
- **Size:** 7,666 bytes
- **Categories:** AI extraction, audit / logging, database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `workbook_sha256()` (line 74)
- `open_workbook()` (line 83)
- `_parse_qaqc()` (line 92)
- `_classify_sheets()` (line 122)
- `_cell()` (line 142)
- `_parse_authoritative_sheet()` (line 149)
- `analyze_workbook()` (line 190)
- `parse_worksheet()` (line 221)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `an`
- `pathlib`
- `the`
- `typing`

#### Imports

- `.models`
- `__future__`
- `hashlib`
- `logging`
- `openpyxl`
- `pathlib`
- `typing`

### 4.232 `src/providers/seai/tests/conftest.py`

- **Module:** `src.providers.seai.tests.conftest`
- **Package:** `src.providers.seai.tests`
- **Lines:** 89
- **Size:** 2,711 bytes
- **Categories:** AI extraction, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_find_workbook()` (line 26)
- `workbook_path()` (line 42)
- `seai_data()` (line 47)
- `db_url()` (line 55)
- `db_conn()` (line 60)
- `clean_seai()` (line 68)
- `_isolate_seai()` (line 84)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `pathlib`
- `public`
- `src`

#### Imports

- `__future__`
- `os`
- `pathlib`
- `psycopg2`
- `pytest`
- `src.providers.seai`

### 4.233 `src/providers/seai/tests/test_defra_regression.py`

- **Module:** `src.providers.seai.tests.test_defra_regression`
- **Package:** `src.providers.seai.tests`
- **Lines:** 217
- **Size:** 7,843 bytes
- **Categories:** AI extraction, calculation, emission factors, factor matching, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `_FakeSink` (line 157; bases: `-`)
  - `__init__()` (line 160)
  - `async save_snapshot()` (line 164)
  - `async create()` (line 170)
  - `async save()` (line 180)

#### Top-Level Functions

- `_backend_factor()` (line 46)
- `seai_and_defra_diesel()` (line 66)
- `_match()` (line 110)
- `test_country_selection_prevents_gb_ie_confusion()` (line 124)
- `test_defra_gb_matching_still_works()` (line 145)
- `test_calculation_with_seai_factor_unchanged()` (line 189)
- `test_domain_calculation_contract_unchanged()` (line 210)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `datetime`
- `decimal`
- `domain`
- `engines`
- `infra`
- `pathlib`
- `public`
- `src`
- `the`
- `typing`

#### Imports

- `__future__`
- `datetime`
- `decimal`
- `domain.calculation`
- `domain.factor`
- `domain.matching`
- `engines.calculation`
- `engines.factor_matching`
- `infra.search_index`
- `pathlib`
- `pytest`
- `src.providers.seai`
- `sys`
- `typing`

### 4.234 `src/providers/seai/tests/test_import.py`

- **Module:** `src.providers.seai.tests.test_import`
- **Package:** `src.providers.seai.tests`
- **Lines:** 152
- **Size:** 5,974 bytes
- **Categories:** AI extraction, CSV / Excel, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_count()` (line 20)
- `test_import_creates_batch_and_20_factors()` (line 25)
- `test_every_factor_linked_to_batch()` (line 74)
- `test_import_is_idempotent()` (line 86)
- `test_import_does_not_modify_existing_defra_rows()` (line 110)
- `test_imported_multipliers_match_approved_spec()` (line 132)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `decimal`
- `public`
- `src`

#### Imports

- `__future__`
- `decimal`
- `pytest`
- `src.providers.seai`

### 4.235 `src/providers/seai/tests/test_mapper.py`

- **Module:** `src.providers.seai.tests.test_mapper`
- **Package:** `src.providers.seai.tests`
- **Lines:** 158
- **Size:** 4,853 bytes
- **Categories:** AI extraction, database / repository, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `mapped()` (line 70)
- `test_mapping_classifies_20_and_8()` (line 75)
- `test_mapping_imported_names()` (line 81)
- `test_mapping_skipped_names_and_reasons()` (line 86)
- `test_mapping_values_units_scopes()` (line 92)
- `test_mapping_labels_use_canonical_form()` (line 102)
- `test_electricity_pair_not_collapsed()` (line 110)
- `test_biodiesel_me_imported_with_value()` (line 116)
- `test_gas_gcv_skipped_ncv_imported()` (line 122)
- `test_co2_only_semantics()` (line 130)
- `test_no_duplicate_natural_keys()` (line 140)
- `test_map_row_unit_mismatch_never_generates_new_unit()` (line 146)
- `test_map_row_on_gcv_skips()` (line 152)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `decimal`
- `src`
- `the`

#### Imports

- `__future__`
- `decimal`
- `pytest`
- `src.providers.seai`
- `src.providers.seai.models`

### 4.236 `src/providers/seai/tests/test_parser.py`

- **Module:** `src.providers.seai.tests.test_parser`
- **Package:** `src.providers.seai.tests`
- **Lines:** 102
- **Size:** 3,524 bytes
- **Categories:** AI extraction, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `test_workbook_exists()` (line 48)
- `test_workbook_sha256_is_sha256_hexdigest()` (line 53)
- `test_parser_returns_28_source_rows()` (line 59)
- `test_parser_row_names_and_sections()` (line 63)
- `test_parser_authoritative_sheet_only()` (line 68)
- `test_parser_metadata_discovered()` (line 77)
- `test_open_workbook_reads_cached_values()` (line 83)
- `test_no_other_sheet_produces_factors()` (line 93)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `src`

#### Imports

- `__future__`
- `hashlib`
- `pytest`
- `src.providers.seai`
- `src.providers.seai.parser`

### 4.237 `src/providers/seai/tests/test_validator.py`

- **Module:** `src.providers.seai.tests.test_validator`
- **Package:** `src.providers.seai.tests`
- **Lines:** 140
- **Size:** 4,632 bytes
- **Categories:** AI extraction, database / repository, factor provider, validation / QA
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `canonical()` (line 23)
- `test_canonical_mapping_passes()` (line 28)
- `test_remove_one_factor_fails()` (line 35)
- `test_add_extra_factor_fails()` (line 42)
- `test_missing_skip_row_fails()` (line 52)
- `test_missing_electricity_pair_fails()` (line 59)
- `test_electricity_consumption_required()` (line 67)
- `test_removing_biodiesel_me_fails()` (line 75)
- `test_gcv_must_be_skipped()` (line 83)
- `test_wrong_country_fails()` (line 90)
- `test_negative_multiplier_fails()` (line 99)
- `test_unsupported_unit_fails()` (line 108)
- `test_duplicate_natural_key_fails()` (line 117)
- `test_skip_reason_counts_enforced()` (line 126)
- `test_factor_source_and_set_fields()` (line 135)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `decimal`
- `src`

#### Imports

- `__future__`
- `copy`
- `decimal`
- `pytest`
- `src.providers.seai`
- `src.providers.seai.models`
- `src.providers.seai.validator`

### 4.238 `src/providers/seai/validator.py`

- **Module:** `src.providers.seai.validator`
- **Package:** `src.providers.seai`
- **Lines:** 129
- **Size:** 5,274 bytes
- **Categories:** AI extraction, database / repository, factor provider, validation / QA
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `_issue()` (line 41)
- `validate()` (line 45)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `__future__`
- `collections`

#### Imports

- `.models`
- `__future__`
- `collections`

### 4.239 `test_endpoints.py`

- **Module:** `test_endpoints`
- **Package:** `test_endpoints`
- **Lines:** 130
- **Size:** 4,367 bytes
- **Categories:** AI extraction, API
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `load_routes_from_markdown()` (line 14)
- `async test_endpoint()` (line 54)
- `async test_all_endpoints()` (line 79)
- `main()` (line 120)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `pathlib`
- `typing`

#### Imports

- `aiohttp`
- `asyncio`
- `json`
- `pathlib`
- `re`
- `sys`
- `typing`

### 4.240 `tools/carbon_data_factory/analyze_project.py`

- **Module:** `tools.carbon_data_factory.analyze_project`
- **Package:** `tools.carbon_data_factory`
- **Lines:** 33
- **Size:** 1,292 bytes
- **Categories:** emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `analyze_project()` (line 3)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `os`

### 4.241 `tools/carbon_data_factory/importers/__init__.py`

- **Module:** `tools.carbon_data_factory.importers`
- **Package:** `tools.carbon_data_factory`
- **Lines:** 4
- **Size:** 39 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.242 `tools/carbon_data_factory/importers/base_importer.py`

- **Module:** `tools.carbon_data_factory.importers.base_importer`
- **Package:** `tools.carbon_data_factory.importers`
- **Lines:** 13
- **Size:** 254 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `BaseImporter` (line 6; bases: `ABC`)
  - `run()` (line 10)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `abc`

#### Imports

- `abc`

### 4.243 `tools/carbon_data_factory/importers/orchestrator.py`

- **Module:** `tools.carbon_data_factory.importers.orchestrator`
- **Package:** `tools.carbon_data_factory.importers`
- **Lines:** 14
- **Size:** 341 bytes
- **Categories:** CSV / Excel, emission factors, workflow
- **V3 impact:** **NO CHANGE**

#### Classes

- `ImportOrchestrator` (line 3; bases: `-`)
  - `__init__()` (line 6)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.244 `tools/carbon_data_factory/importers/providers/__init__.py`

- **Module:** `tools.carbon_data_factory.importers.providers`
- **Package:** `tools.carbon_data_factory.importers`
- **Lines:** 4
- **Size:** 39 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.245 `tools/carbon_data_factory/importers/providers/defra/__init__.py`

- **Module:** `tools.carbon_data_factory.importers.providers.defra`
- **Package:** `tools.carbon_data_factory.importers.providers`
- **Lines:** 4
- **Size:** 44 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.246 `tools/carbon_data_factory/importers/providers/defra/importer.py`

- **Module:** `tools.carbon_data_factory.importers.providers.defra.importer`
- **Package:** `tools.carbon_data_factory.importers.providers.defra`
- **Lines:** 12
- **Size:** 254 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `DefraImporter` (line 6; bases: `BaseImporter`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...base_importer`

### 4.247 `tools/carbon_data_factory/importers/providers/defra/normalizer.py`

- **Module:** `tools.carbon_data_factory.importers.providers.defra.normalizer`
- **Package:** `tools.carbon_data_factory.importers.providers.defra`
- **Lines:** 12
- **Size:** 279 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `DefraNormalizer` (line 6; bases: `NormalizerStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.normalizer`

### 4.248 `tools/carbon_data_factory/importers/providers/defra/parser.py`

- **Module:** `tools.carbon_data_factory.importers.providers.defra.parser`
- **Package:** `tools.carbon_data_factory.importers.providers.defra`
- **Lines:** 12
- **Size:** 256 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `DefraExcelParser` (line 6; bases: `ParserStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.parser`

### 4.249 `tools/carbon_data_factory/importers/providers/defra/pivoter.py`

- **Module:** `tools.carbon_data_factory.importers.providers.defra.pivoter`
- **Package:** `tools.carbon_data_factory.importers.providers.defra`
- **Lines:** 12
- **Size:** 265 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `DefraPivoter` (line 6; bases: `PivoterStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.pivoter`

### 4.250 `tools/carbon_data_factory/importers/providers/defra/schema.py`

- **Module:** `tools.carbon_data_factory.importers.providers.defra.schema`
- **Package:** `tools.carbon_data_factory.importers.providers.defra`
- **Lines:** 8
- **Size:** 117 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.251 `tools/carbon_data_factory/importers/providers/defra/transformer.py`

- **Module:** `tools.carbon_data_factory.importers.providers.defra.transformer`
- **Package:** `tools.carbon_data_factory.importers.providers.defra`
- **Lines:** 12
- **Size:** 285 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `DefraTransformer` (line 6; bases: `TransformerStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.transformer`

### 4.252 `tools/carbon_data_factory/importers/providers/defra/validator.py`

- **Module:** `tools.carbon_data_factory.importers.providers.defra.validator`
- **Package:** `tools.carbon_data_factory.importers.providers.defra`
- **Lines:** 12
- **Size:** 270 bytes
- **Categories:** CSV / Excel, emission factors, factor provider, validation / QA
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `DefraValidator` (line 6; bases: `ValidatorStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.validator`

### 4.253 `tools/carbon_data_factory/importers/providers/epa/__init__.py`

- **Module:** `tools.carbon_data_factory.importers.providers.epa`
- **Package:** `tools.carbon_data_factory.importers.providers`
- **Lines:** 4
- **Size:** 42 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.254 `tools/carbon_data_factory/importers/providers/epa/importer.py`

- **Module:** `tools.carbon_data_factory.importers.providers.epa.importer`
- **Package:** `tools.carbon_data_factory.importers.providers.epa`
- **Lines:** 12
- **Size:** 250 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `EpaImporter` (line 6; bases: `BaseImporter`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...base_importer`

### 4.255 `tools/carbon_data_factory/importers/providers/epa/normalizer.py`

- **Module:** `tools.carbon_data_factory.importers.providers.epa.normalizer`
- **Package:** `tools.carbon_data_factory.importers.providers.epa`
- **Lines:** 12
- **Size:** 275 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `EpaNormalizer` (line 6; bases: `NormalizerStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.normalizer`

### 4.256 `tools/carbon_data_factory/importers/providers/epa/parser.py`

- **Module:** `tools.carbon_data_factory.importers.providers.epa.parser`
- **Package:** `tools.carbon_data_factory.importers.providers.epa`
- **Lines:** 12
- **Size:** 242 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `EpaParser` (line 6; bases: `ParserStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.parser`

### 4.257 `tools/carbon_data_factory/importers/providers/epa/schema.py`

- **Module:** `tools.carbon_data_factory.importers.providers.epa.schema`
- **Package:** `tools.carbon_data_factory.importers.providers.epa`
- **Lines:** 8
- **Size:** 115 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.258 `tools/carbon_data_factory/importers/providers/epa/transformer.py`

- **Module:** `tools.carbon_data_factory.importers.providers.epa.transformer`
- **Package:** `tools.carbon_data_factory.importers.providers.epa`
- **Lines:** 12
- **Size:** 281 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `EpaTransformer` (line 6; bases: `TransformerStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.transformer`

### 4.259 `tools/carbon_data_factory/importers/providers/epa/validator.py`

- **Module:** `tools.carbon_data_factory.importers.providers.epa.validator`
- **Package:** `tools.carbon_data_factory.importers.providers.epa`
- **Lines:** 12
- **Size:** 266 bytes
- **Categories:** CSV / Excel, emission factors, factor provider, validation / QA
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `EpaValidator` (line 6; bases: `ValidatorStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.validator`

### 4.260 `tools/carbon_data_factory/importers/providers/seai/__init__.py`

- **Module:** `tools.carbon_data_factory.importers.providers.seai`
- **Package:** `tools.carbon_data_factory.importers.providers`
- **Lines:** 4
- **Size:** 43 bytes
- **Categories:** AI extraction, CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.261 `tools/carbon_data_factory/importers/providers/seai/importer.py`

- **Module:** `tools.carbon_data_factory.importers.providers.seai.importer`
- **Package:** `tools.carbon_data_factory.importers.providers.seai`
- **Lines:** 12
- **Size:** 252 bytes
- **Categories:** AI extraction, CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `SeaiImporter` (line 6; bases: `BaseImporter`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...base_importer`

### 4.262 `tools/carbon_data_factory/importers/providers/seai/normalizer.py`

- **Module:** `tools.carbon_data_factory.importers.providers.seai.normalizer`
- **Package:** `tools.carbon_data_factory.importers.providers.seai`
- **Lines:** 12
- **Size:** 277 bytes
- **Categories:** AI extraction, CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `SeaiNormalizer` (line 6; bases: `NormalizerStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.normalizer`

### 4.263 `tools/carbon_data_factory/importers/providers/seai/parser.py`

- **Module:** `tools.carbon_data_factory.importers.providers.seai.parser`
- **Package:** `tools.carbon_data_factory.importers.providers.seai`
- **Lines:** 12
- **Size:** 244 bytes
- **Categories:** AI extraction, CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `SeaiParser` (line 6; bases: `ParserStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.parser`

### 4.264 `tools/carbon_data_factory/importers/providers/seai/schema.py`

- **Module:** `tools.carbon_data_factory.importers.providers.seai.schema`
- **Package:** `tools.carbon_data_factory.importers.providers.seai`
- **Lines:** 8
- **Size:** 116 bytes
- **Categories:** AI extraction, CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.265 `tools/carbon_data_factory/importers/providers/seai/transformer.py`

- **Module:** `tools.carbon_data_factory.importers.providers.seai.transformer`
- **Package:** `tools.carbon_data_factory.importers.providers.seai`
- **Lines:** 12
- **Size:** 283 bytes
- **Categories:** AI extraction, CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `SeaiTransformer` (line 6; bases: `TransformerStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.transformer`

### 4.266 `tools/carbon_data_factory/importers/providers/seai/validator.py`

- **Module:** `tools.carbon_data_factory.importers.providers.seai.validator`
- **Package:** `tools.carbon_data_factory.importers.providers.seai`
- **Lines:** 12
- **Size:** 268 bytes
- **Categories:** AI extraction, CSV / Excel, emission factors, factor provider, validation / QA
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- `SeaiValidator` (line 6; bases: `ValidatorStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `...stages.validator`

### 4.267 `tools/carbon_data_factory/importers/shared/__init__.py`

- **Module:** `tools.carbon_data_factory.importers.shared`
- **Package:** `tools.carbon_data_factory.importers`
- **Lines:** 4
- **Size:** 46 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.268 `tools/carbon_data_factory/importers/shared/change_detector.py`

- **Module:** `tools.carbon_data_factory.importers.shared.change_detector`
- **Package:** `tools.carbon_data_factory.importers.shared`
- **Lines:** 12
- **Size:** 329 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `detect_changes()` (line 3)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.269 `tools/carbon_data_factory/importers/shared/db.py`

- **Module:** `tools.carbon_data_factory.importers.shared.db`
- **Package:** `tools.carbon_data_factory.importers.shared`
- **Lines:** 6
- **Size:** 117 bytes
- **Categories:** CSV / Excel, database / repository, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `get_connection()` (line 3)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.270 `tools/carbon_data_factory/importers/shared/hierarchy.py`

- **Module:** `tools.carbon_data_factory.importers.shared.hierarchy`
- **Package:** `tools.carbon_data_factory.importers.shared`
- **Lines:** 6
- **Size:** 180 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `build_hierarchy()` (line 3)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `flat`

#### Imports

- None detected.

### 4.271 `tools/carbon_data_factory/importers/shared/storage.py`

- **Module:** `tools.carbon_data_factory.importers.shared.storage`
- **Package:** `tools.carbon_data_factory.importers.shared`
- **Lines:** 11
- **Size:** 200 bytes
- **Categories:** CSV / Excel, Storage, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `read_file()` (line 3)
- `write_file()` (line 8)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.272 `tools/carbon_data_factory/importers/shared/units.py`

- **Module:** `tools.carbon_data_factory.importers.shared.units`
- **Package:** `tools.carbon_data_factory.importers.shared`
- **Lines:** 12
- **Size:** 228 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `normalize_unit()` (line 6)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.273 `tools/carbon_data_factory/importers/shared/validators.py`

- **Module:** `tools.carbon_data_factory.importers.shared.validators`
- **Package:** `tools.carbon_data_factory.importers.shared`
- **Lines:** 6
- **Size:** 154 bytes
- **Categories:** CSV / Excel, emission factors, validation / QA
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `is_non_empty()` (line 3)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.274 `tools/carbon_data_factory/importers/stages/__init__.py`

- **Module:** `tools.carbon_data_factory.importers.stages`
- **Package:** `tools.carbon_data_factory.importers`
- **Lines:** 4
- **Size:** 45 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- None detected.

### 4.275 `tools/carbon_data_factory/importers/stages/base_stage.py`

- **Module:** `tools.carbon_data_factory.importers.stages.base_stage`
- **Package:** `tools.carbon_data_factory.importers.stages`
- **Lines:** 13
- **Size:** 268 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `BaseStage` (line 6; bases: `ABC`)
  - `run()` (line 10)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `abc`

#### Imports

- `abc`

### 4.276 `tools/carbon_data_factory/importers/stages/importer.py`

- **Module:** `tools.carbon_data_factory.importers.stages.importer`
- **Package:** `tools.carbon_data_factory.importers.stages`
- **Lines:** 12
- **Size:** 221 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `ImporterStage` (line 6; bases: `BaseStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.base_stage`

### 4.277 `tools/carbon_data_factory/importers/stages/normalizer.py`

- **Module:** `tools.carbon_data_factory.importers.stages.normalizer`
- **Package:** `tools.carbon_data_factory.importers.stages`
- **Lines:** 12
- **Size:** 243 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `NormalizerStage` (line 6; bases: `BaseStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.base_stage`

### 4.278 `tools/carbon_data_factory/importers/stages/parser.py`

- **Module:** `tools.carbon_data_factory.importers.stages.parser`
- **Package:** `tools.carbon_data_factory.importers.stages`
- **Lines:** 12
- **Size:** 232 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `ParserStage` (line 6; bases: `BaseStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.base_stage`

### 4.279 `tools/carbon_data_factory/importers/stages/pivoter.py`

- **Module:** `tools.carbon_data_factory.importers.stages.pivoter`
- **Package:** `tools.carbon_data_factory.importers.stages`
- **Lines:** 12
- **Size:** 235 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `PivoterStage` (line 6; bases: `BaseStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.base_stage`

### 4.280 `tools/carbon_data_factory/importers/stages/transformer.py`

- **Module:** `tools.carbon_data_factory.importers.stages.transformer`
- **Package:** `tools.carbon_data_factory.importers.stages`
- **Lines:** 12
- **Size:** 258 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `TransformerStage` (line 6; bases: `BaseStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.base_stage`

### 4.281 `tools/carbon_data_factory/importers/stages/validator.py`

- **Module:** `tools.carbon_data_factory.importers.stages.validator`
- **Package:** `tools.carbon_data_factory.importers.stages`
- **Lines:** 12
- **Size:** 223 bytes
- **Categories:** CSV / Excel, emission factors, validation / QA
- **V3 impact:** **NO CHANGE**

#### Classes

- `ValidatorStage` (line 6; bases: `BaseStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.base_stage`

### 4.282 `tools/carbon_data_factory/importers/stages/verifier.py`

- **Module:** `tools.carbon_data_factory.importers.stages.verifier`
- **Package:** `tools.carbon_data_factory.importers.stages`
- **Lines:** 12
- **Size:** 220 bytes
- **Categories:** CSV / Excel, emission factors
- **V3 impact:** **NO CHANGE**

#### Classes

- `VerifierStage` (line 6; bases: `BaseStage`)
  - `run()` (line 9)

#### Top-Level Functions

- None detected.

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- None detected.

#### Imports

- `.base_stage`

### 4.283 `tools/carbon_data_factory/importers/tests/integration/test_defra_import.py`

- **Module:** `tools.carbon_data_factory.importers.tests.integration.test_defra_import`
- **Package:** `tools.carbon_data_factory.importers.tests.integration`
- **Lines:** 9
- **Size:** 220 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `test_defra_import_placeholder()` (line 6)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `importers`

#### Imports

- None detected.

### 4.284 `tools/carbon_data_factory/importers/tests/unit/test_defra_parser.py`

- **Module:** `tools.carbon_data_factory.importers.tests.unit.test_defra_parser`
- **Package:** `tools.carbon_data_factory.importers.tests.unit`
- **Lines:** 9
- **Size:** 203 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `test_defra_parser_placeholder()` (line 6)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `importers`

#### Imports

- None detected.

### 4.285 `tools/carbon_data_factory/importers/tests/unit/test_defra_pivoter.py`

- **Module:** `tools.carbon_data_factory.importers.tests.unit.test_defra_pivoter`
- **Package:** `tools.carbon_data_factory.importers.tests.unit`
- **Lines:** 9
- **Size:** 193 bytes
- **Categories:** CSV / Excel, emission factors, factor provider
- **Provider type:** **EMISSION-FACTOR PROVIDER**
- **V3 impact:** **NO CHANGE**

#### Classes

- None detected.

#### Top-Level Functions

- `test_defra_pivoter_placeholder()` (line 6)

#### API Routes

- None detected.

#### Database / Supabase Tables Detected

- `importers`

#### Imports

- None detected.

## 5. Architecture Category Index

### AI extraction

- `backend/data/audit.py`
- `backend/data/documents.py`
- `backend/data/emission_factors.py`
- `backend/data/emissions_logs.py`
- `backend/data/events.py`
- `backend/data/factor_aliases.py`
- `backend/data/imports.py`
- `backend/data/organizations.py`
- `backend/data/reports.py`
- `backend/domain/__init__.py`
- `backend/domain/audit.py`
- `backend/domain/benchmarking.py`
- `backend/domain/calculation.py`
- `backend/domain/document.py`
- `backend/domain/factor.py`
- `backend/domain/matching.py`
- `backend/domain/organization.py`
- `backend/domain/provider.py`
- `backend/domain/report.py`
- `backend/domain/validation.py`
- `backend/domain/workflow.py`
- `backend/engines/__init__.py`
- `backend/engines/ai_extraction.py`
- `backend/engines/benchmarking.py`
- `backend/engines/calculation.py`
- `backend/engines/extraction.py`
- `backend/engines/factor_matching.py`
- `backend/engines/matching_stages.py`
- `backend/engines/report_generation.py`
- `backend/engines/validation.py`
- `backend/engines/workflow.py`
- `backend/infra/audit_logger.py`
- `backend/infra/event_bus.py`
- `backend/infra/llm_client.py`
- `backend/infra/search_index.py`
- `backend/main copy 2.py`
- `backend/main copy.py`
- `backend/main.py`
- `backend/routes/admin/email_templates.py`
- `backend/routes/admin/extraction.py`
- `backend/routes/admin/staff.py`
- `backend/routes/documents_main.py`
- `backend/routes/organizations/members.py`
- `backend/routes/upload.py`
- `backend/routes/users.py`
- `backend/routes/waitlist.py`
- `backend/tests/integration/conftest.py`
- `backend/tests/integration/test_ai_extraction.py`
- `backend/tests/integration/test_audit.py`
- `backend/tests/integration/test_audit_logger.py`
- `backend/tests/integration/test_calculation.py`
- `backend/tests/integration/test_emission_factors.py`
- `backend/tests/integration/test_emissions_logs.py`
- `backend/tests/integration/test_event_bus.py`
- `backend/tests/integration/test_events.py`
- `backend/tests/integration/test_extraction.py`
- `backend/tests/integration/test_factor_aliases.py`
- `backend/tests/integration/test_factor_matching.py`
- `backend/tests/integration/test_imports.py`
- `backend/tests/integration/test_llm_client.py`
- `backend/tests/integration/test_organizations.py`
- `backend/tests/integration/test_search_index.py`
- `backend/tests/integration/test_workflow.py`
- `backend/tests/test_failing_endpoints.py`
- `backend/tests/unit/domain/__init__.py`
- `backend/tests/unit/domain/test_audit.py`
- `backend/tests/unit/domain/test_benchmarking.py`
- `backend/tests/unit/domain/test_calculation.py`
- `backend/tests/unit/domain/test_document.py`
- `backend/tests/unit/domain/test_factor.py`
- `backend/tests/unit/domain/test_matching.py`
- `backend/tests/unit/domain/test_organization.py`
- `backend/tests/unit/domain/test_provider.py`
- `backend/tests/unit/domain/test_report.py`
- `backend/tests/unit/domain/test_validation.py`
- `backend/tests/unit/domain/test_workflow.py`
- `backend/tests/unit/engines/test_ai_extraction.py`
- `backend/tests/unit/engines/test_benchmarking.py`
- `backend/tests/unit/engines/test_calculation.py`
- `backend/tests/unit/engines/test_extraction.py`
- `backend/tests/unit/engines/test_factor_matching.py`
- `backend/tests/unit/engines/test_matching_stages.py`
- `backend/tests/unit/engines/test_validation.py`
- `backend/tests/unit/engines/test_workflow.py`
- `backend/tests/unit/infra/test_audit_logger.py`
- `backend/tests/unit/infra/test_event_bus.py`
- `backend/tests/unit/infra/test_llm_client.py`
- `backend/tests/unit/infra/test_search_index.py`
- `backend/utils/__init__.py`
- `backend/utils/email.py`
- `src/commands/import_seai.py`
- `src/providers/seai/__init__.py`
- `src/providers/seai/exporter.py`
- `src/providers/seai/mapper.py`
- `src/providers/seai/models.py`
- `src/providers/seai/parser.py`
- `src/providers/seai/tests/conftest.py`
- `src/providers/seai/tests/test_defra_regression.py`
- `src/providers/seai/tests/test_import.py`
- `src/providers/seai/tests/test_mapper.py`
- `src/providers/seai/tests/test_parser.py`
- `src/providers/seai/tests/test_validator.py`
- `src/providers/seai/validator.py`
- `test_endpoints.py`
- `tools/carbon_data_factory/importers/providers/seai/__init__.py`
- `tools/carbon_data_factory/importers/providers/seai/importer.py`
- `tools/carbon_data_factory/importers/providers/seai/normalizer.py`
- `tools/carbon_data_factory/importers/providers/seai/parser.py`
- `tools/carbon_data_factory/importers/providers/seai/schema.py`
- `tools/carbon_data_factory/importers/providers/seai/transformer.py`
- `tools/carbon_data_factory/importers/providers/seai/validator.py`

### API

- `backend/auth.py`
- `backend/main copy 2.py`
- `backend/main copy.py`
- `backend/main.py`
- `backend/middleware/rate_limit.py`
- `backend/report_generator.py`
- `backend/routes/__init__.py`
- `backend/routes/admin/__init__.py`
- `backend/routes/admin/analytics.py`
- `backend/routes/admin/assignments.py`
- `backend/routes/admin/audit.py`
- `backend/routes/admin/audit_logs.py`
- `backend/routes/admin/beta.py`
- `backend/routes/admin/bulk.py`
- `backend/routes/admin/dashboard.py`
- `backend/routes/admin/defra.py`
- `backend/routes/admin/document-types.py`
- `backend/routes/admin/email_templates.py`
- `backend/routes/admin/extraction.py`
- `backend/routes/admin/logs.py`
- `backend/routes/admin/permissions.py`
- `backend/routes/admin/review_history.py`
- `backend/routes/admin/reviews.py`
- `backend/routes/admin/settings.py`
- `backend/routes/admin/staff.py`
- `backend/routes/admin/workload.py`
- `backend/routes/communication.py`
- `backend/routes/customer_dashboard.py`
- `backend/routes/customer_documents.py`
- `backend/routes/customer_verifications.py`
- `backend/routes/document_activity.py`
- `backend/routes/documents/__init__.py`
- `backend/routes/documents_main.py`
- `backend/routes/drafts.py`
- `backend/routes/drafts_enhanced.py`
- `backend/routes/emissions.py`
- `backend/routes/feedback.py`
- `backend/routes/glossary.py`
- `backend/routes/logs.py`
- `backend/routes/notifications.py`
- `backend/routes/organizations/__init__.py`
- `backend/routes/organizations/analytics.py`
- `backend/routes/organizations/assets.py`
- `backend/routes/organizations/bulk.py`
- `backend/routes/organizations/dashboard.py`
- `backend/routes/organizations/data.py`
- `backend/routes/organizations/exports.py`
- `backend/routes/organizations/files.py`
- `backend/routes/organizations/management.py`
- `backend/routes/organizations/members.py`
- `backend/routes/organizations/metadata.py`
- `backend/routes/organizations/team.py`
- `backend/routes/reference.py`
- `backend/routes/reports.py`
- `backend/routes/upload.py`
- `backend/routes/users.py`
- `backend/routes/waitlist.py`
- `backend/tests/test_all_endpoints.py`
- `backend/tests/test_api.py`
- `backend/tests/test_api_simple.py`
- `backend/tests/test_failing_endpoints.py`
- `generate_api_docs.py`
- `list_endpoints.py`
- `quick_api_ref.py`
- `test_endpoints.py`

### CSV / Excel

- `backend/data/__init__.py`
- `backend/data/audit.py`
- `backend/data/imports.py`
- `backend/routes/admin/audit.py`
- `backend/routes/admin/review_history.py`
- `backend/routes/admin/staff.py`
- `backend/routes/document_activity.py`
- `backend/routes/emissions.py`
- `backend/routes/organizations/exports.py`
- `backend/tests/check_imports.py`
- `backend/tests/export_postman.py`
- `backend/tests/fix_imports.py`
- `backend/tests/integration/test_emission_factors.py`
- `backend/tests/integration/test_imports.py`
- `demodatagen/generators/base_generator.py`
- `demodatagen/organizations.py`
- `demodatagen/scripts/export_to_sql.py`
- `demodatagen/scripts/validate_data.py`
- `export_postman.py`
- `generate_messy_fuel_csv.py`
- `generate_messy_utility_csv.py`
- `src/commands/import_defra.py`
- `src/commands/import_seai.py`
- `src/providers/defra/__init__.py`
- `src/providers/defra/exporter.py`
- `src/providers/seai/__init__.py`
- `src/providers/seai/exporter.py`
- `src/providers/seai/tests/test_import.py`
- `tools/carbon_data_factory/importers/__init__.py`
- `tools/carbon_data_factory/importers/base_importer.py`
- `tools/carbon_data_factory/importers/orchestrator.py`
- `tools/carbon_data_factory/importers/providers/__init__.py`
- `tools/carbon_data_factory/importers/providers/defra/__init__.py`
- `tools/carbon_data_factory/importers/providers/defra/importer.py`
- `tools/carbon_data_factory/importers/providers/defra/normalizer.py`
- `tools/carbon_data_factory/importers/providers/defra/parser.py`
- `tools/carbon_data_factory/importers/providers/defra/pivoter.py`
- `tools/carbon_data_factory/importers/providers/defra/schema.py`
- `tools/carbon_data_factory/importers/providers/defra/transformer.py`
- `tools/carbon_data_factory/importers/providers/defra/validator.py`
- `tools/carbon_data_factory/importers/providers/epa/__init__.py`
- `tools/carbon_data_factory/importers/providers/epa/importer.py`
- `tools/carbon_data_factory/importers/providers/epa/normalizer.py`
- `tools/carbon_data_factory/importers/providers/epa/parser.py`
- `tools/carbon_data_factory/importers/providers/epa/schema.py`
- `tools/carbon_data_factory/importers/providers/epa/transformer.py`
- `tools/carbon_data_factory/importers/providers/epa/validator.py`
- `tools/carbon_data_factory/importers/providers/seai/__init__.py`
- `tools/carbon_data_factory/importers/providers/seai/importer.py`
- `tools/carbon_data_factory/importers/providers/seai/normalizer.py`
- `tools/carbon_data_factory/importers/providers/seai/parser.py`
- `tools/carbon_data_factory/importers/providers/seai/schema.py`
- `tools/carbon_data_factory/importers/providers/seai/transformer.py`
- `tools/carbon_data_factory/importers/providers/seai/validator.py`
- `tools/carbon_data_factory/importers/shared/__init__.py`
- `tools/carbon_data_factory/importers/shared/change_detector.py`
- `tools/carbon_data_factory/importers/shared/db.py`
- `tools/carbon_data_factory/importers/shared/hierarchy.py`
- `tools/carbon_data_factory/importers/shared/storage.py`
- `tools/carbon_data_factory/importers/shared/units.py`
- `tools/carbon_data_factory/importers/shared/validators.py`
- `tools/carbon_data_factory/importers/stages/__init__.py`
- `tools/carbon_data_factory/importers/stages/base_stage.py`
- `tools/carbon_data_factory/importers/stages/importer.py`
- `tools/carbon_data_factory/importers/stages/normalizer.py`
- `tools/carbon_data_factory/importers/stages/parser.py`
- `tools/carbon_data_factory/importers/stages/pivoter.py`
- `tools/carbon_data_factory/importers/stages/transformer.py`
- `tools/carbon_data_factory/importers/stages/validator.py`
- `tools/carbon_data_factory/importers/stages/verifier.py`
- `tools/carbon_data_factory/importers/tests/integration/test_defra_import.py`
- `tools/carbon_data_factory/importers/tests/unit/test_defra_parser.py`
- `tools/carbon_data_factory/importers/tests/unit/test_defra_pivoter.py`

### RBAC

- `backend/routes/admin/permissions.py`

### Realtime / communication

- `backend/routes/communication.py`
- `backend/routes/notifications.py`
- `demodatagen/generators/collaboration/generate_conversations.py`
- `demodatagen/generators/collaboration/generate_messages.py`

### Storage

- `backend/auth.py`
- `backend/config.py`
- `backend/database.py`
- `backend/infra/audit_logger.py`
- `backend/infra/config.py`
- `backend/infra/supabase.py`
- `backend/main copy 2.py`
- `backend/main copy.py`
- `backend/report_generator.py`
- `backend/routes/admin/audit_logs.py`
- `backend/routes/admin/dashboard.py`
- `backend/routes/admin/staff.py`
- `backend/routes/admin/workload.py`
- `backend/routes/communication.py`
- `backend/routes/customer_dashboard.py`
- `backend/routes/customer_documents.py`
- `backend/routes/customer_verifications.py`
- `backend/routes/emissions.py`
- `backend/routes/organizations/files.py`
- `backend/routes/organizations/management.py`
- `backend/routes/organizations/members.py`
- `backend/routes/reports.py`
- `backend/routes/users.py`
- `backend/tests/integration/test_config.py`
- `backend/tests/integration/test_infra.py`
- `backend/tests/setup_test_data.py`
- `backend/tests/setup_test_orgs.py`
- `backend/tests/test_all_endpoints.py`
- `backend/tests/test_api_simple.py`
- `backend/tests/test_failing_endpoints.py`
- `backend/utils/organization_utils.py`
- `demodatagen/generators/core/generate_staff_profiles.py`
- `src/providers/defra/exporter.py`
- `tools/carbon_data_factory/importers/shared/storage.py`

### audit / logging

- `backend/core/__init__.py`
- `backend/core/logging.py`
- `backend/data/__init__.py`
- `backend/data/audit.py`
- `backend/data/emissions_logs.py`
- `backend/data/events.py`
- `backend/domain/__init__.py`
- `backend/domain/audit.py`
- `backend/engines/ai_extraction.py`
- `backend/engines/benchmarking.py`
- `backend/engines/calculation.py`
- `backend/engines/extraction.py`
- `backend/engines/factor_matching.py`
- `backend/engines/matching_stages.py`
- `backend/engines/report_generation.py`
- `backend/engines/validation.py`
- `backend/engines/workflow.py`
- `backend/infra/audit_logger.py`
- `backend/infra/event_bus.py`
- `backend/routes/admin/audit.py`
- `backend/routes/admin/audit_logs.py`
- `backend/routes/admin/logs.py`
- `backend/routes/logs.py`
- `backend/tests/audit_code.py`
- `backend/tests/integration/test_ai_extraction.py`
- `backend/tests/integration/test_audit.py`
- `backend/tests/integration/test_audit_logger.py`
- `backend/tests/integration/test_calculation.py`
- `backend/tests/integration/test_emissions_logs.py`
- `backend/tests/integration/test_event_bus.py`
- `backend/tests/integration/test_events.py`
- `backend/tests/integration/test_extraction.py`
- `backend/tests/integration/test_factor_matching.py`
- `backend/tests/integration/test_workflow.py`
- `backend/tests/unit/domain/test_audit.py`
- `backend/tests/unit/engines/test_ai_extraction.py`
- `backend/tests/unit/engines/test_benchmarking.py`
- `backend/tests/unit/engines/test_calculation.py`
- `backend/tests/unit/engines/test_extraction.py`
- `backend/tests/unit/engines/test_factor_matching.py`
- `backend/tests/unit/engines/test_validation.py`
- `backend/tests/unit/engines/test_workflow.py`
- `backend/tests/unit/infra/test_audit_logger.py`
- `backend/tests/unit/infra/test_event_bus.py`
- `backend/tests/unit/test_core.py`
- `backend/utils/audit_logger.py`
- `demodatagen/generators/base_generator.py`
- `demodatagen/generators/carbon/generate_emissions_logs.py`
- `demodatagen/scripts/run_all_generators.py`
- `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/19fc925d-0962-8a3a-8000-0fb8fbe59ca5/scratch/postprocess.py`
- `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/scratch_mm/style.py`
- `src/commands/import_defra.py`
- `src/commands/import_seai.py`
- `src/providers/defra/exporter.py`
- `src/providers/seai/exporter.py`
- `src/providers/seai/parser.py`

### authentication / security

- `backend/auth.py`
- `backend/main copy 2.py`
- `backend/routes/admin/analytics.py`
- `backend/routes/admin/assignments.py`
- `backend/routes/admin/audit.py`
- `backend/routes/admin/audit_logs.py`
- `backend/routes/admin/beta.py`
- `backend/routes/admin/bulk.py`
- `backend/routes/admin/dashboard.py`
- `backend/routes/admin/defra.py`
- `backend/routes/admin/document-types.py`
- `backend/routes/admin/email_templates.py`
- `backend/routes/admin/extraction.py`
- `backend/routes/admin/logs.py`
- `backend/routes/admin/permissions.py`
- `backend/routes/admin/review_history.py`
- `backend/routes/admin/reviews.py`
- `backend/routes/admin/settings.py`
- `backend/routes/admin/staff.py`
- `backend/routes/admin/workload.py`
- `backend/routes/communication.py`
- `backend/routes/customer_dashboard.py`
- `backend/routes/customer_documents.py`
- `backend/routes/customer_verifications.py`
- `backend/routes/document_activity.py`
- `backend/routes/documents_main.py`
- `backend/routes/drafts.py`
- `backend/routes/drafts_enhanced.py`
- `backend/routes/emissions.py`
- `backend/routes/feedback.py`
- `backend/routes/glossary.py`
- `backend/routes/logs.py`
- `backend/routes/notifications.py`
- `backend/routes/organizations/analytics.py`
- `backend/routes/organizations/assets.py`
- `backend/routes/organizations/bulk.py`
- `backend/routes/organizations/dashboard.py`
- `backend/routes/organizations/data.py`
- `backend/routes/organizations/exports.py`
- `backend/routes/organizations/files.py`
- `backend/routes/organizations/management.py`
- `backend/routes/organizations/members.py`
- `backend/routes/organizations/metadata.py`
- `backend/routes/organizations/team.py`
- `backend/routes/reference.py`
- `backend/routes/reports.py`
- `backend/routes/upload.py`
- `backend/routes/users.py`
- `backend/tests/auth_helper.py`
- `backend/tests/create_test_users.py`
- `backend/tests/test_api.py`
- `backend/tests/test_auth_simple.py`

### calculation

- `backend/data/__init__.py`
- `backend/data/emission_factors.py`
- `backend/data/emissions_logs.py`
- `backend/domain/__init__.py`
- `backend/domain/calculation.py`
- `backend/engines/__init__.py`
- `backend/engines/benchmarking.py`
- `backend/engines/calculation.py`
- `backend/engines/report_generation.py`
- `backend/engines/validation.py`
- `backend/engines/workflow.py`
- `backend/process_emissions.py`
- `backend/routes/emissions.py`
- `backend/routes/upload.py`
- `backend/tests/integration/test_calculation.py`
- `backend/tests/integration/test_emission_factors.py`
- `backend/tests/integration/test_emissions_logs.py`
- `backend/tests/integration/test_factor_matching.py`
- `backend/tests/integration/test_search_index.py`
- `backend/tests/integration/test_workflow.py`
- `backend/tests/unit/domain/test_calculation.py`
- `backend/tests/unit/engines/test_benchmarking.py`
- `backend/tests/unit/engines/test_calculation.py`
- `backend/tests/unit/engines/test_validation.py`
- `backend/tests/unit/engines/test_workflow.py`
- `backend/utils/__init__.py`
- `backend/utils/emissions.py`
- `demodatagen/generators/carbon/generate_emissions_logs.py`
- `src/providers/seai/tests/test_defra_regression.py`

### database / repository

- `backend/data/__init__.py`
- `backend/data/reports.py`
- `backend/database.py`
- `backend/domain/__init__.py`
- `backend/domain/report.py`
- `backend/engines/__init__.py`
- `backend/engines/report_generation.py`
- `backend/main copy 2.py`
- `backend/main copy.py`
- `backend/main.py`
- `backend/report_generator.py`
- `backend/routes/admin/analytics.py`
- `backend/routes/admin/assignments.py`
- `backend/routes/admin/audit.py`
- `backend/routes/admin/audit_logs.py`
- `backend/routes/admin/beta.py`
- `backend/routes/admin/bulk.py`
- `backend/routes/admin/dashboard.py`
- `backend/routes/admin/defra.py`
- `backend/routes/admin/document-types.py`
- `backend/routes/admin/email_templates.py`
- `backend/routes/admin/extraction.py`
- `backend/routes/admin/logs.py`
- `backend/routes/admin/permissions.py`
- `backend/routes/admin/review_history.py`
- `backend/routes/admin/reviews.py`
- `backend/routes/admin/settings.py`
- `backend/routes/admin/staff.py`
- `backend/routes/admin/workload.py`
- `backend/routes/communication.py`
- `backend/routes/customer_dashboard.py`
- `backend/routes/customer_documents.py`
- `backend/routes/customer_verifications.py`
- `backend/routes/document_activity.py`
- `backend/routes/documents_main.py`
- `backend/routes/drafts.py`
- `backend/routes/drafts_enhanced.py`
- `backend/routes/emissions.py`
- `backend/routes/feedback.py`
- `backend/routes/glossary.py`
- `backend/routes/logs.py`
- `backend/routes/notifications.py`
- `backend/routes/organizations/analytics.py`
- `backend/routes/organizations/assets.py`
- `backend/routes/organizations/bulk.py`
- `backend/routes/organizations/dashboard.py`
- `backend/routes/organizations/data.py`
- `backend/routes/organizations/exports.py`
- `backend/routes/organizations/files.py`
- `backend/routes/organizations/management.py`
- `backend/routes/organizations/members.py`
- `backend/routes/organizations/metadata.py`
- `backend/routes/organizations/team.py`
- `backend/routes/reference.py`
- `backend/routes/reports.py`
- `backend/routes/upload.py`
- `backend/routes/users.py`
- `backend/routes/waitlist.py`
- `backend/tests/create_test_users.py`
- `backend/tests/integration/test_reports.py`
- `backend/tests/setup_test_data.py`
- `backend/tests/setup_test_orgs.py`
- `backend/tests/unit/domain/test_report.py`
- `backend/tests/verify_setup.py`
- `backend/utils/audit_logger.py`
- `backend/utils/document_classifier.py`
- `backend/utils/staff_workload.py`
- `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/19fc925d-0962-8a3a-8000-0fb8fbe59ca5/scratch/postprocess.py`
- `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/scratch_mm/style.py`
- `src/commands/import_defra.py`
- `src/commands/import_seai.py`
- `src/providers/defra/__init__.py`
- `src/providers/defra/exporter.py`
- `src/providers/defra/mapper.py`
- `src/providers/defra/models.py`
- `src/providers/defra/parser.py`
- `src/providers/defra/validator.py`
- `src/providers/seai/__init__.py`
- `src/providers/seai/exporter.py`
- `src/providers/seai/mapper.py`
- `src/providers/seai/models.py`
- `src/providers/seai/parser.py`
- `src/providers/seai/tests/test_mapper.py`
- `src/providers/seai/tests/test_validator.py`
- `src/providers/seai/validator.py`
- `tools/carbon_data_factory/importers/shared/db.py`

### document processing

- `backend/data/__init__.py`
- `backend/data/documents.py`
- `backend/domain/__init__.py`
- `backend/domain/document.py`
- `backend/engines/ai_extraction.py`
- `backend/engines/extraction.py`
- `backend/engines/workflow.py`
- `backend/routes/admin/assignments.py`
- `backend/routes/admin/document-types.py`
- `backend/routes/customer_documents.py`
- `backend/routes/document_activity.py`
- `backend/routes/documents/__init__.py`
- `backend/routes/documents_main.py`
- `backend/tests/integration/test_ai_extraction.py`
- `backend/tests/integration/test_documents.py`
- `backend/tests/integration/test_extraction.py`
- `backend/tests/integration/test_workflow.py`
- `backend/tests/unit/domain/test_document.py`
- `backend/tests/unit/engines/test_ai_extraction.py`
- `backend/tests/unit/engines/test_extraction.py`
- `backend/tests/unit/engines/test_workflow.py`
- `backend/utils/__init__.py`
- `backend/utils/document_classifier.py`
- `demodatagen/generators/documents/generate_customer_documents.py`
- `demodatagen/generators/documents/generate_document_types.py`

### emission factors

- `backend/data/__init__.py`
- `backend/data/emission_factors.py`
- `backend/data/factor_aliases.py`
- `backend/domain/__init__.py`
- `backend/domain/calculation.py`
- `backend/domain/factor.py`
- `backend/domain/matching.py`
- `backend/engines/__init__.py`
- `backend/engines/benchmarking.py`
- `backend/engines/calculation.py`
- `backend/engines/factor_matching.py`
- `backend/engines/matching_stages.py`
- `backend/engines/report_generation.py`
- `backend/engines/validation.py`
- `backend/engines/workflow.py`
- `backend/infra/search_index.py`
- `backend/tests/integration/test_calculation.py`
- `backend/tests/integration/test_emission_factors.py`
- `backend/tests/integration/test_emissions_logs.py`
- `backend/tests/integration/test_factor_aliases.py`
- `backend/tests/integration/test_factor_matching.py`
- `backend/tests/integration/test_search_index.py`
- `backend/tests/integration/test_workflow.py`
- `backend/tests/unit/domain/test_calculation.py`
- `backend/tests/unit/domain/test_factor.py`
- `backend/tests/unit/domain/test_matching.py`
- `backend/tests/unit/engines/test_benchmarking.py`
- `backend/tests/unit/engines/test_calculation.py`
- `backend/tests/unit/engines/test_factor_matching.py`
- `backend/tests/unit/engines/test_matching_stages.py`
- `backend/tests/unit/engines/test_validation.py`
- `backend/tests/unit/engines/test_workflow.py`
- `backend/tests/unit/infra/test_search_index.py`
- `src/providers/seai/tests/test_defra_regression.py`
- `tools/carbon_data_factory/analyze_project.py`
- `tools/carbon_data_factory/importers/__init__.py`
- `tools/carbon_data_factory/importers/base_importer.py`
- `tools/carbon_data_factory/importers/orchestrator.py`
- `tools/carbon_data_factory/importers/providers/__init__.py`
- `tools/carbon_data_factory/importers/providers/defra/__init__.py`
- `tools/carbon_data_factory/importers/providers/defra/importer.py`
- `tools/carbon_data_factory/importers/providers/defra/normalizer.py`
- `tools/carbon_data_factory/importers/providers/defra/parser.py`
- `tools/carbon_data_factory/importers/providers/defra/pivoter.py`
- `tools/carbon_data_factory/importers/providers/defra/schema.py`
- `tools/carbon_data_factory/importers/providers/defra/transformer.py`
- `tools/carbon_data_factory/importers/providers/defra/validator.py`
- `tools/carbon_data_factory/importers/providers/epa/__init__.py`
- `tools/carbon_data_factory/importers/providers/epa/importer.py`
- `tools/carbon_data_factory/importers/providers/epa/normalizer.py`
- `tools/carbon_data_factory/importers/providers/epa/parser.py`
- `tools/carbon_data_factory/importers/providers/epa/schema.py`
- `tools/carbon_data_factory/importers/providers/epa/transformer.py`
- `tools/carbon_data_factory/importers/providers/epa/validator.py`
- `tools/carbon_data_factory/importers/providers/seai/__init__.py`
- `tools/carbon_data_factory/importers/providers/seai/importer.py`
- `tools/carbon_data_factory/importers/providers/seai/normalizer.py`
- `tools/carbon_data_factory/importers/providers/seai/parser.py`
- `tools/carbon_data_factory/importers/providers/seai/schema.py`
- `tools/carbon_data_factory/importers/providers/seai/transformer.py`
- `tools/carbon_data_factory/importers/providers/seai/validator.py`
- `tools/carbon_data_factory/importers/shared/__init__.py`
- `tools/carbon_data_factory/importers/shared/change_detector.py`
- `tools/carbon_data_factory/importers/shared/db.py`
- `tools/carbon_data_factory/importers/shared/hierarchy.py`
- `tools/carbon_data_factory/importers/shared/storage.py`
- `tools/carbon_data_factory/importers/shared/units.py`
- `tools/carbon_data_factory/importers/shared/validators.py`
- `tools/carbon_data_factory/importers/stages/__init__.py`
- `tools/carbon_data_factory/importers/stages/base_stage.py`
- `tools/carbon_data_factory/importers/stages/importer.py`
- `tools/carbon_data_factory/importers/stages/normalizer.py`
- `tools/carbon_data_factory/importers/stages/parser.py`
- `tools/carbon_data_factory/importers/stages/pivoter.py`
- `tools/carbon_data_factory/importers/stages/transformer.py`
- `tools/carbon_data_factory/importers/stages/validator.py`
- `tools/carbon_data_factory/importers/stages/verifier.py`
- `tools/carbon_data_factory/importers/tests/integration/test_defra_import.py`
- `tools/carbon_data_factory/importers/tests/unit/test_defra_parser.py`
- `tools/carbon_data_factory/importers/tests/unit/test_defra_pivoter.py`

### factor matching

- `backend/data/factor_aliases.py`
- `backend/domain/__init__.py`
- `backend/domain/matching.py`
- `backend/engines/__init__.py`
- `backend/engines/calculation.py`
- `backend/engines/factor_matching.py`
- `backend/engines/matching_stages.py`
- `backend/engines/validation.py`
- `backend/engines/workflow.py`
- `backend/tests/integration/test_factor_aliases.py`
- `backend/tests/integration/test_factor_matching.py`
- `backend/tests/integration/test_workflow.py`
- `backend/tests/unit/domain/test_matching.py`
- `backend/tests/unit/engines/test_calculation.py`
- `backend/tests/unit/engines/test_factor_matching.py`
- `backend/tests/unit/engines/test_matching_stages.py`
- `backend/tests/unit/engines/test_validation.py`
- `backend/tests/unit/engines/test_workflow.py`
- `src/providers/seai/tests/test_defra_regression.py`

### factor provider

- `backend/data/imports.py`
- `backend/domain/__init__.py`
- `backend/domain/provider.py`
- `backend/routes/admin/defra.py`
- `backend/tests/integration/test_imports.py`
- `backend/tests/unit/domain/test_provider.py`
- `demodatagen/generators/core/generate_organizations.py`
- `demodatagen/organizations.py`
- `src/commands/import_defra.py`
- `src/commands/import_seai.py`
- `src/providers/__init__.py`
- `src/providers/defra/__init__.py`
- `src/providers/defra/exporter.py`
- `src/providers/defra/mapper.py`
- `src/providers/defra/models.py`
- `src/providers/defra/parser.py`
- `src/providers/defra/validator.py`
- `src/providers/seai/__init__.py`
- `src/providers/seai/exporter.py`
- `src/providers/seai/mapper.py`
- `src/providers/seai/models.py`
- `src/providers/seai/parser.py`
- `src/providers/seai/tests/conftest.py`
- `src/providers/seai/tests/test_defra_regression.py`
- `src/providers/seai/tests/test_import.py`
- `src/providers/seai/tests/test_mapper.py`
- `src/providers/seai/tests/test_parser.py`
- `src/providers/seai/tests/test_validator.py`
- `src/providers/seai/validator.py`
- `tools/carbon_data_factory/importers/providers/__init__.py`
- `tools/carbon_data_factory/importers/providers/defra/__init__.py`
- `tools/carbon_data_factory/importers/providers/defra/importer.py`
- `tools/carbon_data_factory/importers/providers/defra/normalizer.py`
- `tools/carbon_data_factory/importers/providers/defra/parser.py`
- `tools/carbon_data_factory/importers/providers/defra/pivoter.py`
- `tools/carbon_data_factory/importers/providers/defra/schema.py`
- `tools/carbon_data_factory/importers/providers/defra/transformer.py`
- `tools/carbon_data_factory/importers/providers/defra/validator.py`
- `tools/carbon_data_factory/importers/providers/epa/__init__.py`
- `tools/carbon_data_factory/importers/providers/epa/importer.py`
- `tools/carbon_data_factory/importers/providers/epa/normalizer.py`
- `tools/carbon_data_factory/importers/providers/epa/parser.py`
- `tools/carbon_data_factory/importers/providers/epa/schema.py`
- `tools/carbon_data_factory/importers/providers/epa/transformer.py`
- `tools/carbon_data_factory/importers/providers/epa/validator.py`
- `tools/carbon_data_factory/importers/providers/seai/__init__.py`
- `tools/carbon_data_factory/importers/providers/seai/importer.py`
- `tools/carbon_data_factory/importers/providers/seai/normalizer.py`
- `tools/carbon_data_factory/importers/providers/seai/parser.py`
- `tools/carbon_data_factory/importers/providers/seai/schema.py`
- `tools/carbon_data_factory/importers/providers/seai/transformer.py`
- `tools/carbon_data_factory/importers/providers/seai/validator.py`
- `tools/carbon_data_factory/importers/tests/integration/test_defra_import.py`
- `tools/carbon_data_factory/importers/tests/unit/test_defra_parser.py`
- `tools/carbon_data_factory/importers/tests/unit/test_defra_pivoter.py`

### reporting

- `backend/data/__init__.py`
- `backend/data/reports.py`
- `backend/domain/__init__.py`
- `backend/domain/report.py`
- `backend/engines/__init__.py`
- `backend/engines/report_generation.py`
- `backend/main copy 2.py`
- `backend/main copy.py`
- `backend/report_generator.py`
- `backend/routes/admin/dashboard.py`
- `backend/routes/customer_dashboard.py`
- `backend/routes/organizations/dashboard.py`
- `backend/routes/reports.py`
- `backend/routes/upload.py`
- `backend/tests/integration/test_reports.py`
- `backend/tests/unit/domain/test_report.py`
- `create_admin_dashboard.py`
- `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/19fc925d-0962-8a3a-8000-0fb8fbe59ca5/scratch/postprocess.py`
- `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/scratch_mm/style.py`

### validation / QA

- `backend/domain/__init__.py`
- `backend/domain/validation.py`
- `backend/engines/__init__.py`
- `backend/engines/report_generation.py`
- `backend/engines/validation.py`
- `backend/routes/admin/review_history.py`
- `backend/routes/admin/reviews.py`
- `backend/tests/unit/domain/test_validation.py`
- `backend/tests/unit/engines/test_validation.py`
- `demodatagen/scripts/validate_data.py`
- `demodatagen/utils/data_validators.py`
- `src/providers/defra/__init__.py`
- `src/providers/defra/validator.py`
- `src/providers/seai/__init__.py`
- `src/providers/seai/tests/test_validator.py`
- `src/providers/seai/validator.py`
- `tools/carbon_data_factory/importers/providers/defra/validator.py`
- `tools/carbon_data_factory/importers/providers/epa/validator.py`
- `tools/carbon_data_factory/importers/providers/seai/validator.py`
- `tools/carbon_data_factory/importers/shared/validators.py`
- `tools/carbon_data_factory/importers/stages/validator.py`

### workflow

- `backend/data/events.py`
- `backend/domain/__init__.py`
- `backend/domain/workflow.py`
- `backend/engines/__init__.py`
- `backend/engines/ai_extraction.py`
- `backend/engines/calculation.py`
- `backend/engines/extraction.py`
- `backend/engines/factor_matching.py`
- `backend/engines/report_generation.py`
- `backend/engines/validation.py`
- `backend/engines/workflow.py`
- `backend/infra/event_bus.py`
- `backend/tests/integration/test_ai_extraction.py`
- `backend/tests/integration/test_calculation.py`
- `backend/tests/integration/test_event_bus.py`
- `backend/tests/integration/test_events.py`
- `backend/tests/integration/test_extraction.py`
- `backend/tests/integration/test_factor_matching.py`
- `backend/tests/integration/test_workflow.py`
- `backend/tests/unit/domain/test_workflow.py`
- `backend/tests/unit/engines/test_ai_extraction.py`
- `backend/tests/unit/engines/test_calculation.py`
- `backend/tests/unit/engines/test_extraction.py`
- `backend/tests/unit/engines/test_factor_matching.py`
- `backend/tests/unit/engines/test_validation.py`
- `backend/tests/unit/engines/test_workflow.py`
- `backend/tests/unit/infra/test_event_bus.py`
- `tools/carbon_data_factory/importers/orchestrator.py`

## 6. Provider Architecture Review

### Emission-Factor Provider Modules

- `backend/routes/admin/defra.py`
- `src/commands/import_defra.py`
- `src/commands/import_seai.py`
- `src/providers/defra/__init__.py`
- `src/providers/defra/exporter.py`
- `src/providers/defra/mapper.py`
- `src/providers/defra/models.py`
- `src/providers/defra/parser.py`
- `src/providers/defra/validator.py`
- `src/providers/seai/__init__.py`
- `src/providers/seai/exporter.py`
- `src/providers/seai/mapper.py`
- `src/providers/seai/models.py`
- `src/providers/seai/parser.py`
- `src/providers/seai/tests/conftest.py`
- `src/providers/seai/tests/test_defra_regression.py`
- `src/providers/seai/tests/test_import.py`
- `src/providers/seai/tests/test_mapper.py`
- `src/providers/seai/tests/test_parser.py`
- `src/providers/seai/tests/test_validator.py`
- `src/providers/seai/validator.py`
- `tools/carbon_data_factory/importers/providers/defra/__init__.py`
- `tools/carbon_data_factory/importers/providers/defra/importer.py`
- `tools/carbon_data_factory/importers/providers/defra/normalizer.py`
- `tools/carbon_data_factory/importers/providers/defra/parser.py`
- `tools/carbon_data_factory/importers/providers/defra/pivoter.py`
- `tools/carbon_data_factory/importers/providers/defra/schema.py`
- `tools/carbon_data_factory/importers/providers/defra/transformer.py`
- `tools/carbon_data_factory/importers/providers/defra/validator.py`
- `tools/carbon_data_factory/importers/providers/epa/__init__.py`
- `tools/carbon_data_factory/importers/providers/epa/importer.py`
- `tools/carbon_data_factory/importers/providers/epa/normalizer.py`
- `tools/carbon_data_factory/importers/providers/epa/parser.py`
- `tools/carbon_data_factory/importers/providers/epa/schema.py`
- `tools/carbon_data_factory/importers/providers/epa/transformer.py`
- `tools/carbon_data_factory/importers/providers/epa/validator.py`
- `tools/carbon_data_factory/importers/providers/seai/__init__.py`
- `tools/carbon_data_factory/importers/providers/seai/importer.py`
- `tools/carbon_data_factory/importers/providers/seai/normalizer.py`
- `tools/carbon_data_factory/importers/providers/seai/parser.py`
- `tools/carbon_data_factory/importers/providers/seai/schema.py`
- `tools/carbon_data_factory/importers/providers/seai/transformer.py`
- `tools/carbon_data_factory/importers/providers/seai/validator.py`
- `tools/carbon_data_factory/importers/tests/integration/test_defra_import.py`
- `tools/carbon_data_factory/importers/tests/unit/test_defra_parser.py`
- `tools/carbon_data_factory/importers/tests/unit/test_defra_pivoter.py`

### Human Data-Processing Provider Modules

- No modules confidently classified as human data-processing providers.

## 7. V3 Impact Groups

### EXTEND / REVIEW

- `backend/auth.py`
- `backend/config.py`
- `backend/database.py`
- `backend/infra/config.py`
- `backend/infra/supabase.py`
- `backend/report_generator.py`
- `backend/routes/admin/analytics.py`
- `backend/routes/admin/assignments.py`
- `backend/routes/admin/audit_logs.py`
- `backend/routes/admin/beta.py`
- `backend/routes/admin/bulk.py`
- `backend/routes/admin/dashboard.py`
- `backend/routes/admin/document-types.py`
- `backend/routes/admin/logs.py`
- `backend/routes/admin/permissions.py`
- `backend/routes/admin/reviews.py`
- `backend/routes/admin/settings.py`
- `backend/routes/admin/workload.py`
- `backend/routes/communication.py`
- `backend/routes/customer_dashboard.py`
- `backend/routes/customer_documents.py`
- `backend/routes/customer_verifications.py`
- `backend/routes/documents/__init__.py`
- `backend/routes/drafts.py`
- `backend/routes/drafts_enhanced.py`
- `backend/routes/feedback.py`
- `backend/routes/glossary.py`
- `backend/routes/logs.py`
- `backend/routes/notifications.py`
- `backend/routes/organizations/analytics.py`
- `backend/routes/organizations/assets.py`
- `backend/routes/organizations/bulk.py`
- `backend/routes/organizations/dashboard.py`
- `backend/routes/organizations/data.py`
- `backend/routes/organizations/files.py`
- `backend/routes/organizations/management.py`
- `backend/routes/organizations/metadata.py`
- `backend/routes/organizations/team.py`
- `backend/routes/reference.py`
- `backend/routes/reports.py`
- `backend/tests/auth_helper.py`
- `backend/tests/create_test_users.py`
- `backend/tests/integration/test_config.py`
- `backend/tests/integration/test_documents.py`
- `backend/tests/integration/test_infra.py`
- `backend/tests/integration/test_reports.py`
- `backend/tests/setup_test_data.py`
- `backend/tests/setup_test_orgs.py`
- `backend/tests/test_all_endpoints.py`
- `backend/tests/test_api.py`
- `backend/tests/test_api_simple.py`
- `backend/tests/test_auth_simple.py`
- `backend/tests/verify_setup.py`
- `backend/utils/audit_logger.py`
- `backend/utils/document_classifier.py`
- `backend/utils/organization_utils.py`
- `backend/utils/staff_workload.py`
- `demodatagen/generators/core/generate_staff_profiles.py`
- `demodatagen/generators/documents/generate_customer_documents.py`
- `demodatagen/generators/documents/generate_document_types.py`
- `demodatagen/utils/data_validators.py`
- `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/19fc925d-0962-8a3a-8000-0fb8fbe59ca5/scratch/postprocess.py`
- `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/scratch_mm/style.py`

### NO CHANGE

- `backend/data/__init__.py`
- `backend/data/audit.py`
- `backend/data/documents.py`
- `backend/data/emission_factors.py`
- `backend/data/emissions_logs.py`
- `backend/data/events.py`
- `backend/data/factor_aliases.py`
- `backend/data/imports.py`
- `backend/data/organizations.py`
- `backend/data/reports.py`
- `backend/domain/__init__.py`
- `backend/domain/audit.py`
- `backend/domain/benchmarking.py`
- `backend/domain/calculation.py`
- `backend/domain/document.py`
- `backend/domain/factor.py`
- `backend/domain/matching.py`
- `backend/domain/organization.py`
- `backend/domain/provider.py`
- `backend/domain/report.py`
- `backend/domain/validation.py`
- `backend/domain/workflow.py`
- `backend/engines/__init__.py`
- `backend/engines/ai_extraction.py`
- `backend/engines/benchmarking.py`
- `backend/engines/calculation.py`
- `backend/engines/extraction.py`
- `backend/engines/factor_matching.py`
- `backend/engines/matching_stages.py`
- `backend/engines/report_generation.py`
- `backend/engines/validation.py`
- `backend/engines/workflow.py`
- `backend/infra/audit_logger.py`
- `backend/infra/event_bus.py`
- `backend/infra/llm_client.py`
- `backend/infra/search_index.py`
- `backend/main copy 2.py`
- `backend/main copy.py`
- `backend/main.py`
- `backend/process_emissions.py`
- `backend/routes/admin/audit.py`
- `backend/routes/admin/defra.py`
- `backend/routes/admin/email_templates.py`
- `backend/routes/admin/extraction.py`
- `backend/routes/admin/review_history.py`
- `backend/routes/admin/staff.py`
- `backend/routes/document_activity.py`
- `backend/routes/documents_main.py`
- `backend/routes/emissions.py`
- `backend/routes/organizations/exports.py`
- `backend/routes/organizations/members.py`
- `backend/routes/upload.py`
- `backend/routes/users.py`
- `backend/routes/waitlist.py`
- `backend/tests/check_imports.py`
- `backend/tests/export_postman.py`
- `backend/tests/fix_imports.py`
- `backend/tests/integration/conftest.py`
- `backend/tests/integration/test_ai_extraction.py`
- `backend/tests/integration/test_audit.py`
- `backend/tests/integration/test_audit_logger.py`
- `backend/tests/integration/test_calculation.py`
- `backend/tests/integration/test_emission_factors.py`
- `backend/tests/integration/test_emissions_logs.py`
- `backend/tests/integration/test_event_bus.py`
- `backend/tests/integration/test_events.py`
- `backend/tests/integration/test_extraction.py`
- `backend/tests/integration/test_factor_aliases.py`
- `backend/tests/integration/test_factor_matching.py`
- `backend/tests/integration/test_imports.py`
- `backend/tests/integration/test_llm_client.py`
- `backend/tests/integration/test_organizations.py`
- `backend/tests/integration/test_search_index.py`
- `backend/tests/integration/test_workflow.py`
- `backend/tests/test_failing_endpoints.py`
- `backend/tests/unit/domain/__init__.py`
- `backend/tests/unit/domain/test_audit.py`
- `backend/tests/unit/domain/test_benchmarking.py`
- `backend/tests/unit/domain/test_calculation.py`
- `backend/tests/unit/domain/test_document.py`
- `backend/tests/unit/domain/test_factor.py`
- `backend/tests/unit/domain/test_matching.py`
- `backend/tests/unit/domain/test_organization.py`
- `backend/tests/unit/domain/test_provider.py`
- `backend/tests/unit/domain/test_report.py`
- `backend/tests/unit/domain/test_validation.py`
- `backend/tests/unit/domain/test_workflow.py`
- `backend/tests/unit/engines/test_ai_extraction.py`
- `backend/tests/unit/engines/test_benchmarking.py`
- `backend/tests/unit/engines/test_calculation.py`
- `backend/tests/unit/engines/test_extraction.py`
- `backend/tests/unit/engines/test_factor_matching.py`
- `backend/tests/unit/engines/test_matching_stages.py`
- `backend/tests/unit/engines/test_validation.py`
- `backend/tests/unit/engines/test_workflow.py`
- `backend/tests/unit/infra/test_audit_logger.py`
- `backend/tests/unit/infra/test_event_bus.py`
- `backend/tests/unit/infra/test_llm_client.py`
- `backend/tests/unit/infra/test_search_index.py`
- `backend/utils/__init__.py`
- `backend/utils/email.py`
- `backend/utils/emissions.py`
- `demodatagen/generators/base_generator.py`
- `demodatagen/generators/carbon/generate_emissions_logs.py`
- `demodatagen/organizations.py`
- `demodatagen/scripts/export_to_sql.py`
- `demodatagen/scripts/validate_data.py`
- `export_postman.py`
- `generate_messy_fuel_csv.py`
- `generate_messy_utility_csv.py`
- `src/commands/import_defra.py`
- `src/commands/import_seai.py`
- `src/providers/defra/__init__.py`
- `src/providers/defra/exporter.py`
- `src/providers/defra/mapper.py`
- `src/providers/defra/models.py`
- `src/providers/defra/parser.py`
- `src/providers/defra/validator.py`
- `src/providers/seai/__init__.py`
- `src/providers/seai/exporter.py`
- `src/providers/seai/mapper.py`
- `src/providers/seai/models.py`
- `src/providers/seai/parser.py`
- `src/providers/seai/tests/conftest.py`
- `src/providers/seai/tests/test_defra_regression.py`
- `src/providers/seai/tests/test_import.py`
- `src/providers/seai/tests/test_mapper.py`
- `src/providers/seai/tests/test_parser.py`
- `src/providers/seai/tests/test_validator.py`
- `src/providers/seai/validator.py`
- `test_endpoints.py`
- `tools/carbon_data_factory/analyze_project.py`
- `tools/carbon_data_factory/importers/__init__.py`
- `tools/carbon_data_factory/importers/base_importer.py`
- `tools/carbon_data_factory/importers/orchestrator.py`
- `tools/carbon_data_factory/importers/providers/__init__.py`
- `tools/carbon_data_factory/importers/providers/defra/__init__.py`
- `tools/carbon_data_factory/importers/providers/defra/importer.py`
- `tools/carbon_data_factory/importers/providers/defra/normalizer.py`
- `tools/carbon_data_factory/importers/providers/defra/parser.py`
- `tools/carbon_data_factory/importers/providers/defra/pivoter.py`
- `tools/carbon_data_factory/importers/providers/defra/schema.py`
- `tools/carbon_data_factory/importers/providers/defra/transformer.py`
- `tools/carbon_data_factory/importers/providers/defra/validator.py`
- `tools/carbon_data_factory/importers/providers/epa/__init__.py`
- `tools/carbon_data_factory/importers/providers/epa/importer.py`
- `tools/carbon_data_factory/importers/providers/epa/normalizer.py`
- `tools/carbon_data_factory/importers/providers/epa/parser.py`
- `tools/carbon_data_factory/importers/providers/epa/schema.py`
- `tools/carbon_data_factory/importers/providers/epa/transformer.py`
- `tools/carbon_data_factory/importers/providers/epa/validator.py`
- `tools/carbon_data_factory/importers/providers/seai/__init__.py`
- `tools/carbon_data_factory/importers/providers/seai/importer.py`
- `tools/carbon_data_factory/importers/providers/seai/normalizer.py`
- `tools/carbon_data_factory/importers/providers/seai/parser.py`
- `tools/carbon_data_factory/importers/providers/seai/schema.py`
- `tools/carbon_data_factory/importers/providers/seai/transformer.py`
- `tools/carbon_data_factory/importers/providers/seai/validator.py`
- `tools/carbon_data_factory/importers/shared/__init__.py`
- `tools/carbon_data_factory/importers/shared/change_detector.py`
- `tools/carbon_data_factory/importers/shared/db.py`
- `tools/carbon_data_factory/importers/shared/hierarchy.py`
- `tools/carbon_data_factory/importers/shared/storage.py`
- `tools/carbon_data_factory/importers/shared/units.py`
- `tools/carbon_data_factory/importers/shared/validators.py`
- `tools/carbon_data_factory/importers/stages/__init__.py`
- `tools/carbon_data_factory/importers/stages/base_stage.py`
- `tools/carbon_data_factory/importers/stages/importer.py`
- `tools/carbon_data_factory/importers/stages/normalizer.py`
- `tools/carbon_data_factory/importers/stages/parser.py`
- `tools/carbon_data_factory/importers/stages/pivoter.py`
- `tools/carbon_data_factory/importers/stages/transformer.py`
- `tools/carbon_data_factory/importers/stages/validator.py`
- `tools/carbon_data_factory/importers/stages/verifier.py`
- `tools/carbon_data_factory/importers/tests/integration/test_defra_import.py`
- `tools/carbon_data_factory/importers/tests/unit/test_defra_parser.py`
- `tools/carbon_data_factory/importers/tests/unit/test_defra_pivoter.py`

### NO DIRECT V3 IMPACT

- `admin/serve.py`
- `backend/core/__init__.py`
- `backend/core/exceptions.py`
- `backend/core/logging.py`
- `backend/core/types.py`
- `backend/data/base.py`
- `backend/glossary copy.py`
- `backend/glossary.py`
- `backend/infra/__init__.py`
- `backend/middleware/rate_limit.py`
- `backend/pdf_engine.py`
- `backend/routes/__init__.py`
- `backend/routes/admin/__init__.py`
- `backend/routes/organizations/__init__.py`
- `backend/services/email_service.py`
- `backend/tests/__init__.py`
- `backend/tests/audit_code.py`
- `backend/tests/config.py`
- `backend/tests/integration/__init__.py`
- `backend/tests/unit/__init__.py`
- `backend/tests/unit/engines/__init__.py`
- `backend/tests/unit/infra/__init__.py`
- `backend/tests/unit/infra/test_config.py`
- `backend/tests/unit/test_core.py`
- `create_admin_dashboard.py`
- `demodatagen/config.py`
- `demodatagen/generators/__init__.py`
- `demodatagen/generators/carbon/generate_activity_categories.py`
- `demodatagen/generators/collaboration/generate_conversations.py`
- `demodatagen/generators/collaboration/generate_messages.py`
- `demodatagen/generators/core/generate_users.py`
- `demodatagen/generators/facilities/generate_assets.py`
- `demodatagen/generators/facilities/generate_facilities.py`
- `demodatagen/scripts/run_all_generators.py`
- `demodatagen/utils/__init__.py`
- `demodatagen/utils/date_utils.py`
- `demodatagen/utils/id_generators.py`
- `generate_api_docs.py`
- `generate_backend_inventory.py`
- `list_endpoints.py`
- `quick_api_ref.py`
- `src/__init__.py`
- `src/commands/__init__.py`

### REVIEW — PROVIDER SEMANTICS

- `demodatagen/generators/core/generate_organizations.py`
- `src/providers/__init__.py`

## 8. Parse / Inspection Issues

The following files could not be fully parsed:

- `backend/services/email_service.py` — SyntaxError: unexpected indent at line 18
- `demodatagen/utils/__init__.py` — SyntaxError: invalid syntax at line 6

## 9. V3 Interpretation Notes

The following existing CarbonTally capabilities should normally remain part of the technical core:

- CSV / Excel ingestion
- PDF / document ingestion
- AI extraction
- Manual extraction
- Validation
- Factor Matching Engine
- Emission-factor provider architecture
- Calculation Engine
- Calculation snapshots / lineage
- Workflow orchestration
- QC / approval
- Exports
- API

V3 primarily introduces an operational layer for human data-processing providers.

Potential V3 concepts requiring targeted inspection:

- processing provider entity
- processing provider contracts
- provider staff membership
- provider-specific RBAC
- provider lifecycle
- provider SLA
- provider KPI
- provider performance
- provider actions / remediation
- provider suspension / termination
- provider-aware work assignment
- cross-provider reassignment
- provider-scoped Storage access
- provider-scoped RLS
- customer-to-provider communication isolation

This inventory does NOT authorize implementation of any of these changes. A separate V3 impact audit must determine the minimum required modification.

## 10. Recommended Next Step

Use this inventory together with the current database schema and existing CarbonTally V2.1 implementation documentation to produce a read-only V3 impact matrix.

Do not generate migrations until the actual backend modules, database relationships, RLS policies, Storage policies and existing processing workflow have been compared against V3.

---

Generated automatically — READ-ONLY analysis.
