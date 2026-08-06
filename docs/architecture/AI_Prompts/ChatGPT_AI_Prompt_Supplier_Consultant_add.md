# CarbonTally is a single multi-tenant SaaS application with role-based workspaces. Every user logs into the same application. The workspace, menus, permissions, and accessible data are determined entirely by role and organization assignments.

# CARBONTALLY PLATFORM ARCHITECTURE

CarbonTally is NOT a collection of separate applications.

It is ONE multi-tenant SaaS platform.

Every authenticated user logs into the same application.

The interface changes based on role.

Platform
│
├── Platform Workspace
│   ├── Super Admin
│   ├── Carbon Analyst
│   ├── Senior Validator
│   ├── Support
│   ├── Sales
│   └── Compliance
│
├── Consultant Workspace
│   ├── Client Portfolio
│   ├── Organization Switcher
│   ├── Supplier Management
│   ├── Upload Management
│   ├── Reports
│   └── Analytics
│
└── Organization Workspace
    ├── Dashboard
    ├── Documents
    ├── Uploads
    ├── Suppliers
    ├── Reports
    ├── Team
    ├── Compliance
    └── Settings

Suppliers are owned by organizations.

Suppliers do NOT login in v1.0.

Consultants manage multiple organizations.

Platform staff manage the entire platform.

The architecture must support future additions without redesigning the database.

Do not create separate applications.

Everything must use role-based workspaces.
# PHASE 1

You are the Chief Database Architect for CarbonTally.

This is Phase 1 of a multi-phase architecture project.

DO NOT generate SQL.

DO NOT modify tables.

DO NOT redesign from scratch.

Your task is ONLY to audit the existing Supabase database.

You will receive the complete database schema.

Your objectives are:

1. Review every table.

2. Explain the purpose of every table.

3. Identify duplicated data.

4. Identify denormalized structures.

5. Identify missing foreign keys.

6. Identify missing indexes.

7. Review naming consistency.

8. Review scalability.

9. Review tenant isolation.

10. Review security implications.

11. Review reporting capabilities.

12. Review document relationships.

13. Review uploads.

14. Review OCR workflow.

15. Review AI extraction workflow.

16. Review audit logging.

17. Identify missing entities.

18. Identify missing relationships.

19. Evaluate whether the schema supports:

- Consultants
- Multiple organizations
- Supplier management
- Future supplier portal
- Corporate groups
- White label
- API integrations

20. Produce an improved ERD.

DO NOT generate SQL.

Return only architecture recommendations.

At the end produce:

Architecture Score (/100)

Scalability Score

Maintainability Score

Future Readiness Score

List every recommended change with reasons.

These recommendations will be used in Phase 2.

Below is the updated database schema of supabase database:


below is my database schema:
## Table `organizations`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `name` | `varchar` |  |
| `company_number` | `varchar` |  Nullable Unique |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `logo_url` | `text` |  Nullable |
| `industry` | `text` |  Nullable |
| `sector` | `text` |  Nullable |
| `company_size` | `text` |  Nullable |
| `vat_number` | `text` |  Nullable |
| `registration_number` | `text` |  Nullable |
| `registered_address` | `text` |  Nullable |
| `country` | `text` |  Nullable |
| `timezone` | `text` |  Nullable |
| `currency` | `text` |  Nullable |
| `financial_year_end` | `date` |  Nullable |
| `reporting_standard` | `text` |  Nullable |
| `secr_enabled` | `bool` |  Nullable |
| `esrs_enabled` | `bool` |  Nullable |
| `issb_enabled` | `bool` |  Nullable |
| `default_defra_version` | `int4` |  Nullable |
| `preferred_units` | `text` |  Nullable |
| `website` | `text` |  Nullable |
| `primary_contact_email` | `text` |  Nullable |
| `primary_contact_name` | `text` |  Nullable |
| `billing_contact_email` | `text` |  Nullable |
| `billing_contact_name` | `text` |  Nullable |
| `subscription_status` | `text` |  Nullable |
| `trial_start_date` | `timestamptz` |  Nullable |
| `trial_end_date` | `timestamptz` |  Nullable |
| `subscription_tier` | `text` |  Nullable |
| `subscription_id` | `text` |  Nullable |
| `billing_address` | `text` |  Nullable |
| `tax_rate` | `numeric` |  Nullable |
| `metadata` | `jsonb` |  Nullable |

