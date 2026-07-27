


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE OR REPLACE FUNCTION "public"."get_admin_customer_overview"() RETURNS TABLE("organization_id" "uuid", "organization_name" character varying, "company_number" character varying, "member_count" bigint, "facility_count" bigint, "asset_count" bigint, "total_emissions_kg_co2e" numeric, "subscription_tier" "text", "joined_at" timestamp with time zone, "last_activity" timestamp with time zone)
    LANGUAGE "sql" SECURITY DEFINER
    AS $$
  SELECT 
    o.id AS organization_id,
    o.name AS organization_name,
    o.company_number,
    COUNT(DISTINCT om.user_id) AS member_count,
    COUNT(DISTINCT f.id) AS facility_count,
    COUNT(DISTINCT a.id) AS asset_count,
    COALESCE(SUM(el.calculated_kg_co2e), 0) AS total_emissions_kg_co2e,
    'free' AS subscription_tier, -- Placeholder until you add subscription logic
    o.created_at AS joined_at,
    MAX(el.created_at) AS last_activity
  FROM organizations o
  LEFT JOIN organization_members om ON o.id = om.organization_id
  LEFT JOIN facilities f ON o.id = f.organization_id
  LEFT JOIN assets a ON f.id = a.facility_id
  LEFT JOIN emissions_logs el ON o.id = el.organization_id
  GROUP BY o.id, o.name, o.company_number, o.created_at
  ORDER BY o.created_at DESC;
$$;


ALTER FUNCTION "public"."get_admin_customer_overview"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_admin_dashboard_stats"() RETURNS json
    LANGUAGE "sql" SECURITY DEFINER
    AS $$
  SELECT json_build_object(
    'total_organizations', (SELECT COUNT(*) FROM organizations),
    'total_users', (SELECT COUNT(DISTINCT user_id) FROM organization_members),
    'total_facilities', (SELECT COUNT(*) FROM facilities),
    'total_assets', (SELECT COUNT(*) FROM assets),
    'total_emissions_kg', (SELECT COALESCE(SUM(calculated_kg_co2e), 0) FROM emissions_logs),
    'pending_reviews', (SELECT COUNT(*) FROM manual_review_queue WHERE status = 'pending'),
    'emissions_by_month', (
      SELECT json_agg(row_to_json(t))
      FROM (
        SELECT 
          to_char(start_date, 'Mon YYYY') as month,
          SUM(calculated_kg_co2e) as total_kg_co2e
        FROM emissions_logs
        GROUP BY month, start_date
        ORDER BY start_date ASC
        LIMIT 12
      ) t
    ),
    'emissions_by_scope', (
      SELECT json_agg(row_to_json(t))
      FROM (
        SELECT 
          COALESCE(d.activity_type, 'Unknown') as scope,
          SUM(e.calculated_kg_co2e) as total_kg_co2e
        FROM emissions_logs e
        LEFT JOIN defra_conversion_factors d ON e.defra_factor_id = d.id
        GROUP BY d.activity_type
      ) t
    ),
    'recent_organizations', (
      SELECT json_agg(row_to_json(t))
      FROM (
        SELECT name, created_at
        FROM organizations
        ORDER BY created_at DESC
        LIMIT 5
      ) t
    )
  );
$$;


ALTER FUNCTION "public"."get_admin_dashboard_stats"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_platform_users"() RETURNS TABLE("user_id" "uuid", "email" character varying, "created_at" timestamp with time zone, "last_sign_in_at" timestamp with time zone, "email_confirmed" boolean, "organization_name" character varying, "organization_id" "uuid", "member_role" character varying, "account_status" "text")
    LANGUAGE "sql" SECURITY DEFINER
    AS $$
  SELECT 
    u.id AS user_id,
    u.email::VARCHAR,
    u.created_at,
    u.last_sign_in_at,
    (u.email_confirmed_at IS NOT NULL) AS email_confirmed,
    o.name AS organization_name,
    o.id AS organization_id,
    om.role AS member_role,
    CASE 
      WHEN u.banned_until IS NOT NULL AND u.banned_until > NOW() THEN 'Banned'
      WHEN u.email_confirmed_at IS NULL THEN 'Pending Confirmation'
      ELSE 'Active'
    END AS account_status
  FROM auth.users u
  LEFT JOIN organization_members om ON u.id = om.user_id
  LEFT JOIN organizations o ON om.organization_id = o.id
  ORDER BY u.created_at DESC;
$$;


ALTER FUNCTION "public"."get_platform_users"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_new_user"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  new_org_id UUID;
  invite_record RECORD;
