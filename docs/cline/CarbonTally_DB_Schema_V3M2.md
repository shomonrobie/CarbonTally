## Table `activity_categories`

Activity classification reference data

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `activity_type` | `text` |  Unique |
| `esrs_e1_category` | `text` |  Nullable |
| `issb_category` | `text` |  Nullable |
| `ghg_protocol_scope` | `text` |  Nullable |
| `ghg_protocol_category` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `document_type_categories`

Document type classification reference

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `code` | `varchar` |  Unique |
| `name` | `varchar` |  |
| `description` | `text` |  Nullable |
| `category_group` | `varchar` |  Nullable |
| `default_priority` | `int4` |  Nullable |
| `requires_facility` | `bool` |  Nullable |
| `requires_asset` | `bool` |  Nullable |
| `requires_supplier` | `bool` |  Nullable |
| `requires_date_range` | `bool` |  Nullable |
| `default_defra_activity_type` | `varchar` |  Nullable |
| `default_scope` | `varchar` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `is_system` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `document_types`

Document type reference

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

## Table `roles`

Role definitions for RBAC

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `name` | `varchar` |  Unique |
| `description` | `text` |  Nullable |
| `permissions` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `supplier_categories`

Supplier category reference

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `name` | `varchar` |  |
| `description` | `text` |  Nullable |
| `category_group` | `varchar` |  Nullable |
| `default_emission_factor` | `numeric` |  Nullable |
| `default_emission_factor_unit` | `varchar` |  Nullable |
| `ghg_protocol_category` | `varchar` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `product_categories`

Product categories per organization

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `name` | `varchar` |  |
| `description` | `text` |  Nullable |
| `category_type` | `varchar` |  Nullable |
| `ghg_protocol_scope` | `varchar` |  Nullable |
| `ghg_protocol_category` | `varchar` |  Nullable |
| `esrs_e1_category` | `varchar` |  Nullable |
| `issb_category` | `varchar` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `metadata` | `jsonb` |  Nullable |

## Table `units`

Unit of measurement reference

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

## Table `email_templates`

Email template reference

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

## Table `notification_templates`