## Table `organization_members`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `user_id` | `uuid` |  |
| `role` | `varchar` |  |
| `created_at` | `timestamptz` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `facilities`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `name` | `varchar` |  |
| `postcode` | `varchar` |  |
| `created_at` | `timestamptz` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `latitude` | `numeric` |  Nullable |
| `longitude` | `numeric` |  Nullable |
| `type` | `varchar` |  Nullable |
| `address_line1` | `varchar` |  Nullable |
| `address_line2` | `varchar` |  Nullable |
| `city` | `varchar` |  Nullable |
| `county` | `varchar` |  Nullable |
| `country` | `varchar` |  Nullable |
| `region` | `varchar` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `assets`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `facility_id` | `uuid` |  |
| `name` | `varchar` |  |
| `description` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `capacity` | `numeric` |  Nullable |
| `capacity_unit` | `varchar` |  Nullable |
| `serial_number` | `varchar` |  Nullable |
| `installation_date` | `date` |  Nullable |
| `type` | `varchar` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `defra_conversion_factors`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `reporting_year` | `int4` |  |
| `activity_type` | `varchar` |  |
| `co2e_multiplier` | `numeric` |  |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `emissions_logs`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `asset_id` | `uuid` |  Nullable |
| `defra_factor_id` | `uuid` |  Nullable |
| `start_date` | `date` |  |
| `end_date` | `date` |  |
| `raw_quantity` | `numeric` |  |
| `calculated_kg_co2e` | `numeric` |  |
| `created_by_user_id` | `uuid` |  |
| `created_at` | `timestamptz` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `file_id` | `uuid` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `customer_document_id` | `uuid` |  Nullable |