BEGIN
  -- Try to find a pending invite (case-insensitive match to be safe)
  SELECT id, organization_id, role INTO invite_record 
  FROM pending_invites 
  WHERE LOWER(email) = LOWER(NEW.email);

  IF FOUND THEN
    -- SCENARIO A: User was invited. Add them to the existing org.
    INSERT INTO organization_members (organization_id, user_id, role)
    VALUES (invite_record.organization_id, NEW.id, invite_record.role);
    
    -- Delete the used invite
    DELETE FROM pending_invites WHERE id = invite_record.id;
  ELSE
    -- SCENARIO B: Brand new user. Create a new org for them.
    INSERT INTO organizations (name, company_number)
    VALUES (
      COALESCE(NEW.raw_user_meta_data->>'company_name', 'My Company'),
      COALESCE(NEW.raw_user_meta_data->>'company_number', NULL)
    )
    RETURNING id INTO new_org_id;
    
    -- Make them admin of their new org
    INSERT INTO organization_members (organization_id, user_id, role)
    VALUES (new_org_id, NEW.id, 'admin');
  END IF;
  
  RETURN NEW;

EXCEPTION WHEN OTHERS THEN
  -- CRITICAL: If ANYTHING fails, log a warning but DO NOT block the user from signing up.
  RAISE WARNING 'Signup trigger failed for user %: %', NEW.email, SQLERRM;
  RETURN NEW; 
END;
$$;


ALTER FUNCTION "public"."handle_new_user"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."activity_categories" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "activity_type" "text" NOT NULL,
    "esrs_e1_category" "text" NOT NULL,
    "issb_category" "text" NOT NULL,
    "ghg_protocol_scope" "text" NOT NULL,
    "ghg_protocol_category" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."activity_categories" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."assets" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "facility_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" "text",
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE "public"."assets" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."beta_access_codes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "code" "text" NOT NULL,
    "email" "text",
    "status" "text" DEFAULT 'unused'::"text",
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "used_at" timestamp with time zone,
    "magic_token" "text",
    "token_created_at" timestamp with time zone
);


ALTER TABLE "public"."beta_access_codes" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."beta_users" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "email" "text" NOT NULL,
    "beta_code" "text",
    "access_level" "text" DEFAULT 'beta'::"text",
    "invited_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "last_active_at" timestamp with time zone,
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."beta_users" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."defra_conversion_factors" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "reporting_year" integer NOT NULL,
    "activity_type" character varying(150) NOT NULL,
    "co2e_multiplier" numeric(12,6) NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE "public"."defra_conversion_factors" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."email_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "email" "text" NOT NULL,
    "type" "text" NOT NULL,
    "status" "text" NOT NULL,
    "error_message" "text",
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."email_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."emissions_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "asset_id" "uuid",
    "defra_factor_id" "uuid",
    "start_date" "date" NOT NULL,
    "end_date" "date" NOT NULL,
    "raw_quantity" numeric(12,2) NOT NULL,
    "calculated_kg_co2e" numeric(15,4) NOT NULL,
    "created_by_user_id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    CONSTRAINT "check_dates" CHECK (("end_date" >= "start_date"))
);


ALTER TABLE "public"."emissions_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."facilities" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "postcode" character varying(20) NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE "public"."facilities" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."glossary" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "term" "text" NOT NULL,
    "definition" "text" NOT NULL,
    "category" "text",
    "related_terms" "text"[],
    "example" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "is_active" boolean DEFAULT true
);


ALTER TABLE "public"."glossary" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."manual_review_queue" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid",
    "file_url" "text" NOT NULL,
    "file_name" "text" NOT NULL,
    "file_type" "text" NOT NULL,
    "data_type" "text" NOT NULL,
    "status" "text" DEFAULT 'pending'::"text" NOT NULL,
    "auto_extraction_result" "jsonb",
    "manual_extraction_result" "jsonb",
    "assigned_to" "uuid",
    "priority" integer DEFAULT 0,
    "customer_notes" "text",
    "staff_notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "completed_at" timestamp with time zone,
    "estimated_completion_hours" integer DEFAULT 24,
    "batch_id" "uuid",
    "assigned_by" "uuid",
    "started_at" timestamp with time zone,
    "completed_by" "uuid",
    "data_entry" "jsonb",
    "review_time_seconds" integer,
    CONSTRAINT "manual_review_queue_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'assigned'::"text", 'in_progress'::"text", 'completed'::"text", 'rejected'::"text"])))
);


ALTER TABLE "public"."manual_review_queue" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."organization_members" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "role" character varying(20) NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "organization_members_role_check" CHECK ((("role")::"text" = ANY ((ARRAY['admin'::character varying, 'editor'::character varying, 'viewer'::character varying])::"text"[])))
);