Notification template reference

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `template_type` | `varchar` |  Unique |
| `name` | `varchar` |  |
| `subject` | `varchar` |  |
| `body` | `text` |  |
| `variables` | `jsonb` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_by` | `uuid` |  Nullable |

## Table `glossary`

Glossary of terms

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

## Table `organizations`

Organization/tenant root

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
| `default_factor_year` | `int4` |  Nullable |
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
| `address_line1` | `varchar` |  Nullable |
| `address_line2` | `varchar` |  Nullable |
| `city` | `varchar` |  Nullable |
| `county` | `varchar` |  Nullable |
| `postcode` | `varchar` |  Nullable |
| `eircode` | `varchar` |  Nullable |
| `language` | `varchar` |  Nullable |
| `locale` | `varchar` |  Nullable |
| `vat_region` | `varchar` |  Nullable |
| `vat_registered` | `bool` |  Nullable |
| `tax_region` | `varchar` |  Nullable |
| `registration_region` | `varchar` |  Nullable |
| `sic_code` | `varchar` |  Nullable |
| `naics_code` | `varchar` |  Nullable |
| `nace_code` | `varchar` |  Nullable |
| `business_structure` | `varchar` |  Nullable |
| `is_public` | `bool` |  Nullable |
| `is_listed` | `bool` |  Nullable |
| `isin` | `varchar` |  Nullable |
| `cik` | `varchar` |  Nullable |
| `sedol` | `varchar` |  Nullable |
| `lei` | `varchar` |  Nullable |
| `reporting_frequency` | `varchar` |  Nullable |
| `accounting_standard` | `varchar` |  Nullable |
| `sustainability_standard` | `varchar` |  Nullable |
| `carbon_tax_region` | `varchar` |  Nullable |
| `data_protection_officer` | `varchar` |  Nullable |
| `privacy_policy_url` | `text` |  Nullable |
| `terms_url` | `text` |  Nullable |
| `is_active` | `bool` |  |
| `archived_at` | `timestamptz` |  Nullable |

## Table `users`

User accounts (auth.users mirror)

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `email` | `varchar` |  Unique |
| `password_hash` | `varchar` |  Nullable |
| `first_name` | `varchar` |  Nullable |
| `last_name` | `varchar` |  Nullable |
| `user_type` | `varchar` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `email_verified` | `bool` |  Nullable |
| `last_login` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `is_anonymised` | `bool` |  Nullable |

## Table `organization_members`

Organization membership

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

## Table `organization_metadata`

Organization extended metadata

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
| `total_floor_area_sqm` | `numeric` |  Nullable |
| `occupied_floor_area_sqm` | `numeric` |  Nullable |

## Table `organization_files`

Organization file storage

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

## Table `customer_documents`

Customer document storage

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `organization_member_id` | `uuid` |  |
| `asset_id` | `uuid` |  Nullable |
| `file_name` | `text` |  |
| `file_url` | `text` |  |
| `file_type` | `text` |  |
| `upload_date` | `timestamptz` |  Nullable |
| `status` | `text` |  |
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
| `processing_queue_id` | `uuid` |  Nullable |
| `supplier_id` | `uuid` |  Nullable |
| `product_category_id` | `uuid` |  Nullable |
| `processing_method` | `varchar` |  Nullable |
| `processing_status` | `varchar` |  Nullable |
| `processing_completed_at` | `timestamptz` |  Nullable |
| `extracted_data` | `jsonb` |  Nullable |
| `mapped_data` | `jsonb` |  Nullable |
| `calculated_emissions_kg_co2e` | `numeric` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `uploaded_by` | `uuid` |  Nullable |
| `processing_started_at` | `timestamptz` |  Nullable |
| `file_checksum` | `text` |  Nullable |

## Table `facilities`

Organization facilities/locations

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `name` | `varchar` |  |
| `postcode` | `varchar` |  Nullable |
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
| `eircode` | `varchar` |  Nullable |
| `meter_mpan_mprn` | `varchar` |  Nullable |

## Table `assets`

Assets within facilities

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
| `organization_id` | `uuid` |  Nullable |

## Table `suppliers`

Supplier records

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `name` | `varchar` |  |
| `type` | `varchar` |  Nullable |
| `supplier_category_id` | `uuid` |  Nullable |
| `contact_name` | `varchar` |  Nullable |
| `contact_email` | `varchar` |  Nullable |
| `contact_phone` | `varchar` |  Nullable |
| `address` | `text` |  Nullable |
| `website` | `varchar` |  Nullable |
| `tax_id` | `varchar` |  Nullable |
| `registration_number` | `varchar` |  Nullable |
| `annual_emissions_scope1` | `numeric` |  Nullable |
| `annual_emissions_scope2` | `numeric` |  Nullable |
| `annual_emissions_scope3` | `numeric` |  Nullable |
| `reporting_year` | `int4` |  Nullable |
| `emission_factor_scope1` | `numeric` |  Nullable |
| `emission_factor_scope2` | `numeric` |  Nullable |
| `emission_factor_scope3` | `numeric` |  Nullable |
| `emission_factor_unit` | `varchar` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `address_line1` | `varchar` |  Nullable |
| `address_line2` | `varchar` |  Nullable |
| `city` | `varchar` |  Nullable |
| `county` | `varchar` |  Nullable |
| `postcode` | `varchar` |  Nullable |
| `country` | `varchar` |  Nullable |
| `eircode` | `varchar` |  Nullable |
| `tax_region` | `varchar` |  Nullable |
| `tax_rate` | `numeric` |  Nullable |
| `vat_number` | `varchar` |  Nullable |
| `company_number` | `varchar` |  Nullable |
| `registration_region` | `varchar` |  Nullable |
| `primary_contact` | `varchar` |  Nullable |
| `primary_email` | `varchar` |  Nullable |
| `primary_phone` | `varchar` |  Nullable |
| `supplier_type` | `varchar` |  Nullable |
| `annual_emissions` | `numeric` |  Nullable |
| `emission_factor` | `numeric` |  Nullable |
| `supplier_rating` | `numeric` |  Nullable |
| `is_certified` | `bool` |  Nullable |
| `certification_type` | `text` |  Nullable |
| `certification_expiry` | `date` |  Nullable |
| `contract_start` | `date` |  Nullable |
| `contract_end` | `date` |  Nullable |
| `payment_terms` | `varchar` |  Nullable |
| `payment_currency` | `varchar` |  Nullable |
| `bank_name` | `varchar` |  Nullable |
| `bank_account` | `varchar` |  Nullable |
| `iban` | `varchar` |  Nullable |
| `swift_code` | `varchar` |  Nullable |
| `risk_score` | `numeric` |  Nullable |
| `compliance_status` | `varchar` |  Nullable |
| `sort_code` | `varchar` |  Nullable |

## Table `emission_factors`

Emission factors reference

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `reporting_year` | `int4` |  |
| `activity_type` | `varchar` |  |
| `co2e_multiplier` | `numeric` |  |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `unit` | `text` |  Nullable |
| `scope` | `text` |  Nullable |
| `factor_source` | `text` |  Nullable |
| `factor_set` | `text` |  Nullable |
| `country` | `varchar` |  Nullable |
| `region_deprecated` | `varchar` |  Nullable |
| `import_batch_id` | `uuid` |  Nullable |

## Table `emissions_logs`

Emission records

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `asset_id` | `uuid` |  Nullable |
| `emission_factor_id` | `uuid` |  Nullable |
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
| `organization_member_id` | `uuid` |  Nullable |
| `supplier_id` | `uuid` |  Nullable |
| `product_category_id` | `uuid` |  Nullable |
| `data_source` | `varchar` |  Nullable |
| `confidence_score` | `numeric` |  Nullable |
| `verified_by` | `uuid` |  Nullable |
| `verified_at` | `timestamptz` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `unit` | `text` |  Nullable |
| `scope` | `text` |  Nullable |
| `snapshot_id` | `uuid` |  Nullable |

## Table `conversations`

Conversation threads

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
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

## Table `conversation_participants`

Conversation participants

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

## Table `messages`

Messages within conversations

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `conversation_id` | `uuid` |  Nullable |
| `sender_id` | `uuid` |  Nullable |
| `receiver_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  |
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

## Table `file_attachments`

Message file attachments

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `message_id` | `uuid` |  Nullable |
| `conversation_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  |
| `file_name` | `text` |  |
| `file_url` | `text` |  |
| `file_size` | `int8` |  Nullable |
| `file_type` | `text` |  Nullable |
| `mime_type` | `text` |  Nullable |
| `uploaded_by` | `uuid` |  Nullable |
| `uploaded_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `notifications`