## Table `pending_invites`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `email` | `varchar` |  |
| `role` | `varchar` |  |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `manual_review_queue`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  Nullable |
| `file_url` | `text` |  |
| `file_name` | `text` |  |
| `file_type` | `text` |  |
| `data_type` | `text` |  |
| `status` | `text` |  |
| `auto_extraction_result` | `jsonb` |  Nullable |
| `manual_extraction_result` | `jsonb` |  Nullable |
| `assigned_to` | `uuid` |  Nullable |
| `priority` | `int4` |  Nullable |
| `customer_notes` | `text` |  Nullable |
| `staff_notes` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `completed_at` | `timestamptz` |  Nullable |
| `estimated_completion_hours` | `int4` |  Nullable |
| `batch_id` | `uuid` |  Nullable |
| `assigned_by` | `uuid` |  Nullable |
| `started_at` | `timestamptz` |  Nullable |
| `completed_by` | `uuid` |  Nullable |
| `data_entry` | `jsonb` |  Nullable |
| `review_time_seconds` | `int4` |  Nullable |
| `priority_score` | `int4` |  Nullable |
| `sla_deadline` | `timestamptz` |  Nullable |
| `sla_breached` | `bool` |  Nullable |
| `escalation_level` | `int4` |  Nullable |
| `customer_notified_at` | `timestamptz` |  Nullable |
| `customer_responded_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `customer_document_id` | `uuid` |  Nullable |

## Table `staff_profiles`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `role` | `text` |  |
| `extraction_count` | `int4` |  Nullable |
| `accuracy_rate` | `numeric` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `user_id` | `uuid` |  Nullable |
| `first_name` | `text` |  Nullable |
| `last_name` | `text` |  Nullable |
| `email` | `text` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `last_login` | `timestamptz` |  Nullable |
| `total_reviews_completed` | `int4` |  Nullable |
| `avg_review_time_minutes` | `int4` |  Nullable |
| `role_id` | `uuid` |  Nullable |
| `permissions` | `jsonb` |  Nullable |
| `reviews_assigned` | `int4` |  Nullable |
| `reviews_completed` | `int4` |  Nullable |
| `avg_review_time_seconds` | `int4` |  Nullable |
| `total_review_time_seconds` | `int4` |  Nullable |
| `current_load` | `int4` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `upload_batches`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  Nullable |
| `batch_name` | `varchar` |  Nullable |
| `total_files` | `int4` |  Nullable |
| `processed_files` | `int4` |  Nullable |
| `status` | `text` |  Nullable |
| `created_by_user_id` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `completed_at` | `timestamptz` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `beta_access_codes`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `code` | `text` |  Unique |
| `email` | `text` |  Nullable |
| `status` | `text` |  Nullable |
| `expires_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `used_at` | `timestamptz` |  Nullable |
| `magic_token` | `text` |  Nullable |
| `token_created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `beta_users`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  Nullable |
| `email` | `text` |  Unique |
| `beta_code` | `text` |  Nullable |
| `access_level` | `text` |  Nullable |
| `invited_by` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `last_active_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `review_audit_trail`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `review_id` | `uuid` |  Nullable |
| `action` | `text` |  |
| `performed_by` | `uuid` |  Nullable |
| `performed_by_email` | `text` |  Nullable |
| `assigned_to` | `uuid` |  Nullable |
| `old_value` | `jsonb` |  Nullable |
| `new_value` | `jsonb` |  Nullable |
| `note` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `waitlist`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `email` | `text` |  Unique |
| `full_name` | `text` |  Nullable |
| `company_name` | `text` |  Nullable |
| `company_size` | `text` |  Nullable |
| `interested_in` | `text` |  Nullable |
| `source` | `text` |  Nullable |
| `status` | `text` |  Nullable |
| `invited_at` | `timestamptz` |  Nullable |
| `activated_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `email_logs`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `email` | `text` |  |
| `type` | `text` |  |
| `status` | `text` |  |
| `error_message` | `text` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `glossary`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `term` | `text` |  Unique |
| `definition` | `text` |  |
| `category` | `text` |  Nullable |
| `related_terms` | `_text` |  Nullable |
| `example` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `is_active` | `bool` |  Nullable |

## Table `activity_categories`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `activity_type` | `text` |  Unique |
| `esrs_e1_category` | `text` |  |
| `issb_category` | `text` |  |
| `ghg_protocol_scope` | `text` |  |
| `ghg_protocol_category` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `system_settings`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `settings_json` | `jsonb` |  Nullable |
| `max_file_size_mb` | `int4` |  Nullable |
| `allowed_file_types` | `_text` |  Nullable |
| `enable_auto_repair` | `bool` |  Nullable |
| `max_batch_files` | `int4` |  Nullable |
| `max_total_batch_size_mb` | `int4` |  Nullable |
| `data_retention_days` | `int4` |  Nullable |
| `require_2fa` | `bool` |  Nullable |
| `session_timeout_minutes` | `int4` |  Nullable |
| `max_login_attempts` | `int4` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `roles`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `name` | `varchar` |  Unique |
| `description` | `text` |  Nullable |
| `permissions` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `user_activity_log`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  Nullable |
| `action` | `varchar` |  |
| `details` | `jsonb` |  Nullable |
| `ip_address` | `varchar` |  Nullable |
| `user_agent` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `user_invitations`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `email` | `varchar` |  |
| `role_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  Nullable |
| `invited_by` | `uuid` |  Nullable |
| `token` | `varchar` |  Unique |
| `status` | `varchar` |  Nullable |
| `expires_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `user_feedback`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  Nullable |
| `user_id` | `uuid` |  Nullable |
| `user_email` | `text` |  |
| `type` | `text` |  |
| `title` | `text` |  |
| `description` | `text` |  |
| `severity` | `text` |  Nullable |
| `status` | `text` |  Nullable |
| `rating` | `int4` |  Nullable |
| `screenshot_url` | `text` |  Nullable |
| `browser_info` | `text` |  Nullable |
| `os_info` | `text` |  Nullable |
| `url` | `text` |  Nullable |
| `assigned_to` | `uuid` |  Nullable |
| `resolved_at` | `timestamptz` |  Nullable |
| `resolution_notes` | `text` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |

## Table `password_reset_tokens`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  Nullable Unique |
| `token` | `varchar` |  Unique |
| `expires_at` | `timestamptz` |  |
| `used` | `bool` |  Nullable |
| `used_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `organization_files`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `name` | `varchar` |  |
| `path` | `text` |  |
| `size_bytes` | `int8` |  |
| `file_type` | `varchar` |  |
| `mime_type` | `varchar` |  |
| `bucket` | `varchar` |  Nullable |
| `uploaded_by` | `uuid` |  Nullable |
| `uploaded_at` | `timestamptz` |  Nullable |
| `last_accessed` | `timestamptz` |  Nullable |
| `access_count` | `int4` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `deleted_at` | `timestamptz` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `status` | `varchar` |  Nullable |
| `status_updated_at` | `timestamptz` |  Nullable |
| `processing_started_at` | `timestamptz` |  Nullable |
| `review_ready_at` | `timestamptz` |  Nullable |
| `approved_at` | `timestamptz` |  Nullable |
| `rejected_at` | `timestamptz` |  Nullable |
| `rejection_reason` | `text` |  Nullable |
| `reviewed_by` | `uuid` |  Nullable |
| `approved_by` | `uuid` |  Nullable |