ALTER TABLE "public"."organization_members" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."organizations" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" character varying(255) NOT NULL,
    "company_number" character varying(50),
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    "logo_url" "text",
    "industry" "text",
    "sector" "text",
    "company_size" "text",
    "vat_number" "text",
    "registration_number" "text",
    "registered_address" "text",
    "country" "text" DEFAULT 'UK'::"text",
    "timezone" "text" DEFAULT 'Europe/London'::"text",
    "currency" "text" DEFAULT 'GBP'::"text",
    "financial_year_end" "date",
    "reporting_standard" "text" DEFAULT 'SECR'::"text",
    "secr_enabled" boolean DEFAULT true,
    "esrs_enabled" boolean DEFAULT false,
    "issb_enabled" boolean DEFAULT false,
    "default_defra_version" integer DEFAULT 2024,
    "preferred_units" "text" DEFAULT 'metric'::"text",
    "website" "text",
    "primary_contact_email" "text",
    "primary_contact_name" "text",
    "billing_contact_email" "text",
    "billing_contact_name" "text",
    "subscription_status" "text" DEFAULT 'trial'::"text",
    "trial_start_date" timestamp with time zone,
    "trial_end_date" timestamp with time zone,
    "subscription_tier" "text" DEFAULT 'starter'::"text",
    "subscription_id" "text",
    "billing_address" "text",
    "tax_rate" numeric(5,2) DEFAULT 20.00,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb"
);


ALTER TABLE "public"."organizations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."pending_invites" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "email" character varying(255) NOT NULL,
    "role" character varying(20) NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "pending_invites_role_check" CHECK ((("role")::"text" = ANY ((ARRAY['admin'::character varying, 'editor'::character varying, 'viewer'::character varying])::"text"[])))
);


ALTER TABLE "public"."pending_invites" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."review_audit_trail" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "review_id" "uuid",
    "action" "text" NOT NULL,
    "performed_by" "uuid",
    "performed_by_email" "text",
    "assigned_to" "uuid",
    "old_value" "jsonb",
    "new_value" "jsonb",
    "note" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."review_audit_trail" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."roles" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" character varying(50) NOT NULL,
    "description" "text",
    "permissions" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."roles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."staff_profiles" (
    "id" "uuid" NOT NULL,
    "role" "text" DEFAULT 'data_extractor'::"text" NOT NULL,
    "extraction_count" integer DEFAULT 0,
    "accuracy_rate" numeric(5,2) DEFAULT 100.00,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "user_id" "uuid",
    "first_name" "text",
    "last_name" "text",
    "email" "text",
    "is_active" boolean DEFAULT true,
    "last_login" timestamp with time zone,
    "total_reviews_completed" integer DEFAULT 0,
    "avg_review_time_minutes" integer,
    "role_id" "uuid",
    "permissions" "jsonb" DEFAULT '{}'::"jsonb"
);


ALTER TABLE "public"."staff_profiles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."system_settings" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "settings_json" "jsonb",
    "max_file_size_mb" integer DEFAULT 50,
    "allowed_file_types" "text"[] DEFAULT ARRAY['pdf'::"text", 'csv'::"text", 'xlsx'::"text", 'jpg'::"text", 'jpeg'::"text", 'png'::"text"],
    "enable_auto_repair" boolean DEFAULT true,
    "max_batch_files" integer DEFAULT 20,
    "max_total_batch_size_mb" integer DEFAULT 200,
    "data_retention_days" integer DEFAULT 365,
    "require_2fa" boolean DEFAULT false,
    "session_timeout_minutes" integer DEFAULT 60,
    "max_login_attempts" integer DEFAULT 5,
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "updated_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."system_settings" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."upload_batches" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid",
    "batch_name" character varying(255),
    "total_files" integer DEFAULT 0,
    "processed_files" integer DEFAULT 0,
    "status" "text" DEFAULT 'uploading'::"text",
    "created_by_user_id" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "completed_at" timestamp with time zone,
    "metadata" "jsonb"
);