User notifications

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `recipient_type` | `varchar` |  |
| `recipient_id` | `uuid` |  |
| `notification_type` | `varchar` |  |
| `title` | `varchar` |  |
| `message` | `text` |  |
| `priority` | `varchar` |  Nullable |
| `link` | `text` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `is_read` | `bool` |  Nullable |
| `read_at` | `timestamptz` |  Nullable |
| `is_dismissed` | `bool` |  Nullable |
| `dismissed_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `notification_delivery`

Notification delivery tracking

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `notification_id` | `uuid` |  |
| `channel` | `varchar` |  |
| `status` | `varchar` |  Nullable |
| `sent_at` | `timestamptz` |  Nullable |
| `delivered_at` | `timestamptz` |  Nullable |
| `opened_at` | `timestamptz` |  Nullable |
| `error_message` | `text` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `document_processing_queue`

Document processing queue

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `customer_document_id` | `uuid` |  Nullable |
| `processing_type` | `varchar` |  |
| `status` | `varchar` |  Nullable |
| `file_name` | `varchar` |  |
| `file_url` | `text` |  |
| `file_size_bytes` | `int8` |  Nullable |
| `file_type` | `varchar` |  Nullable |
| `page_count` | `int4` |  Nullable |
| `ai_extraction_result` | `jsonb` |  Nullable |
| `ai_confidence_score` | `numeric` |  Nullable |
| `ai_extraction_method` | `varchar` |  Nullable |
| `ai_extracted_at` | `timestamptz` |  Nullable |
| `ai_processing_time_ms` | `int4` |  Nullable |
| `ai_mapped_facility_id` | `uuid` |  Nullable |
| `ai_mapped_asset_id` | `uuid` |  Nullable |
| `ai_mapped_supplier_id` | `uuid` |  Nullable |
| `ai_mapping_confidence` | `numeric` |  Nullable |
| `ai_mapped_document_type_code` | `varchar` |  Nullable |
| `manual_requested_by` | `uuid` |  Nullable |
| `manual_requested_at` | `timestamptz` |  Nullable |
| `manual_assigned_to` | `uuid` |  Nullable |
| `manual_assigned_by` | `uuid` |  Nullable |
| `manual_assigned_at` | `timestamptz` |  Nullable |
| `manual_extraction_result` | `jsonb` |  Nullable |
| `manual_extracted_by` | `uuid` |  Nullable |
| `manual_extracted_at` | `timestamptz` |  Nullable |
| `manual_notes` | `text` |  Nullable |
| `qc_required` | `bool` |  |
| `qc_by` | `uuid` |  Nullable |
| `qc_at` | `timestamptz` |  Nullable |
| `qc_notes` | `text` |  Nullable |
| `qc_approved` | `bool` |  Nullable |
| `customer_reviewed_by` | `uuid` |  Nullable |
| `customer_reviewed_at` | `timestamptz` |  Nullable |
| `customer_approved` | `bool` |  |
| `customer_rejection_reason` | `text` |  Nullable |
| `customer_notes` | `text` |  Nullable |
| `calculated_emissions_kg_co2e` | `numeric` |  Nullable |
| `emission_factor_used` | `uuid` |  Nullable |
| `emission_calculation_method` | `varchar` |  Nullable |
| `batch_id` | `uuid` |  Nullable |
| `batch_sequence` | `int4` |  Nullable |
| `processing_cost` | `numeric` |  Nullable |
| `billing_currency` | `varchar` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `completed_at` | `timestamptz` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `workflow_error_count` | `int4` |  Nullable |
| `workflow_next_retry_at` | `timestamptz` |  Nullable |

## Table `processing_queue`

Processing queue

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `document_id` | `uuid` |  |
| `organization_id` | `uuid` |  |
| `batch_id` | `uuid` |  Nullable |
| `document_type` | `varchar` |  |
| `priority` | `int4` |  Nullable |
| `priority_score` | `int4` |  Nullable |
| `queue_status` | `varchar` |  |
| `sla_deadline` | `timestamptz` |  Nullable |
| `sla_breached` | `bool` |  |
| `estimated_completion_hours` | `int4` |  Nullable |
| `actual_completion_hours` | `int4` |  Nullable |
| `page_count` | `int4` |  Nullable |
| `file_size_bytes` | `int8` |  Nullable |
| `notes` | `text` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_by` | `uuid` |  Nullable |

## Table `processing_assignments`

Queue task assignments

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `queue_id` | `uuid` |  |
| `assigned_to` | `uuid` |  |
| `assigned_by` | `uuid` |  |
| `assignment_status` | `varchar` |  Nullable |
| `started_at` | `timestamptz` |  Nullable |
| `completed_at` | `timestamptz` |  Nullable |
| `processing_time_seconds` | `int4` |  Nullable |
| `notes` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `processing_steps`

Processing step tracking

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `assignment_id` | `uuid` |  |
| `step_name` | `varchar` |  |
| `step_order` | `int4` |  |
| `status` | `varchar` |  Nullable |
| `started_at` | `timestamptz` |  Nullable |
| `completed_at` | `timestamptz` |  Nullable |
| `duration_seconds` | `int4` |  Nullable |
| `notes` | `text` |  Nullable |
| `errors` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `manual_extraction_batches`

Manual extraction batches

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `batch_name` | `varchar` |  |
| `batch_description` | `text` |  Nullable |
| `total_documents` | `int4` |  |
| `total_pages` | `int4` |  |
| `total_cost` | `numeric` |  |
| `price_per_page` | `numeric` |  Nullable |
| `currency` | `varchar` |  Nullable |
| `status` | `varchar` |  Nullable |
| `estimated_completion_date` | `timestamptz` |  Nullable |
| `actual_completion_date` | `timestamptz` |  Nullable |
| `sla_deadline` | `timestamptz` |  Nullable |
| `sla_breached` | `bool` |  Nullable |
| `assigned_to` | `uuid` |  Nullable |
| `assigned_by` | `uuid` |  Nullable |
| `assigned_at` | `timestamptz` |  Nullable |
| `qc_by` | `uuid` |  Nullable |
| `qc_at` | `timestamptz` |  Nullable |
| `qc_notes` | `text` |  Nullable |
| `qc_approved` | `bool` |  Nullable |
| `customer_notes` | `text` |  Nullable |
| `staff_notes` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `completed_by` | `uuid` |  Nullable |
| `completed_at` | `timestamptz` |  Nullable |