## Table `organization_metadata`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  Unique |
| `total_employees` | `int4` |  Nullable |
| `full_time_employees` | `int4` |  Nullable |
| `part_time_employees` | `int4` |  Nullable |
| `contract_employees` | `int4` |  Nullable |
| `average_employees` | `int4` |  Nullable |
| `annual_revenue` | `numeric` |  Nullable |
| `ebitda` | `numeric` |  Nullable |
| `total_assets` | `numeric` |  Nullable |
| `total_facilities` | `int4` |  Nullable |
| `total_floor_area_sqft` | `numeric` |  Nullable |
| `occupied_floor_area_sqft` | `numeric` |  Nullable |
| `renewable_energy_percentage` | `numeric` |  Nullable |
| `carbon_offset_percentage` | `numeric` |  Nullable |
| `energy_intensity` | `numeric` |  Nullable |
| `reporting_standard` | `varchar` |  Nullable |
| `fiscal_year_start` | `date` |  Nullable |
| `fiscal_year_end` | `date` |  Nullable |
| `primary_contact_name` | `varchar` |  Nullable |
| `primary_contact_email` | `varchar` |  Nullable |
| `primary_contact_phone` | `varchar` |  Nullable |
| `sustainability_officer_name` | `varchar` |  Nullable |
| `sustainability_officer_email` | `varchar` |  Nullable |
| `industry_sector` | `varchar` |  Nullable |
| `naics_code` | `varchar` |  Nullable |
| `sic_code` | `varchar` |  Nullable |
| `custom_metrics` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `updated_by` | `uuid` |  Nullable |