ALTER TABLE "public"."upload_batches" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_activity_log" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "action" character varying(100) NOT NULL,
    "details" "jsonb" DEFAULT '{}'::"jsonb",
    "ip_address" character varying(45),
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."user_activity_log" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_feedback" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid",
    "user_id" "uuid",
    "user_email" "text" NOT NULL,
    "type" "text" NOT NULL,
    "title" "text" NOT NULL,
    "description" "text" NOT NULL,
    "severity" "text",
    "status" "text" DEFAULT 'new'::"text",
    "rating" integer,
    "screenshot_url" "text",
    "browser_info" "text",
    "os_info" "text",
    "url" "text",
    "assigned_to" "uuid",
    "resolved_at" timestamp with time zone,
    "resolution_notes" "text",
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "user_feedback_rating_check" CHECK ((("rating" >= 1) AND ("rating" <= 5))),
    CONSTRAINT "user_feedback_severity_check" CHECK (("severity" = ANY (ARRAY['low'::"text", 'medium'::"text", 'high'::"text", 'critical'::"text"]))),
    CONSTRAINT "user_feedback_status_check" CHECK (("status" = ANY (ARRAY['new'::"text", 'reviewing'::"text", 'planned'::"text", 'in_progress'::"text", 'completed'::"text", 'declined'::"text"]))),
    CONSTRAINT "user_feedback_type_check" CHECK (("type" = ANY (ARRAY['bug'::"text", 'feature'::"text", 'general'::"text", 'rating'::"text"])))
);


ALTER TABLE "public"."user_feedback" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_invitations" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "email" character varying(255) NOT NULL,
    "role_id" "uuid",
    "organization_id" "uuid",
    "invited_by" "uuid",
    "token" character varying(255) NOT NULL,
    "status" character varying(20) DEFAULT 'pending'::character varying,
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."user_invitations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."waitlist" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "email" "text" NOT NULL,
    "full_name" "text",
    "company_name" "text",
    "company_size" "text",
    "interested_in" "text",
    "source" "text" DEFAULT 'landing_page'::"text",
    "status" "text" DEFAULT 'pending'::"text",
    "invited_at" timestamp with time zone,
    "activated_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."waitlist" OWNER TO "postgres";


ALTER TABLE ONLY "public"."activity_categories"
    ADD CONSTRAINT "activity_categories_activity_type_key" UNIQUE ("activity_type");



ALTER TABLE ONLY "public"."activity_categories"
    ADD CONSTRAINT "activity_categories_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."assets"
    ADD CONSTRAINT "assets_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."beta_access_codes"
    ADD CONSTRAINT "beta_access_codes_code_key" UNIQUE ("code");



ALTER TABLE ONLY "public"."beta_access_codes"
    ADD CONSTRAINT "beta_access_codes_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_email_unique" UNIQUE ("email");



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."defra_conversion_factors"
    ADD CONSTRAINT "defra_conversion_factors_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."defra_conversion_factors"
    ADD CONSTRAINT "defra_conversion_factors_reporting_year_activity_type_key" UNIQUE ("reporting_year", "activity_type");



ALTER TABLE ONLY "public"."email_logs"
    ADD CONSTRAINT "email_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."facilities"
    ADD CONSTRAINT "facilities_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."glossary"
    ADD CONSTRAINT "glossary_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."glossary"
    ADD CONSTRAINT "glossary_term_key" UNIQUE ("term");



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."organization_members"
    ADD CONSTRAINT "organization_members_organization_id_user_id_key" UNIQUE ("organization_id", "user_id");



ALTER TABLE ONLY "public"."organization_members"
    ADD CONSTRAINT "organization_members_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."organizations"
    ADD CONSTRAINT "organizations_company_number_key" UNIQUE ("company_number");



ALTER TABLE ONLY "public"."organizations"
    ADD CONSTRAINT "organizations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."pending_invites"
    ADD CONSTRAINT "pending_invites_organization_id_email_key" UNIQUE ("organization_id", "email");



ALTER TABLE ONLY "public"."pending_invites"
    ADD CONSTRAINT "pending_invites_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."review_audit_trail"
    ADD CONSTRAINT "review_audit_trail_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_name_key" UNIQUE ("name");



ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."staff_profiles"
    ADD CONSTRAINT "staff_profiles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."system_settings"
    ADD CONSTRAINT "system_settings_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."defra_conversion_factors"
    ADD CONSTRAINT "unique_year_activity" UNIQUE ("reporting_year", "activity_type");



ALTER TABLE ONLY "public"."upload_batches"
    ADD CONSTRAINT "upload_batches_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_activity_log"
    ADD CONSTRAINT "user_activity_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_feedback"
    ADD CONSTRAINT "user_feedback_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_invitations"
    ADD CONSTRAINT "user_invitations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_invitations"
    ADD CONSTRAINT "user_invitations_token_key" UNIQUE ("token");



ALTER TABLE ONLY "public"."waitlist"
    ADD CONSTRAINT "waitlist_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."waitlist"
    ADD CONSTRAINT "waitlist_pkey" PRIMARY KEY ("id");