## Table `manual_extraction_items`

Manual extraction items

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `batch_id` | `uuid` |  |
| `document_processing_queue_id` | `uuid` |  Nullable |
| `file_name` | `varchar` |  |
| `file_url` | `text` |  |
| `page_count` | `int4` |  |
| `document_type` | `varchar` |  Nullable |
| `status` | `varchar` |  Nullable |
| `extracted_data` | `jsonb` |  Nullable |
| `mapped_data` | `jsonb` |  Nullable |
| `mapped_facility_id` | `uuid` |  Nullable |
| `mapped_asset_id` | `uuid` |  Nullable |
| `mapped_supplier_id` | `uuid` |  Nullable |
| `calculated_emissions_kg_co2e` | `numeric` |  Nullable |
| `emission_factor_used` | `uuid` |  Nullable |
| `extracted_by` | `uuid` |  Nullable |
| `extracted_at` | `timestamptz` |  Nullable |
| `qc_by` | `uuid` |  Nullable |
| `qc_at` | `timestamptz` |  Nullable |
| `qc_notes` | `text` |  Nullable |
| `quality_score` | `int4` |  Nullable |
| `customer_reviewed_by` | `uuid` |  Nullable |
| `customer_reviewed_at` | `timestamptz` |  Nullable |
| `customer_approved` | `bool` |  Nullable |
| `customer_rejection_reason` | `text` |  Nullable |
| `customer_notes` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `report_templates`

Report templates

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  Nullable |
| `name` | `varchar` |  |
| `description` | `text` |  Nullable |
| `report_type` | `varchar` |  |
| `template_structure` | `jsonb` |  |
| `ai_prompts` | `jsonb` |  Nullable |
| `logo_url` | `text` |  Nullable |
| `primary_color` | `varchar` |  Nullable |
| `secondary_color` | `varchar` |  Nullable |
| `font_family` | `varchar` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `is_default` | `bool` |  Nullable |
| `is_system` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `updated_by` | `uuid` |  Nullable |

## Table `report_generation_queue`

Report generation queue

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `user_id` | `uuid` |  Nullable |
| `template_id` | `uuid` |  Nullable |
| `report_type` | `varchar` |  |
| `reporting_year` | `int4` |  |
| `report_name` | `varchar` |  Nullable |
| `data_sources` | `jsonb` |  Nullable |
| `status` | `varchar` |  Nullable |
| `progress_percentage` | `int4` |  Nullable |
| `current_step` | `varchar` |  Nullable |
| `generated_content` | `jsonb` |  Nullable |
| `user_edits` | `jsonb` |  Nullable |
| `final_report_url` | `text` |  Nullable |
| `final_report_file_name` | `varchar` |  Nullable |
| `final_report_size_bytes` | `int8` |  Nullable |
| `ai_model_used` | `varchar` |  Nullable |
| `ai_tokens_used` | `int4` |  Nullable |
| `ai_cost` | `numeric` |  Nullable |
| `ai_processing_time_ms` | `int4` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `started_at` | `timestamptz` |  Nullable |
| `completed_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `error_log` | `text` |  Nullable |

## Table `report_versions`

Report version history

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `report_id` | `uuid` |  |
| `version_number` | `int4` |  |
| `content` | `jsonb` |  Nullable |
| `file_url` | `text` |  Nullable |
| `file_name` | `varchar` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `notes` | `text` |  Nullable |
| `change_summary` | `text` |  Nullable |
| `is_current` | `bool` |  Nullable |

## Table `report_comments`

Report comments

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `report_id` | `uuid` |  |
| `user_id` | `uuid` |  |
| `section_id` | `varchar` |  Nullable |
| `comment` | `text` |  |
| `comment_type` | `varchar` |  Nullable |
| `is_resolved` | `bool` |  Nullable |
| `resolved_at` | `timestamptz` |  Nullable |
| `resolved_by` | `uuid` |  Nullable |
| `resolution_notes` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `ai_content_history`

AI generation history

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `report_id` | `uuid` |  Nullable |
| `prompt_type` | `varchar` |  |
| `prompt_text` | `text` |  Nullable |
| `model_used` | `varchar` |  Nullable |
| `generated_content` | `text` |  Nullable |
| `content_format` | `varchar` |  Nullable |
| `tokens_used` | `int4` |  Nullable |
| `processing_time_ms` | `int4` |  Nullable |
| `cost` | `numeric` |  Nullable |
| `user_rating` | `int4` |  Nullable |
| `user_feedback` | `text` |  Nullable |
| `was_accepted` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |

## Table `consultant_profiles`

Consultant firm profiles

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  |
| `company_name` | `varchar` |  |
| `company_number` | `varchar` |  Nullable |
| `website` | `varchar` |  Nullable |
| `phone` | `varchar` |  Nullable |
| `brand_name` | `varchar` |  Nullable |
| `logo_url` | `text` |  Nullable |
| `primary_color` | `varchar` |  Nullable |
| `secondary_color` | `varchar` |  Nullable |
| `footer_text` | `text` |  Nullable |
| `email_from` | `varchar` |  Nullable |
| `default_plan` | `varchar` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `address_line1` | `varchar` |  Nullable |
| `address_line2` | `varchar` |  Nullable |
| `city` | `varchar` |  Nullable |
| `county` | `varchar` |  Nullable |
| `postcode` | `varchar` |  Nullable |
| `country` | `varchar` |  Nullable |
| `eircode` | `varchar` |  Nullable |
| `vat_number` | `varchar` |  Nullable |
| `registration_region` | `varchar` |  Nullable |
| `tax_region` | `varchar` |  Nullable |
| `tax_rate` | `numeric` |  Nullable |
| `firm_type` | `varchar` |  Nullable |
| `firm_size` | `varchar` |  Nullable |
| `industries_served` | `_text` |  Nullable |
| `expertise` | `_text` |  Nullable |
| `certifications` | `_text` |  Nullable |
| `annual_revenue` | `numeric` |  Nullable |
| `revenue_currency` | `varchar` |  Nullable |
| `employee_count` | `int4` |  Nullable |
| `founded_year` | `int4` |  Nullable |
| `partner_since` | `date` |  Nullable |
| `partner_status` | `varchar` |  Nullable |
| `partner_tier` | `varchar` |  Nullable |
| `commission_rate` | `numeric` |  Nullable |
| `referral_code` | `varchar` |  Nullable |
| `co_branding_enabled` | `bool` |  Nullable |
| `api_key` | `varchar` |  Nullable |
| `webhook_url` | `text` |  Nullable |
| `client_portal_url` | `text` |  Nullable |
| `support_hours` | `varchar` |  Nullable |
| `support_phone` | `varchar` |  Nullable |
| `support_email` | `varchar` |  Nullable |

## Table `consultant_clients`

Consultant-client relationships

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `consultant_id` | `uuid` |  |
| `organization_id` | `uuid` |  |
| `client_name` | `varchar` |  |
| `client_industry` | `varchar` |  Nullable |
| `client_contact_email` | `varchar` |  Nullable |
| `client_contact_name` | `varchar` |  Nullable |
| `client_contact_phone` | `varchar` |  Nullable |
| `status` | `varchar` |  Nullable |
| `billing_plan` | `varchar` |  Nullable |
| `billing_cycle` | `varchar` |  Nullable |
| `notes` | `text` |  Nullable |
| `tags` | `_text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |

## Table `consultant_firm_members`

Consultant firm team members

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `firm_id` | `uuid` |  |
| `user_id` | `uuid` |  |
| `role` | `varchar` |  |
| `can_manage_clients` | `bool` |  Nullable |
| `can_upload_documents` | `bool` |  Nullable |
| `can_generate_reports` | `bool` |  Nullable |
| `can_manage_team` | `bool` |  Nullable |
| `client_access` | `_uuid` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `invited_by` | `uuid` |  Nullable |
| `invited_at` | `timestamptz` |  Nullable |
| `joined_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `role_id` | `uuid` |  Nullable |
| `permissions` | `jsonb` |  Nullable |

## Table `consultant_tasks`

Consultant tasks

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `consultant_id` | `uuid` |  |
| `client_id` | `uuid` |  Nullable |
| `task_title` | `varchar` |  |
| `task_description` | `text` |  Nullable |
| `task_type` | `varchar` |  Nullable |
| `priority` | `varchar` |  Nullable |
| `status` | `varchar` |  Nullable |
| `assigned_to` | `uuid` |  Nullable |
| `assigned_by` | `uuid` |  Nullable |
| `due_date` | `timestamptz` |  Nullable |
| `completed_at` | `timestamptz` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `consultant_billing`

Consultant billing

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `consultant_id` | `uuid` |  |
| `client_id` | `uuid` |  Nullable |
| `plan` | `varchar` |  Nullable |
| `auto_extraction_limit` | `int4` |  Nullable |
| `manual_extraction_credit` | `int4` |  Nullable |
| `auto_extraction_used` | `int4` |  Nullable |
| `manual_extraction_used` | `int4` |  Nullable |
| `billing_cycle` | `varchar` |  Nullable |
| `subscription_start_date` | `timestamptz` |  Nullable |
| `subscription_end_date` | `timestamptz` |  Nullable |
| `auto_extraction_price` | `numeric` |  Nullable |
| `manual_extraction_price` | `numeric` |  Nullable |
| `last_invoice_date` | `timestamptz` |  Nullable |
| `next_invoice_date` | `timestamptz` |  Nullable |
| `stripe_subscription_id` | `varchar` |  Nullable |
| `stripe_customer_id` | `varchar` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `currency` | `varchar` |  Nullable |

## Table `customer_subscriptions`

Customer subscriptions

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `plan` | `varchar` |  |
| `status` | `varchar` |  Nullable |
| `ai_extraction_limit` | `int4` |  Nullable |
| `ai_extraction_used` | `int4` |  Nullable |
| `batch_upload_limit` | `int4` |  Nullable |
| `batch_upload_per_day` | `int4` |  Nullable |
| `manual_extraction_pages_included` | `int4` |  Nullable |
| `manual_extraction_pages_used` | `int4` |  Nullable |
| `price_per_ai_extra` | `numeric` |  Nullable |
| `price_per_manual_page` | `numeric` |  Nullable |
| `currency` | `varchar` |  Nullable |
| `features` | `jsonb` |  Nullable |
| `stripe_subscription_id` | `varchar` |  Nullable |
| `stripe_customer_id` | `varchar` |  Nullable |
| `stripe_price_id` | `varchar` |  Nullable |
| `billing_period_start` | `date` |  Nullable |
| `billing_period_end` | `date` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `cancelled_at` | `timestamptz` |  Nullable |
| `cancelled_by` | `uuid` |  Nullable |

## Table `usage_tracking`

Usage tracking

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `usage_date` | `date` |  Nullable |
| `usage_month` | `date` |  Nullable |
| `ai_files_processed` | `int4` |  Nullable |
| `batch_files_uploaded` | `int4` |  Nullable |
| `manual_pages_extracted` | `int4` |  Nullable |
| `reports_generated` | `int4` |  Nullable |
| `total_storage_bytes` | `int8` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `staff_roles`

Staff role definitions

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `name` | `varchar` |  Unique |
| `description` | `text` |  Nullable |
| `permissions` | `jsonb` |  |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_by` | `uuid` |  Nullable |