## Table `document_activity_log`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `file_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  Nullable |
| `user_id` | `uuid` |  Nullable |
| `action` | `varchar` |  |
| `details` | `jsonb` |  Nullable |
| `ip_address` | `varchar` |  Nullable |
| `user_agent` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `customer_review_log`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `file_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  Nullable |
| `user_id` | `uuid` |  Nullable |
| `status` | `varchar` |  |
| `notes` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `draft_entries`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `file_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  Nullable |
| `user_id` | `uuid` |  Nullable |
| `data` | `jsonb` |  Nullable |
| `progress` | `int4` |  Nullable |
| `sections_completed` | `jsonb` |  Nullable |
| `last_updated` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `review_assignment_history`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `review_id` | `uuid` |  Nullable |
| `assigned_by` | `uuid` |  Nullable |
| `assigned_to` | `uuid` |  Nullable |
| `previous_assigned_to` | `uuid` |  Nullable |
| `action` | `varchar` |  |
| `note` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `export_history`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  Nullable |
| `user_id` | `uuid` |  Nullable |
| `file_name` | `varchar` |  Nullable |
| `format` | `varchar` |  Nullable |
| `filters` | `jsonb` |  Nullable |
| `record_count` | `int4` |  Nullable |
| `status` | `varchar` |  Nullable |
| `file_url` | `text` |  Nullable |
| `expires_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `units`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `code` | `varchar` |  Unique |
| `name` | `varchar` |  |
| `category` | `varchar` |  |
| `symbol` | `varchar` |  Nullable |
| `conversion_factor` | `numeric` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `staff_workload`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `staff_id` | `uuid` |  Nullable |
| `assigned_reviews` | `int4` |  Nullable |
| `in_progress_reviews` | `int4` |  Nullable |
| `pending_reviews` | `int4` |  Nullable |
| `completed_today` | `int4` |  Nullable |
| `workload_score` | `float8` |  Nullable |
| `last_updated` | `timestamptz` |  Nullable |
| `date` | `date` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `queue_settings`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `max_reviews_per_staff` | `int4` |  Nullable |
| `sla_hours` | `int4` |  Nullable |
| `auto_assign_enabled` | `bool` |  Nullable |
| `escalation_hours` | `int4` |  Nullable |
| `priority_weights` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `updated_by` | `uuid` |  Nullable |

## Table `activity_logs`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  Nullable |
| `action` | `varchar` |  |
| `resource_type` | `varchar` |  |
| `resource_id` | `uuid` |  Nullable |
| `details` | `jsonb` |  Nullable |
| `ip_address` | `varchar` |  Nullable |
| `user_agent` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `processing_logs`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `file_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  Nullable |
| `step` | `varchar` |  |
| `status` | `varchar` |  |
| `started_at` | `timestamptz` |  Nullable |
| `completed_at` | `timestamptz` |  Nullable |
| `duration_ms` | `int4` |  Nullable |
| `details` | `jsonb` |  Nullable |
| `error` | `text` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `email_templates`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `name` | `varchar` |  |
| `subject` | `varchar` |  |
| `body` | `text` |  |
| `type` | `varchar` |  |
| `variables` | `_text` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `description` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_by` | `uuid` |  Nullable |

## Table `customer_documents`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `organization_member_id` | `uuid` |  |
| `asset_id` | `uuid` |  |
| `file_name` | `text` |  |
| `file_url` | `text` |  |
| `file_type` | `text` |  |
| `upload_date` | `timestamptz` |  Nullable |
| `status` | `text` |  Nullable |
| `manual_review_queue_id` | `uuid` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `document_type_id` | `uuid` |  Nullable |
| `document_type_code` | `text` |  Nullable |
| `organization_classification` | `text` |  Nullable |
| `classification_by` | `uuid` |  Nullable |
| `classification_at` | `timestamptz` |  Nullable |
| `confidence_score` | `float8` |  Nullable |
| `organization_notes` | `text` |  Nullable |
| `billing_period_start` | `date` |  Nullable |
| `billing_period_end` | `date` |  Nullable |

## Table `audit_logs`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  Nullable |
| `staff_id` | `uuid` |  Nullable |
| `organization_member_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  Nullable |
| `action_type` | `text` |  |
| `resource_type` | `text` |  Nullable |
| `resource_id` | `uuid` |  Nullable |
| `action` | `text` |  |
| `description` | `text` |  Nullable |
| `ip_address` | `text` |  Nullable |
| `user_agent` | `text` |  Nullable |
| `old_data` | `jsonb` |  Nullable |
| `new_data` | `jsonb` |  Nullable |
| `changes` | `jsonb` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `conversations`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  Nullable |
| `staff_id` | `uuid` |  Nullable |
| `customer_id` | `uuid` |  Nullable |
| `subject` | `text` |  Nullable |
| `status` | `text` |  Nullable |
| `last_message_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `closed_by` | `uuid` |  Nullable |
| `closed_at` | `timestamptz` |  Nullable |
| `is_urgent` | `bool` |  Nullable |
| `priority` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `read_by` | `_uuid` |  Nullable |
| `unread_count` | `int4` |  Nullable |
| `participant_count` | `int4` |  Nullable |

## Table `conversation_activity_log`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `conversation_id` | `uuid` |  Nullable |
| `user_id` | `uuid` |  Nullable |
| `action_type` | `text` |  Nullable |
| `action_details` | `jsonb` |  Nullable |
| `ip_address` | `text` |  Nullable |
| `user_agent` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `messages`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `conversation_id` | `uuid` |  Nullable |
| `sender_id` | `uuid` |  Nullable |
| `receiver_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  Nullable |
| `subject` | `text` |  Nullable |
| `content` | `text` |  |
| `is_read` | `bool` |  Nullable |
| `parent_message_id` | `uuid` |  Nullable |
| `sent_at` | `timestamptz` |  Nullable |
| `delivered_at` | `timestamptz` |  Nullable |
| `read_at` | `timestamptz` |  Nullable |
| `is_deleted` | `bool` |  Nullable |
| `deleted_at` | `timestamptz` |  Nullable |
| `is_archived` | `bool` |  Nullable |
| `archived_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `read_by` | `_uuid` |  Nullable |
| `read_count` | `int4` |  Nullable |
| `last_read_at` | `timestamptz` |  Nullable |
| `attachments` | `jsonb` |  Nullable |
| `has_attachments` | `bool` |  Nullable |

## Table `message_activity_log`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `message_id` | `uuid` |  Nullable |
| `conversation_id` | `uuid` |  Nullable |
| `user_id` | `uuid` |  Nullable |
| `action_type` | `text` |  Nullable |
| `action_details` | `jsonb` |  Nullable |
| `ip_address` | `text` |  Nullable |
| `user_agent` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `notifications`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  Nullable |
| `type` | `text` |  |
| `title` | `text` |  |
| `message` | `text` |  |
| `link` | `text` |  Nullable |
| `is_read` | `bool` |  Nullable |
| `read_at` | `timestamptz` |  Nullable |
| `priority` | `text` |  Nullable |
| `sent_via` | `_text` |  Nullable |
| `email_sent` | `bool` |  Nullable |
| `email_sent_at` | `timestamptz` |  Nullable |
| `push_sent` | `bool` |  Nullable |
| `push_sent_at` | `timestamptz` |  Nullable |
| `is_dismissed` | `bool` |  Nullable |
| `dismissed_at` | `timestamptz` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `notification_delivery_log`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `notification_id` | `uuid` |  Nullable |
| `user_id` | `uuid` |  Nullable |
| `channel` | `text` |  Nullable |
| `status` | `text` |  Nullable |
| `error_message` | `text` |  Nullable |
| `sent_at` | `timestamptz` |  Nullable |
| `delivered_at` | `timestamptz` |  Nullable |
| `opened_at` | `timestamptz` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `customer_verifications`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `customer_document_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  Nullable |
| `customer_member_id` | `uuid` |  Nullable |
| `status` | `text` |  Nullable |
| `notes` | `text` |  Nullable |
| `submitted_at` | `timestamptz` |  Nullable |
| `submitted_by` | `uuid` |  Nullable |
| `verified_at` | `timestamptz` |  Nullable |
| `verified_by` | `uuid` |  Nullable |
| `rejected_at` | `timestamptz` |  Nullable |
| `rejected_by` | `uuid` |  Nullable |
| `rejected_reason` | `text` |  Nullable |
| `revision_requested_at` | `timestamptz` |  Nullable |
| `revision_requested_by` | `uuid` |  Nullable |
| `revision_notes` | `text` |  Nullable |
| `is_escalated` | `bool` |  Nullable |
| `escalation_reason` | `text` |  Nullable |
| `escalated_at` | `timestamptz` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `verification_activity_log`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `verification_id` | `uuid` |  Nullable |
| `user_id` | `uuid` |  Nullable |
| `action_type` | `text` |  Nullable |
| `action_details` | `jsonb` |  Nullable |
| `ip_address` | `text` |  Nullable |
| `user_agent` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `document_types`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `code` | `text` |  Unique |
| `name` | `text` |  |
| `category` | `text` |  |
| `description` | `text` |  Nullable |
| `file_extensions` | `_text` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `requires_asset` | `bool` |  Nullable |
| `requires_date_range` | `bool` |  Nullable |
| `requires_facility` | `bool` |  Nullable |
| `priority` | `int4` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `typing_status`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  Nullable |
| `conversation_id` | `uuid` |  Nullable |
| `is_typing` | `bool` |  Nullable |
| `started_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `user_presence`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  Nullable |
| `status` | `text` |  Nullable |
| `last_seen_at` | `timestamptz` |  Nullable |
| `current_channel` | `text` |  Nullable |
| `metadata` | `jsonb` |  Nullable |

## Table `activity_feed`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  Nullable |
| `user_id` | `uuid` |  Nullable |
| `event_type` | `text` |  Nullable |
| `event_data` | `jsonb` |  Nullable |
| `is_read` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `conversation_participants`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `conversation_id` | `uuid` |  |
| `user_id` | `uuid` |  |
| `joined_at` | `timestamptz` |  Nullable |
| `last_read_at` | `timestamptz` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `file_attachments`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `message_id` | `uuid` |  Nullable |
| `conversation_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  Nullable |
| `file_name` | `text` |  |
| `file_url` | `text` |  |
| `file_size` | `int4` |  Nullable |
| `file_type` | `text` |  Nullable |
| `mime_type` | `text` |  Nullable |
| `uploaded_by` | `uuid` |  Nullable |
| `uploaded_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Custom Types / Enums

### `document_status`

`uploaded` | `processing` | `staff_review` | `ready_for_review` | `approved` | `rejected`

## RLS Policies

### `emissions_logs`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Users can view their own organization's emissions` | ALL | public | PERMISSIVE | `(organization_id IN ( SELECT organization_members.organization_id    FROM organization_members   WHERE (organization_members.user_id = auth.uid())))` | — |