CREATE INDEX "idx_beta_access_codes_magic_token" ON "public"."beta_access_codes" USING "btree" ("magic_token");



CREATE INDEX "idx_defra_lookup" ON "public"."defra_conversion_factors" USING "btree" ("reporting_year", "activity_type");



CREATE INDEX "idx_email_logs_email" ON "public"."email_logs" USING "btree" ("email");



CREATE INDEX "idx_email_logs_type" ON "public"."email_logs" USING "btree" ("type");



CREATE INDEX "idx_emissions_date_range" ON "public"."emissions_logs" USING "btree" ("start_date", "end_date");



CREATE INDEX "idx_emissions_metadata" ON "public"."emissions_logs" USING "gin" ("metadata");



CREATE INDEX "idx_emissions_org" ON "public"."emissions_logs" USING "btree" ("organization_id");



CREATE INDEX "idx_glossary_category" ON "public"."glossary" USING "btree" ("category");



CREATE INDEX "idx_glossary_is_active" ON "public"."glossary" USING "btree" ("is_active");



CREATE INDEX "idx_glossary_term" ON "public"."glossary" USING "btree" ("term");



CREATE INDEX "idx_manual_review_queue_batch" ON "public"."manual_review_queue" USING "btree" ("batch_id");



CREATE INDEX "idx_manual_review_queue_created" ON "public"."manual_review_queue" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_manual_review_queue_org" ON "public"."manual_review_queue" USING "btree" ("organization_id");



CREATE INDEX "idx_manual_review_queue_status" ON "public"."manual_review_queue" USING "btree" ("status");



CREATE INDEX "idx_members_org" ON "public"."organization_members" USING "btree" ("organization_id");



CREATE INDEX "idx_members_user" ON "public"."organization_members" USING "btree" ("user_id");



CREATE INDEX "idx_review_audit_trail_created_at" ON "public"."review_audit_trail" USING "btree" ("created_at");



CREATE INDEX "idx_review_audit_trail_performed_by" ON "public"."review_audit_trail" USING "btree" ("performed_by");



CREATE INDEX "idx_review_audit_trail_review_id" ON "public"."review_audit_trail" USING "btree" ("review_id");



CREATE INDEX "idx_upload_batches_org" ON "public"."upload_batches" USING "btree" ("organization_id");



CREATE INDEX "idx_upload_batches_status" ON "public"."upload_batches" USING "btree" ("status");



CREATE INDEX "idx_waitlist_email" ON "public"."waitlist" USING "btree" ("email");



CREATE INDEX "idx_waitlist_status" ON "public"."waitlist" USING "btree" ("status");