## Table `staff_profiles`

Staff profiles

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  |
| `first_name` | `varchar` |  |
| `last_name` | `varchar` |  |
| `email` | `varchar` |  Unique |
| `role_id` | `uuid` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `hire_date` | `date` |  Nullable |
| `skills` | `jsonb` |  Nullable |
| `max_concurrent_tasks` | `int4` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `entity_id` | `uuid` |  Nullable |

## Table `staff_workload`

Staff workload tracking

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `staff_id` | `uuid` |  |
| `assigned_tasks` | `int4` |  Nullable |
| `in_progress_tasks` | `int4` |  Nullable |
| `pending_tasks` | `int4` |  Nullable |
| `completed_today` | `int4` |  Nullable |
| `workload_score` | `numeric` |  Nullable |
| `capacity_percentage` | `numeric` |  Nullable |
| `date` | `date` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `staff_performance`

Staff performance metrics

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `staff_id` | `uuid` |  |
| `period_start` | `date` |  |
| `period_end` | `date` |  |
| `period_type` | `varchar` |  |
| `total_assigned` | `int4` |  Nullable |
| `total_completed` | `int4` |  Nullable |
| `total_rejected` | `int4` |  Nullable |
| `avg_processing_time_seconds` | `int4` |  Nullable |
| `qc_pass_rate` | `numeric` |  Nullable |
| `accuracy_rate` | `numeric` |  Nullable |
| `productivity_score` | `numeric` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `qc_checklists`

QC checklists

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `document_type` | `varchar` |  |
| `checklist_name` | `varchar` |  |
| `checklist_items` | `jsonb` |  |
| `is_active` | `bool` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_by` | `uuid` |  Nullable |

## Table `qc_checks`

QC check results

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `assignment_id` | `uuid` |  |
| `qc_by` | `uuid` |  |
| `qc_status` | `varchar` |  Nullable |
| `qc_score` | `int4` |  Nullable |
| `checks_passed` | `int4` |  Nullable |
| `checks_failed` | `int4` |  Nullable |
| `notes` | `text` |  Nullable |
| `reviewed_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `qc_errors`

QC errors

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `qc_check_id` | `uuid` |  |
| `error_type` | `varchar` |  |
| `field_name` | `varchar` |  Nullable |
| `expected_value` | `text` |  Nullable |
| `actual_value` | `text` |  Nullable |
| `severity` | `varchar` |  Nullable |
| `notes` | `text` |  Nullable |
| `is_resolved` | `bool` |  Nullable |
| `resolved_at` | `timestamptz` |  Nullable |
| `resolved_by` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `approval_requests`

Approval requests

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `assignment_id` | `uuid` |  |
| `requested_by` | `uuid` |  |
| `requested_at` | `timestamptz` |  Nullable |
| `approval_type` | `varchar` |  |
| `status` | `varchar` |  Nullable |
| `priority` | `varchar` |  Nullable |
| `notes` | `text` |  Nullable |
| `sla_deadline` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `approval_decisions`

Approval decisions

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `approval_request_id` | `uuid` |  |
| `decision_by` | `uuid` |  |
| `decision_at` | `timestamptz` |  Nullable |
| `decision` | `varchar` |  |
| `reason` | `text` |  Nullable |
| `comments` | `text` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `audit_logs`

Audit log

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

## Table `activity_logs`

Activity log

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

## Table `activity_feed`

Activity feed

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

## Table `beta_access_codes`

Beta access codes

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

Beta users

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

## Table `pending_invites`

Pending invites

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `email` | `varchar` |  |
| `role` | `varchar` |  |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `user_invitations`

User invitations

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

## Table `waitlist`

Waitlist

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

## Table `password_reset_tokens`