### `pending_invites`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Admins can delete invites for their org` | DELETE | public | PERMISSIVE | `(organization_id IN ( SELECT organization_members.organization_id    FROM organization_members   WHERE ((organization_members.user_id = auth.uid()) AND ((organization_members.role)::text = 'admin'::text))))` | — |
| `Admins can insert invites for their org` | INSERT | public | PERMISSIVE | — | `(organization_id IN ( SELECT organization_members.organization_id    FROM organization_members   WHERE ((organization_members.user_id = auth.uid()) AND ((organization_members.role)::text = 'admin'::text))))` |
| `Admins can view invites for their org` | SELECT | public | PERMISSIVE | `(organization_id IN ( SELECT organization_members.organization_id    FROM organization_members   WHERE ((organization_members.user_id = auth.uid()) AND ((organization_members.role)::text = 'admin'::text))))` | — |

### `beta_users`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Enable all for authenticated users with admin role` | ALL | public | PERMISSIVE | `(auth.role() = 'authenticated'::text)` | — |

### `staff_profiles`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Staff can view their own profile` | SELECT | public | PERMISSIVE | `(id = auth.uid())` | — |

### `beta_access_codes`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Enable all for authenticated users with admin role` | ALL | public | PERMISSIVE | `(auth.role() = 'authenticated'::text)` | — |