ALTER TABLE ONLY "public"."assets"
    ADD CONSTRAINT "assets_facility_id_fkey" FOREIGN KEY ("facility_id") REFERENCES "public"."facilities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_beta_code_fkey" FOREIGN KEY ("beta_code") REFERENCES "public"."beta_access_codes"("code");



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_invited_by_fkey" FOREIGN KEY ("invited_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_asset_id_fkey" FOREIGN KEY ("asset_id") REFERENCES "public"."assets"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_created_by_user_id_fkey" FOREIGN KEY ("created_by_user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_defra_factor_id_fkey" FOREIGN KEY ("defra_factor_id") REFERENCES "public"."defra_conversion_factors"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."facilities"
    ADD CONSTRAINT "facilities_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_assigned_by_fkey" FOREIGN KEY ("assigned_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_assigned_to_fkey" FOREIGN KEY ("assigned_to") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_batch_id_fkey" FOREIGN KEY ("batch_id") REFERENCES "public"."upload_batches"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_completed_by_fkey" FOREIGN KEY ("completed_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."organization_members"
    ADD CONSTRAINT "organization_members_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."organization_members"
    ADD CONSTRAINT "organization_members_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."pending_invites"
    ADD CONSTRAINT "pending_invites_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."review_audit_trail"
    ADD CONSTRAINT "review_audit_trail_assigned_to_fkey" FOREIGN KEY ("assigned_to") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."review_audit_trail"
    ADD CONSTRAINT "review_audit_trail_performed_by_fkey" FOREIGN KEY ("performed_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."review_audit_trail"
    ADD CONSTRAINT "review_audit_trail_review_id_fkey" FOREIGN KEY ("review_id") REFERENCES "public"."manual_review_queue"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."staff_profiles"
    ADD CONSTRAINT "staff_profiles_id_fkey" FOREIGN KEY ("id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."staff_profiles"
    ADD CONSTRAINT "staff_profiles_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");



ALTER TABLE ONLY "public"."system_settings"
    ADD CONSTRAINT "system_settings_updated_by_fkey" FOREIGN KEY ("updated_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."upload_batches"
    ADD CONSTRAINT "upload_batches_created_by_user_id_fkey" FOREIGN KEY ("created_by_user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."upload_batches"
    ADD CONSTRAINT "upload_batches_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_activity_log"
    ADD CONSTRAINT "user_activity_log_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."user_feedback"
    ADD CONSTRAINT "user_feedback_assigned_to_fkey" FOREIGN KEY ("assigned_to") REFERENCES "public"."staff_profiles"("id");



ALTER TABLE ONLY "public"."user_feedback"
    ADD CONSTRAINT "user_feedback_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_feedback"
    ADD CONSTRAINT "user_feedback_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."user_invitations"
    ADD CONSTRAINT "user_invitations_invited_by_fkey" FOREIGN KEY ("invited_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."user_invitations"
    ADD CONSTRAINT "user_invitations_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."user_invitations"
    ADD CONSTRAINT "user_invitations_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");



CREATE POLICY "Admins can delete invites for their org" ON "public"."pending_invites" FOR DELETE USING (("organization_id" IN ( SELECT "organization_members"."organization_id"
   FROM "public"."organization_members"
  WHERE (("organization_members"."user_id" = "auth"."uid"()) AND (("organization_members"."role")::"text" = 'admin'::"text")))));



CREATE POLICY "Admins can insert invites for their org" ON "public"."pending_invites" FOR INSERT WITH CHECK (("organization_id" IN ( SELECT "organization_members"."organization_id"
   FROM "public"."organization_members"
  WHERE (("organization_members"."user_id" = "auth"."uid"()) AND (("organization_members"."role")::"text" = 'admin'::"text")))));



CREATE POLICY "Admins can view invites for their org" ON "public"."pending_invites" FOR SELECT USING (("organization_id" IN ( SELECT "organization_members"."organization_id"
   FROM "public"."organization_members"
  WHERE (("organization_members"."user_id" = "auth"."uid"()) AND (("organization_members"."role")::"text" = 'admin'::"text")))));



CREATE POLICY "Allow admin full access to roles" ON "public"."roles" TO "authenticated" USING (("auth"."uid"() IN ( SELECT "staff_profiles"."user_id"
   FROM "public"."staff_profiles"
  WHERE ("staff_profiles"."role_id" IN ( SELECT "roles_1"."id"
           FROM "public"."roles" "roles_1"
          WHERE (("roles_1"."name")::"text" = 'admin'::"text"))))));



CREATE POLICY "Allow admin to manage invitations" ON "public"."user_invitations" TO "authenticated" USING (("auth"."uid"() IN ( SELECT "staff_profiles"."user_id"
   FROM "public"."staff_profiles"
  WHERE ("staff_profiles"."role_id" IN ( SELECT "roles"."id"
           FROM "public"."roles"
          WHERE (("roles"."name")::"text" = 'admin'::"text"))))));



CREATE POLICY "Allow authenticated users to update queue items" ON "public"."manual_review_queue" FOR UPDATE USING (("auth"."role"() = 'authenticated'::"text")) WITH CHECK (("auth"."role"() = 'authenticated'::"text"));



CREATE POLICY "Allow authenticated users to view pending queue items" ON "public"."manual_review_queue" FOR SELECT USING (("auth"."role"() = 'authenticated'::"text"));



CREATE POLICY "Allow batch inserts" ON "public"."upload_batches" FOR INSERT WITH CHECK (true);



CREATE POLICY "Allow batch updates" ON "public"."upload_batches" FOR UPDATE USING (true) WITH CHECK (true);



CREATE POLICY "Allow insert access to admin users only" ON "public"."system_settings" FOR INSERT TO "authenticated" WITH CHECK (("auth"."uid"() IN ( SELECT "staff_profiles"."user_id"
   FROM "public"."staff_profiles"
  WHERE ("staff_profiles"."role" = 'admin'::"text"))));



CREATE POLICY "Allow read access to authenticated users" ON "public"."system_settings" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "Allow read roles for authenticated users" ON "public"."roles" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "Allow update access to admin users only" ON "public"."system_settings" FOR UPDATE TO "authenticated" USING (("auth"."uid"() IN ( SELECT "staff_profiles"."user_id"
   FROM "public"."staff_profiles"
  WHERE ("staff_profiles"."role" = 'admin'::"text"))));



CREATE POLICY "Anyone can read glossary" ON "public"."glossary" FOR SELECT USING (true);



CREATE POLICY "Enable all for authenticated users with admin role" ON "public"."beta_access_codes" USING (("auth"."role"() = 'authenticated'::"text"));



CREATE POLICY "Enable all for authenticated users with admin role" ON "public"."beta_users" USING (("auth"."role"() = 'authenticated'::"text"));



CREATE POLICY "Enable read access for authenticated users" ON "public"."assets" FOR SELECT USING (("auth"."role"() = 'authenticated'::"text"));



CREATE POLICY "Enable read access for authenticated users" ON "public"."facilities" FOR SELECT USING (("auth"."role"() = 'authenticated'::"text"));



CREATE POLICY "Everyone can read DEFRA factors" ON "public"."defra_conversion_factors" FOR SELECT USING (true);



CREATE POLICY "Only admins can modify glossary" ON "public"."glossary" USING (("auth"."role"() = 'authenticated'::"text"));



CREATE POLICY "Org members can manage assets" ON "public"."assets" USING (("facility_id" IN ( SELECT "facilities"."id"
   FROM "public"."facilities"
  WHERE ("facilities"."organization_id" IN ( SELECT "organization_members"."organization_id"
           FROM "public"."organization_members"
          WHERE ("organization_members"."user_id" = "auth"."uid"()))))));



CREATE POLICY "Org members can manage facilities" ON "public"."facilities" USING (("organization_id" IN ( SELECT "organization_members"."organization_id"
   FROM "public"."organization_members"
  WHERE ("organization_members"."user_id" = "auth"."uid"()))));



CREATE POLICY "Organizations can view their own batches" ON "public"."upload_batches" FOR SELECT USING (("organization_id" IN ( SELECT "organization_members"."organization_id"
   FROM "public"."organization_members"
  WHERE ("organization_members"."user_id" = "auth"."uid"()))));



CREATE POLICY "Staff can insert queue items" ON "public"."manual_review_queue" FOR INSERT WITH CHECK (true);



CREATE POLICY "Staff can update queue items" ON "public"."manual_review_queue" FOR UPDATE USING (true) WITH CHECK (true);



CREATE POLICY "Staff can view their own profile" ON "public"."staff_profiles" FOR SELECT USING (("id" = "auth"."uid"()));



CREATE POLICY "Users can view their own membership" ON "public"."organization_members" FOR SELECT USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can view their own organization" ON "public"."organizations" FOR SELECT USING (("id" IN ( SELECT "organization_members"."organization_id"
   FROM "public"."organization_members"
  WHERE ("organization_members"."user_id" = "auth"."uid"()))));



CREATE POLICY "Users can view their own organization's assets" ON "public"."assets" USING (("facility_id" IN ( SELECT "facilities"."id"
   FROM "public"."facilities"
  WHERE ("facilities"."organization_id" IN ( SELECT "organization_members"."organization_id"
           FROM "public"."organization_members"
          WHERE ("organization_members"."user_id" = "auth"."uid"()))))));



CREATE POLICY "Users can view their own organization's emissions" ON "public"."emissions_logs" USING (("organization_id" IN ( SELECT "organization_members"."organization_id"
   FROM "public"."organization_members"
  WHERE ("organization_members"."user_id" = "auth"."uid"()))));



CREATE POLICY "Users can view their own organization's facilities" ON "public"."facilities" USING (("organization_id" IN ( SELECT "organization_members"."organization_id"
   FROM "public"."organization_members"
  WHERE ("organization_members"."user_id" = "auth"."uid"()))));



ALTER TABLE "public"."assets" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."beta_access_codes" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."beta_users" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."defra_conversion_factors" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."emissions_logs" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."facilities" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."glossary" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."manual_review_queue" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."organization_members" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."organizations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."pending_invites" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."roles" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."staff_profiles" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."system_settings" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."upload_batches" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_activity_log" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_invitations" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";






















































































































































GRANT ALL ON FUNCTION "public"."get_admin_customer_overview"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_admin_customer_overview"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_admin_customer_overview"() TO "service_role";



GRANT ALL ON FUNCTION "public"."get_admin_dashboard_stats"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_admin_dashboard_stats"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_admin_dashboard_stats"() TO "service_role";



GRANT ALL ON FUNCTION "public"."get_platform_users"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_platform_users"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_platform_users"() TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "service_role";


















GRANT ALL ON TABLE "public"."activity_categories" TO "anon";
GRANT ALL ON TABLE "public"."activity_categories" TO "authenticated";
GRANT ALL ON TABLE "public"."activity_categories" TO "service_role";



GRANT ALL ON TABLE "public"."assets" TO "anon";
GRANT ALL ON TABLE "public"."assets" TO "authenticated";
GRANT ALL ON TABLE "public"."assets" TO "service_role";



GRANT ALL ON TABLE "public"."beta_access_codes" TO "anon";
GRANT ALL ON TABLE "public"."beta_access_codes" TO "authenticated";
GRANT ALL ON TABLE "public"."beta_access_codes" TO "service_role";



GRANT ALL ON TABLE "public"."beta_users" TO "anon";
GRANT ALL ON TABLE "public"."beta_users" TO "authenticated";
GRANT ALL ON TABLE "public"."beta_users" TO "service_role";



GRANT ALL ON TABLE "public"."defra_conversion_factors" TO "anon";
GRANT ALL ON TABLE "public"."defra_conversion_factors" TO "authenticated";
GRANT ALL ON TABLE "public"."defra_conversion_factors" TO "service_role";



GRANT ALL ON TABLE "public"."email_logs" TO "anon";
GRANT ALL ON TABLE "public"."email_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."email_logs" TO "service_role";



GRANT ALL ON TABLE "public"."emissions_logs" TO "anon";
GRANT ALL ON TABLE "public"."emissions_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."emissions_logs" TO "service_role";



GRANT ALL ON TABLE "public"."facilities" TO "anon";
GRANT ALL ON TABLE "public"."facilities" TO "authenticated";
GRANT ALL ON TABLE "public"."facilities" TO "service_role";



GRANT ALL ON TABLE "public"."glossary" TO "anon";
GRANT ALL ON TABLE "public"."glossary" TO "authenticated";
GRANT ALL ON TABLE "public"."glossary" TO "service_role";



GRANT ALL ON TABLE "public"."manual_review_queue" TO "anon";
GRANT ALL ON TABLE "public"."manual_review_queue" TO "authenticated";
GRANT ALL ON TABLE "public"."manual_review_queue" TO "service_role";



GRANT ALL ON TABLE "public"."organization_members" TO "anon";
GRANT ALL ON TABLE "public"."organization_members" TO "authenticated";
GRANT ALL ON TABLE "public"."organization_members" TO "service_role";



GRANT ALL ON TABLE "public"."organizations" TO "anon";
GRANT ALL ON TABLE "public"."organizations" TO "authenticated";
GRANT ALL ON TABLE "public"."organizations" TO "service_role";



GRANT ALL ON TABLE "public"."pending_invites" TO "anon";
GRANT ALL ON TABLE "public"."pending_invites" TO "authenticated";
GRANT ALL ON TABLE "public"."pending_invites" TO "service_role";



GRANT ALL ON TABLE "public"."review_audit_trail" TO "anon";
GRANT ALL ON TABLE "public"."review_audit_trail" TO "authenticated";
GRANT ALL ON TABLE "public"."review_audit_trail" TO "service_role";



GRANT ALL ON TABLE "public"."roles" TO "anon";
GRANT ALL ON TABLE "public"."roles" TO "authenticated";
GRANT ALL ON TABLE "public"."roles" TO "service_role";



GRANT ALL ON TABLE "public"."staff_profiles" TO "anon";
GRANT ALL ON TABLE "public"."staff_profiles" TO "authenticated";
GRANT ALL ON TABLE "public"."staff_profiles" TO "service_role";



GRANT ALL ON TABLE "public"."system_settings" TO "anon";
GRANT ALL ON TABLE "public"."system_settings" TO "authenticated";
GRANT ALL ON TABLE "public"."system_settings" TO "service_role";



GRANT ALL ON TABLE "public"."upload_batches" TO "anon";
GRANT ALL ON TABLE "public"."upload_batches" TO "authenticated";
GRANT ALL ON TABLE "public"."upload_batches" TO "service_role";



GRANT ALL ON TABLE "public"."user_activity_log" TO "anon";
GRANT ALL ON TABLE "public"."user_activity_log" TO "authenticated";
GRANT ALL ON TABLE "public"."user_activity_log" TO "service_role";



GRANT ALL ON TABLE "public"."user_feedback" TO "anon";
GRANT ALL ON TABLE "public"."user_feedback" TO "authenticated";
GRANT ALL ON TABLE "public"."user_feedback" TO "service_role";



GRANT ALL ON TABLE "public"."user_invitations" TO "anon";
GRANT ALL ON TABLE "public"."user_invitations" TO "authenticated";
GRANT ALL ON TABLE "public"."user_invitations" TO "service_role";



GRANT ALL ON TABLE "public"."waitlist" TO "anon";
GRANT ALL ON TABLE "public"."waitlist" TO "authenticated";
GRANT ALL ON TABLE "public"."waitlist" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";