Password reset tokens

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  Nullable |
| `token` | `varchar` |  Unique |
| `expires_at` | `timestamptz` |  |
| `used` | `bool` |  Nullable |
| `used_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `typing_status`

Typing status

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

User presence

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `user_id` | `uuid` |  Nullable |
| `status` | `text` |  Nullable |
| `last_seen_at` | `timestamptz` |  Nullable |
| `current_channel` | `text` |  Nullable |
| `metadata` | `jsonb` |  Nullable |

## Table `customer_review_log`

Customer review log

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

## Table `customer_verifications`

Customer verifications

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `customer_document_id` | `uuid` |  Nullable |
| `organization_id` | `uuid` |  |
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

## Table `document_activity_log`

Document activity log

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

## Table `processing_logs`

Processing logs

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

## Table `email_logs`

Email logs

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

## Table `user_activity_log`

User activity log

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

## Table `system_settings`

System configuration settings

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `setting_key` | `varchar` |  Unique |
| `setting_value` | `jsonb` |  |
| `setting_type` | `varchar` |  Nullable |
| `description` | `text` |  Nullable |
| `is_editable` | `bool` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `default_currency` | `varchar` |  Nullable |
| `default_language` | `varchar` |  Nullable |
| `default_timezone` | `varchar` |  Nullable |
| `default_region` | `varchar` |  Nullable |
| `default_reporting_standard` | `varchar` |  Nullable |
| `date_format` | `varchar` |  Nullable |
| `time_format` | `varchar` |  Nullable |
| `number_format` | `varchar` |  Nullable |
| `week_start_day` | `varchar` |  Nullable |
| `default_tax_region` | `varchar` |  Nullable |
| `default_tax_rate` | `numeric` |  Nullable |
| `default_vat_rate` | `numeric` |  Nullable |
| `default_emission_factor_set` | `varchar` |  Nullable |
| `default_emission_factor_year` | `int4` |  Nullable |
| `carbon_tax_region` | `varchar` |  Nullable |
| `carbon_tax_rate` | `numeric` |  Nullable |
| `carbon_tax_unit` | `varchar` |  Nullable |
| `emission_verification_required` | `bool` |  Nullable |
| `emission_verification_standard` | `varchar` |  Nullable |
| `sla_default_hours` | `int4` |  Nullable |
| `sla_escalation_hours` | `int4` |  Nullable |
| `sla_breach_alert_enabled` | `bool` |  Nullable |
| `sla_breach_alert_recipients` | `text` |  Nullable |
| `max_upload_size_mb` | `int4` |  Nullable |
| `max_batch_size_mb` | `int4` |  Nullable |
| `max_file_upload_daily` | `int4` |  Nullable |
| `max_documents_per_batch` | `int4` |  Nullable |
| `max_pages_per_document` | `int4` |  Nullable |
| `api_rate_limit` | `int4` |  Nullable |
| `api_rate_limit_burst` | `int4` |  Nullable |
| `webhook_retry_count` | `int4` |  Nullable |
| `webhook_retry_delay` | `int4` |  Nullable |
| `webhook_timeout_seconds` | `int4` |  Nullable |
| `session_timeout_minutes` | `int4` |  Nullable |
| `session_extend_on_activity` | `bool` |  Nullable |
| `two_factor_required` | `bool` |  Nullable |
| `two_factor_method` | `varchar` |  Nullable |
| `password_expiry_days` | `int4` |  Nullable |
| `password_min_length` | `int4` |  Nullable |
| `password_require_special` | `bool` |  Nullable |
| `password_require_number` | `bool` |  Nullable |
| `password_require_uppercase` | `bool` |  Nullable |
| `password_require_lowercase` | `bool` |  Nullable |
| `login_attempts_max` | `int4` |  Nullable |
| `login_attempts_lockout_minutes` | `int4` |  Nullable |
| `audit_log_retention_days` | `int4` |  Nullable |
| `data_retention_days` | `int4` |  Nullable |
| `document_retention_days` | `int4` |  Nullable |
| `backup_frequency` | `varchar` |  Nullable |
| `backup_retention_days` | `int4` |  Nullable |
| `backup_storage_location` | `text` |  Nullable |

## Table `queue_settings`

Queue configuration settings

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `setting_key` | `varchar` |  Unique |
| `setting_value` | `jsonb` |  |
| `description` | `text` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `sla_definitions`

SLA definitions

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `document_type` | `varchar` |  |
| `priority_level` | `varchar` |  |
| `sla_hours` | `int4` |  |
| `escalation_hours` | `int4` |  Nullable |
| `is_active` | `bool` |  Nullable |
| `description` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `business_hours`

Business hours configuration

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `day_of_week` | `varchar` |  Unique |
| `is_working_day` | `bool` |  Nullable |
| `start_time` | `time` |  Nullable |
| `end_time` | `time` |  Nullable |
| `is_holiday` | `bool` |  Nullable |
| `holiday_name` | `varchar` |  Nullable |
| `timezone` | `varchar` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `draft_entries`

Draft entries

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

## Table `export_history`

Export history

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

## Table `upload_batches`

Upload batches

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `batch_name` | `varchar` |  Nullable |
| `total_files` | `int4` |  Nullable |
| `processed_files` | `int4` |  Nullable |
| `status` | `text` |  Nullable |
| `created_by_user_id` | `uuid` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `completed_at` | `timestamptz` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |
| `batch_type` | `varchar` |  Nullable |
| `estimated_processing_time` | `timestamptz` |  Nullable |
| `error_count` | `int4` |  Nullable |
| `manual_extraction_requested` | `bool` |  Nullable |
| `manual_extraction_batch_id` | `uuid` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `updated_by` | `uuid` |  Nullable |
| `entity_id` | `uuid` |  Nullable |

## Table `user_feedback`

User feedback

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

## Table `manual_review_queue`

Manual review queue items

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
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
| `entity_id` | `uuid` |  Nullable |

## Table `review_assignment_history`

Review assignment history

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

## Table `review_audit_trail`

Review audit trail

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

## Table `verification_activity_log`

Verification activity log

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

## Table `message_activity_log`

Message activity log

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

## Table `conversation_activity_log`

Conversation activity log

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

## Table `verification_logs`

Verification logs

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `document_id` | `uuid` |  |
| `verified_by` | `uuid` |  |
| `verified_at` | `timestamptz` |  Nullable |
| `verification_status` | `varchar` |  |
| `verification_notes` | `text` |  Nullable |
| `verification_data` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `audit_trail`

Generic audit trail

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `action_type` | `varchar` |  |
| `table_name` | `varchar` |  |
| `record_id` | `uuid` |  |
| `performed_by` | `uuid` |  |
| `performed_at` | `timestamptz` |  Nullable |
| `old_data` | `jsonb` |  Nullable |
| `new_data` | `jsonb` |  Nullable |
| `changes` | `jsonb` |  Nullable |
| `ip_address` | `inet` |  Nullable |
| `user_agent` | `text` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `staff_activity_log`

Staff activity log

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `staff_id` | `uuid` |  |
| `activity_type` | `varchar` |  |
| `activity_details` | `jsonb` |  Nullable |
| `ip_address` | `inet` |  Nullable |
| `user_agent` | `text` |  Nullable |
| `session_id` | `uuid` |  Nullable |
| `duration_seconds` | `int4` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `login_history`

Login history

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `staff_id` | `uuid` |  |
| `login_at` | `timestamptz` |  Nullable |
| `logout_at` | `timestamptz` |  Nullable |
| `ip_address` | `inet` |  Nullable |
| `user_agent` | `text` |  Nullable |
| `session_id` | `uuid` |  Nullable |
| `is_successful` | `bool` |  Nullable |
| `failure_reason` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `staff_daily_performance`

Staff daily performance

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `staff_id` | `uuid` |  |
| `date` | `date` |  |
| `total_assigned` | `int4` |  Nullable |
| `completed` | `int4` |  Nullable |
| `rejected` | `int4` |  Nullable |
| `qc_passed` | `int4` |  Nullable |
| `qc_failed` | `int4` |  Nullable |
| `total_processing_time_seconds` | `int4` |  Nullable |
| `avg_time_per_document_seconds` | `int4` |  Nullable |
| `productivity_score` | `numeric` |  Nullable |
| `quality_score` | `numeric` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `team_performance`

Team performance

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `date` | `date` |  Unique |
| `total_staff_active` | `int4` |  Nullable |
| `total_assigned` | `int4` |  Nullable |
| `total_completed` | `int4` |  Nullable |
| `total_rejected` | `int4` |  Nullable |
| `avg_processing_time_seconds` | `int4` |  Nullable |
| `qc_pass_rate` | `numeric` |  Nullable |
| `sla_compliance_rate` | `numeric` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `sla_compliance`

SLA compliance tracking

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `document_type` | `varchar` |  |
| `queue_id` | `uuid` |  |
| `sla_deadline` | `timestamptz` |  |
| `completed_at` | `timestamptz` |  Nullable |
| `is_breached` | `bool` |  Nullable |
| `breach_reason` | `text` |  Nullable |
| `breach_time_minutes` | `int4` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `reassignment_history`

Reassignment history

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `assignment_id` | `uuid` |  |
| `previous_staff_id` | `uuid` |  Nullable |
| `new_staff_id` | `uuid` |  |
| `reassigned_by` | `uuid` |  |
| `reason` | `varchar` |  Nullable |
| `notes` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `processing_time_log`

Processing time logs

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `assignment_id` | `uuid` |  |
| `staff_id` | `uuid` |  |
| `activity_type` | `varchar` |  |
| `start_time` | `timestamptz` |  |
| `end_time` | `timestamptz` |  Nullable |
| `duration_seconds` | `int4` |  Nullable |
| `paused_duration_seconds` | `int4` |  Nullable |
| `notes` | `text` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `processing_audit_trail`

Processing audit trail

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `queue_id` | `uuid` |  |
| `action` | `varchar` |  |
| `performed_by` | `uuid` |  Nullable |
| `performed_by_staff` | `uuid` |  Nullable |
| `performed_by_type` | `varchar` |  Nullable |
| `previous_value` | `jsonb` |  Nullable |
| `new_value` | `jsonb` |  Nullable |
| `notes` | `text` |  Nullable |
| `duration_ms` | `int4` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `dashboard_metrics`

Dashboard metrics cache

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `metric_type` | `varchar` |  |
| `metric_name` | `varchar` |  |
| `metric_value` | `jsonb` |  |
| `period` | `varchar` |  Nullable |
| `expires_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |

## Table `customer_communication`

Customer communication records

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `staff_id` | `uuid` |  |
| `communication_type` | `varchar` |  |
| `subject` | `varchar` |  Nullable |
| `content` | `text` |  |
| `is_internal` | `bool` |  Nullable |
| `sent_by` | `uuid` |  |
| `sent_at` | `timestamptz` |  Nullable |
| `is_read` | `bool` |  Nullable |
| `read_at` | `timestamptz` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_at` | `timestamptz` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `import_batches`

Versioned import batches for emission-factor provider datasets (Backend v2.1, Import Platform).

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `provider_key` | `varchar` |  |
| `provider_version` | `varchar` |  |
| `source_file` | `text` |  |
| `source_checksum` | `varchar` |  |
| `reporting_year` | `int4` |  |
| `status` | `varchar` |  |
| `rows_total` | `int4` |  Nullable |
| `rows_imported` | `int4` |  Nullable |
| `rows_skipped` | `int4` |  Nullable |
| `rows_duplicate` | `int4` |  Nullable |
| `errors` | `jsonb` |  Nullable |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  Nullable |
| `created_by` | `uuid` |  Nullable |
| `rolled_back_from` | `uuid` |  Nullable |
| `updated_at` | `timestamptz` |  Nullable |

## Table `calculation_snapshots`

Immutable forensic record of every emissions calculation. Append-only; never updated or deleted (Backend v2.1 ADR-5).

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `organization_id` | `uuid` |  |
| `activity` | `varchar` |  |
| `activity_type` | `varchar` |  |
| `quantity` | `numeric` |  |
| `quantity_unit` | `varchar` |  |
| `co2e_multiplier` | `numeric` |  |
| `co2e_kg` | `numeric` |  |
| `scope` | `varchar` |  Nullable |
| `date` | `date` |  |
| `factor_id` | `uuid` |  |
| `factor_source` | `varchar` |  Nullable |
| `factor_set` | `varchar` |  Nullable |
| `import_batch_id` | `uuid` |  Nullable |
| `reporting_year` | `int4` |  |
| `methodology` | `varchar` |  |
| `algorithm_version` | `varchar` |  |
| `content_hash` | `varchar` |  |
| `calculated_at` | `timestamptz` |  Nullable |
| `calculated_by` | `varchar` |  Nullable |
| `request_id` | `uuid` |  Nullable |

## Table `domain_events`

Append-only domain event store. Written by the EventBus, read by audit and replay (Backend v2.1 §14).

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `event_type` | `varchar` |  |
| `occurred_at` | `timestamptz` |  |
| `correlation_id` | `uuid` |  |
| `aggregate_id` | `uuid` |  |
| `aggregate_type` | `varchar` |  |
| `payload` | `jsonb` |  |
| `created_at` | `timestamptz` |  Nullable |