### `upload_batches`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow batch inserts` | INSERT | public | PERMISSIVE | — | `true` |
| `Allow batch updates` | UPDATE | public | PERMISSIVE | `true` | `true` |
| `Organizations can view their own batches` | SELECT | public | PERMISSIVE | `(organization_id IN ( SELECT organization_members.organization_id    FROM organization_members   WHERE (organization_members.user_id = auth.uid())))` | — |

### `glossary`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Anyone can read glossary` | SELECT | public | PERMISSIVE | `true` | — |
| `Only admins can modify glossary` | ALL | public | PERMISSIVE | `(auth.role() = 'authenticated'::text)` | — |

### `user_invitations`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow admin to manage invitations` | ALL | authenticated | PERMISSIVE | `(auth.uid() IN ( SELECT staff_profiles.user_id    FROM staff_profiles   WHERE (staff_profiles.role_id IN ( SELECT roles.id            FROM roles           WHERE ((roles.name)::text = 'admin'::text)))))` | — |

### `system_settings`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow insert access to admin users only` | INSERT | authenticated | PERMISSIVE | — | `(auth.uid() IN ( SELECT staff_profiles.user_id    FROM staff_profiles   WHERE (staff_profiles.role = 'admin'::text)))` |
| `Allow read access to authenticated users` | SELECT | authenticated | PERMISSIVE | `true` | — |
| `Allow update access to admin users only` | UPDATE | authenticated | PERMISSIVE | `(auth.uid() IN ( SELECT staff_profiles.user_id    FROM staff_profiles   WHERE (staff_profiles.role = 'admin'::text)))` | — |

### `roles`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow admin full access to roles` | ALL | authenticated | PERMISSIVE | `(auth.uid() IN ( SELECT staff_profiles.user_id    FROM staff_profiles   WHERE (staff_profiles.role_id IN ( SELECT roles_1.id            FROM roles roles_1           WHERE ((roles_1.name)::text = 'admin'::text)))))` | — |
| `Allow read roles for authenticated users` | SELECT | authenticated | PERMISSIVE | `true` | — |

### `organizations`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Users can view their own organization` | SELECT | public | PERMISSIVE | `(id IN ( SELECT organization_members.organization_id    FROM organization_members   WHERE (organization_members.user_id = auth.uid())))` | — |

### `assets`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Enable read access for authenticated users` | SELECT | public | PERMISSIVE | `(auth.role() = 'authenticated'::text)` | — |
| `Org members can manage assets` | ALL | public | PERMISSIVE | `(facility_id IN ( SELECT facilities.id    FROM facilities   WHERE (facilities.organization_id IN ( SELECT organization_members.organization_id            FROM organization_members           WHERE (organization_members.user_id = auth.uid())))))` | — |
| `Users can view their own organization's assets` | ALL | public | PERMISSIVE | `(facility_id IN ( SELECT facilities.id    FROM facilities   WHERE (facilities.organization_id IN ( SELECT organization_members.organization_id            FROM organization_members           WHERE (organization_members.user_id = auth.uid())))))` | — |

### `defra_conversion_factors`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Everyone can read DEFRA factors` | SELECT | public | PERMISSIVE | `true` | — |

### `organization_members`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Users can view their own membership` | SELECT | public | PERMISSIVE | `(user_id = auth.uid())` | — |

### `manual_review_queue`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Allow authenticated users to update queue items` | UPDATE | public | PERMISSIVE | `(auth.role() = 'authenticated'::text)` | `(auth.role() = 'authenticated'::text)` |
| `Allow authenticated users to view pending queue items` | SELECT | public | PERMISSIVE | `(auth.role() = 'authenticated'::text)` | — |
| `Staff can insert queue items` | INSERT | public | PERMISSIVE | — | `true` |
| `Staff can update queue items` | UPDATE | public | PERMISSIVE | `true` | `true` |

### `facilities`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Enable read access for authenticated users` | SELECT | public | PERMISSIVE | `(auth.role() = 'authenticated'::text)` | — |
| `Org members can manage facilities` | ALL | public | PERMISSIVE | `(organization_id IN ( SELECT organization_members.organization_id    FROM organization_members   WHERE (organization_members.user_id = auth.uid())))` | — |
| `Users can view their own organization's facilities` | ALL | public | PERMISSIVE | `(organization_id IN ( SELECT organization_members.organization_id    FROM organization_members   WHERE (organization_members.user_id = auth.uid())))` | — |

### `messages`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Can see messages in conversation` | SELECT | public | PERMISSIVE | `(EXISTS ( SELECT 1    FROM conversation_participants   WHERE ((conversation_participants.conversation_id = messages.conversation_id) AND (conversation_participants.user_id = auth.uid()))))` | — |

### `notifications`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Users can see own notifications` | SELECT | public | PERMISSIVE | `(user_id = auth.uid())` | — |

### `customer_documents`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Org members see documents` | SELECT | public | PERMISSIVE | `(EXISTS ( SELECT 1    FROM organization_members   WHERE ((organization_members.organization_id = customer_documents.organization_id) AND (organization_members.user_id = auth.uid()))))` | — |

### `conversation_participants`

| Policy | Command | Roles | Action | USING | WITH CHECK |
|--------|---------|-------|--------|-------|------------|
| `Users can delete conversation participants` | DELETE | public | PERMISSIVE | `(auth.uid() = user_id)` | — |
| `Users can insert conversation participants` | INSERT | public | PERMISSIVE | — | `((auth.uid() = user_id) OR (EXISTS ( SELECT 1    FROM conversation_participants cp2   WHERE ((cp2.conversation_id = conversation_participants.conversation_id) AND (cp2.user_id = auth.uid())))))` |
| `Users can join conversations` | INSERT | public | PERMISSIVE | — | `(user_id = auth.uid())` |
| `Users can leave conversations` | DELETE | public | PERMISSIVE | `(user_id = auth.uid())` | — |
| `Users can see conversation participants` | SELECT | public | PERMISSIVE | `(EXISTS ( SELECT 1    FROM conversation_participants cp2   WHERE ((cp2.conversation_id = conversation_participants.conversation_id) AND (cp2.user_id = auth.uid()))))` | — |
| `Users can update conversation participants` | UPDATE | public | PERMISSIVE | `(auth.uid() = user_id)` | — |
| `Users can update own participation` | UPDATE | public | PERMISSIVE | `(user_id = auth.uid())` | — |
| `Users can view conversation participants` | SELECT | public | PERMISSIVE | `((auth.uid() = user_id) OR (EXISTS ( SELECT 1    FROM conversation_participants cp2   WHERE ((cp2.conversation_id = conversation_participants.conversation_id) AND (cp2.user_id = auth.uid())))))` | — |

