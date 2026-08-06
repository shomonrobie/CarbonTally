


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


CREATE SCHEMA IF NOT EXISTS "public";


ALTER SCHEMA "public" OWNER TO "pg_database_owner";


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE TYPE "public"."document_status" AS ENUM (
    'uploaded',
    'processing',
    'staff_review',
    'ready_for_review',
    'approved',
    'rejected'
);


ALTER TYPE "public"."document_status" OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."delete_old_audit_logs"() RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    DELETE FROM audit_logs 
    WHERE created_at < NOW() - INTERVAL '90 days';
    
    DELETE FROM message_activity_log 
    WHERE created_at < NOW() - INTERVAL '90 days';
    
    DELETE FROM notification_delivery_log 
    WHERE created_at < NOW() - INTERVAL '90 days';
    
    DELETE FROM verification_activity_log 
    WHERE created_at < NOW() - INTERVAL '90 days';
END;
$$;


ALTER FUNCTION "public"."delete_old_audit_logs"() OWNER TO "postgres";


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


CREATE OR REPLACE FUNCTION "public"."get_document_status_counts"("org_id" "uuid") RETURNS TABLE("status" character varying, "count" bigint)
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(status, 'unknown'),
        COUNT(*)
    FROM organization_files
    WHERE organization_id = org_id
    AND is_active = true
    GROUP BY status;
END;
$$;


ALTER FUNCTION "public"."get_document_status_counts"("org_id" "uuid") OWNER TO "postgres";


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


CREATE OR REPLACE FUNCTION "public"."log_document_status_change"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO document_activity_log (file_id, organization_id, action, details)
        VALUES (
            NEW.id,
            NEW.organization_id,
            'status_change',
            jsonb_build_object(
                'from_status', OLD.status,
                'to_status', NEW.status,
                'timestamp', NOW()
            )
        );
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."log_document_status_change"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."activity_categories" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "activity_type" "text" NOT NULL,
    "esrs_e1_category" "text" NOT NULL,
    "issb_category" "text" NOT NULL,
    "ghg_protocol_scope" "text" NOT NULL,
    "ghg_protocol_category" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."activity_categories" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."activity_feed" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid",
    "user_id" "uuid",
    "event_type" "text",
    "event_data" "jsonb",
    "is_read" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "now"()
);

ALTER TABLE ONLY "public"."activity_feed" REPLICA IDENTITY FULL;


ALTER TABLE "public"."activity_feed" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."activity_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "organization_id" "uuid",
    "action" character varying(100) NOT NULL,
    "resource_type" character varying(50) NOT NULL,
    "resource_id" "uuid",
    "details" "jsonb" DEFAULT '{}'::"jsonb",
    "ip_address" character varying(45),
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "updated_at" timestamp with time zone DEFAULT "now"()
);

ALTER TABLE ONLY "public"."activity_logs" REPLICA IDENTITY FULL;


ALTER TABLE "public"."activity_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."audit_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "staff_id" "uuid",
    "organization_member_id" "uuid",
    "organization_id" "uuid",
    "action_type" "text" NOT NULL,
    "resource_type" "text",
    "resource_id" "uuid",
    "action" "text" NOT NULL,
    "description" "text",
    "ip_address" "text",
    "user_agent" "text",
    "old_data" "jsonb",
    "new_data" "jsonb",
    "changes" "jsonb",
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "audit_logs_action_type_check" CHECK (("action_type" = ANY (ARRAY['document_uploaded'::"text", 'document_viewed'::"text", 'document_downloaded'::"text", 'document_updated'::"text", 'document_deleted'::"text", 'document_archived'::"text", 'document_restored'::"text", 'extraction_started'::"text", 'extraction_completed'::"text", 'extraction_approved'::"text", 'extraction_rejected'::"text", 'extraction_assigned'::"text", 'extraction_reassigned'::"text", 'review_assigned'::"text", 'review_started'::"text", 'review_completed'::"text", 'review_rejected'::"text", 'review_escalated'::"text", 'review_reassigned'::"text", 'verification_submitted'::"text", 'verification_approved'::"text", 'verification_rejected'::"text", 'verification_needs_revision'::"text", 'message_sent'::"text", 'message_read'::"text", 'conversation_created'::"text", 'conversation_closed'::"text", 'conversation_archived'::"text", 'notification_sent'::"text", 'notification_read'::"text", 'notification_dismissed'::"text", 'user_logged_in'::"text", 'user_logged_out'::"text", 'user_created'::"text", 'user_updated'::"text", 'user_deleted'::"text", 'password_changed'::"text", 'password_reset_requested'::"text", 'organization_created'::"text", 'organization_updated'::"text", 'organization_member_added'::"text", 'organization_member_removed'::"text", 'organization_member_role_changed'::"text", 'system_health_check'::"text", 'system_error'::"text", 'system_warning'::"text"]))),
    CONSTRAINT "audit_logs_resource_type_check" CHECK (("resource_type" = ANY (ARRAY['document'::"text", 'extraction'::"text", 'review'::"text", 'verification'::"text", 'message'::"text", 'conversation'::"text", 'notification'::"text", 'organization'::"text", 'member'::"text", 'staff'::"text", 'system'::"text"])))
);


ALTER TABLE "public"."audit_logs" OWNER TO "postgres";


CREATE OR REPLACE VIEW "public"."activity_summary" AS
 SELECT "organization_id",
    "date_trunc"('day'::"text", "created_at") AS "activity_date",
    "action_type",
    "count"(*) AS "total_actions",
    "count"(DISTINCT "user_id") AS "unique_users",
    "count"(DISTINCT "resource_id") AS "unique_resources"
   FROM "public"."audit_logs"
  WHERE ("created_at" > ("now"() - '30 days'::interval))
  GROUP BY "organization_id", ("date_trunc"('day'::"text", "created_at")), "action_type"
  ORDER BY ("date_trunc"('day'::"text", "created_at")) DESC;


ALTER VIEW "public"."activity_summary" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."assets" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "facility_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" "text",
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    "is_active" boolean DEFAULT true,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "capacity" numeric(15,4),
    "capacity_unit" character varying(50),
    "serial_number" character varying(100),
    "installation_date" "date",
    "type" character varying(100),
    "updated_at" timestamp with time zone DEFAULT "now"()
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
    "token_created_at" timestamp with time zone,
    "updated_at" timestamp with time zone DEFAULT "now"()
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


CREATE TABLE IF NOT EXISTS "public"."conversation_activity_log" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "conversation_id" "uuid",
    "user_id" "uuid",
    "action_type" "text",
    "action_details" "jsonb",
    "ip_address" "text",
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "conversation_activity_log_action_type_check" CHECK (("action_type" = ANY (ARRAY['created'::"text", 'closed'::"text", 'archived'::"text", 'reopened'::"text", 'priority_changed'::"text"])))
);

ALTER TABLE ONLY "public"."conversation_activity_log" REPLICA IDENTITY FULL;


ALTER TABLE "public"."conversation_activity_log" OWNER TO "postgres";


CREATE OR REPLACE VIEW "public"."conversation_details" AS
SELECT
    NULL::"uuid" AS "id",
    NULL::"uuid" AS "organization_id",
    NULL::"uuid" AS "staff_id",
    NULL::"uuid" AS "customer_id",
    NULL::"text" AS "subject",
    NULL::"text" AS "status",
    NULL::timestamp with time zone AS "last_message_at",
    NULL::"uuid" AS "created_by",
    NULL::"uuid" AS "closed_by",
    NULL::timestamp with time zone AS "closed_at",
    NULL::boolean AS "is_urgent",
    NULL::"text" AS "priority",
    NULL::timestamp with time zone AS "created_at",
    NULL::timestamp with time zone AS "updated_at",
    NULL::"uuid"[] AS "read_by",
    NULL::integer AS "unread_count",
    NULL::integer AS "participant_count",
    NULL::bigint AS "total_participants",
    NULL::json AS "participants";


ALTER VIEW "public"."conversation_details" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."conversation_participants" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "conversation_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "joined_at" timestamp with time zone DEFAULT "now"(),
    "last_read_at" timestamp with time zone DEFAULT "now"(),
    "is_active" boolean DEFAULT true,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);

ALTER TABLE ONLY "public"."conversation_participants" REPLICA IDENTITY FULL;


ALTER TABLE "public"."conversation_participants" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."conversations" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid",
    "staff_id" "uuid",
    "customer_id" "uuid",
    "subject" "text",
    "status" "text" DEFAULT 'open'::"text",
    "last_message_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "closed_by" "uuid",
    "closed_at" timestamp with time zone,
    "is_urgent" boolean DEFAULT false,
    "priority" "text" DEFAULT 'normal'::"text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "read_by" "uuid"[] DEFAULT '{}'::"uuid"[],
    "unread_count" integer DEFAULT 0,
    "participant_count" integer DEFAULT 0,
    CONSTRAINT "conversations_priority_check" CHECK (("priority" = ANY (ARRAY['low'::"text", 'normal'::"text", 'high'::"text", 'urgent'::"text"]))),
    CONSTRAINT "conversations_status_check" CHECK (("status" = ANY (ARRAY['open'::"text", 'closed'::"text", 'archived'::"text"])))
);

ALTER TABLE ONLY "public"."conversations" REPLICA IDENTITY FULL;


ALTER TABLE "public"."conversations" OWNER TO "postgres";


CREATE OR REPLACE VIEW "public"."customer_activity_summary" AS
 SELECT "organization_member_id",
    "date_trunc"('day'::"text", "created_at") AS "activity_date",
    "action_type",
    "count"(*) AS "total_actions"
   FROM "public"."audit_logs"
  WHERE (("organization_member_id" IS NOT NULL) AND ("created_at" > ("now"() - '30 days'::interval)))
  GROUP BY "organization_member_id", ("date_trunc"('day'::"text", "created_at")), "action_type"
  ORDER BY ("date_trunc"('day'::"text", "created_at")) DESC;


ALTER VIEW "public"."customer_activity_summary" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."customer_documents" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "organization_member_id" "uuid" NOT NULL,
    "asset_id" "uuid" NOT NULL,
    "file_name" "text" NOT NULL,
    "file_url" "text" NOT NULL,
    "file_type" "text" NOT NULL,
    "upload_date" timestamp with time zone DEFAULT "now"(),
    "status" "text" DEFAULT 'pending'::"text",
    "manual_review_queue_id" "uuid",
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "document_type_id" "uuid",
    "document_type_code" "text",
    "organization_classification" "text",
    "classification_by" "uuid",
    "classification_at" timestamp with time zone,
    "confidence_score" double precision,
    "organization_notes" "text",
    "billing_period_start" "date",
    "billing_period_end" "date",
    CONSTRAINT "customer_documents_file_type_check" CHECK (("file_type" = ANY (ARRAY['invoice'::"text", 'fuel_slip'::"text", 'maintenance'::"text", 'other'::"text"]))),
    CONSTRAINT "customer_documents_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'processing'::"text", 'extracted'::"text", 'approved'::"text", 'rejected'::"text"])))
);

ALTER TABLE ONLY "public"."customer_documents" REPLICA IDENTITY FULL;


ALTER TABLE "public"."customer_documents" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."customer_review_log" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "file_id" "uuid",
    "organization_id" "uuid",
    "user_id" "uuid",
    "status" character varying(50) NOT NULL,
    "notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);

ALTER TABLE ONLY "public"."customer_review_log" REPLICA IDENTITY FULL;


ALTER TABLE "public"."customer_review_log" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."customer_verifications" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "customer_document_id" "uuid",
    "organization_id" "uuid",
    "customer_member_id" "uuid",
    "status" "text",
    "notes" "text",
    "submitted_at" timestamp with time zone DEFAULT "now"(),
    "submitted_by" "uuid",
    "verified_at" timestamp with time zone,
    "verified_by" "uuid",
    "rejected_at" timestamp with time zone,
    "rejected_by" "uuid",
    "rejected_reason" "text",
    "revision_requested_at" timestamp with time zone,
    "revision_requested_by" "uuid",
    "revision_notes" "text",
    "is_escalated" boolean DEFAULT false,
    "escalation_reason" "text",
    "escalated_at" timestamp with time zone,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "customer_verifications_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'verified'::"text", 'rejected'::"text", 'needs_revision'::"text"])))
);

ALTER TABLE ONLY "public"."customer_verifications" REPLICA IDENTITY FULL;


ALTER TABLE "public"."customer_verifications" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."defra_conversion_factors" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "reporting_year" integer NOT NULL,
    "activity_type" character varying(150) NOT NULL,
    "co2e_multiplier" numeric(12,6) NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."defra_conversion_factors" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."document_activity_log" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "file_id" "uuid",
    "organization_id" "uuid",
    "user_id" "uuid",
    "action" character varying(50) NOT NULL,
    "details" "jsonb" DEFAULT '{}'::"jsonb",
    "ip_address" character varying(45),
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."document_activity_log" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."document_types" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "code" "text" NOT NULL,
    "name" "text" NOT NULL,
    "category" "text" NOT NULL,
    "description" "text",
    "file_extensions" "text"[] DEFAULT '{}'::"text"[],
    "is_active" boolean DEFAULT true,
    "requires_asset" boolean DEFAULT false,
    "requires_date_range" boolean DEFAULT false,
    "requires_facility" boolean DEFAULT false,
    "priority" integer DEFAULT 0,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "document_types_category_check" CHECK (("category" = ANY (ARRAY['invoice'::"text", 'receipt'::"text", 'log'::"text", 'export'::"text", 'spreadsheet'::"text", 'other'::"text"])))
);


ALTER TABLE "public"."document_types" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."draft_entries" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "file_id" "uuid",
    "organization_id" "uuid",
    "user_id" "uuid",
    "data" "jsonb" DEFAULT '{}'::"jsonb",
    "progress" integer DEFAULT 0,
    "sections_completed" "jsonb" DEFAULT '[]'::"jsonb",
    "last_updated" timestamp with time zone DEFAULT "now"(),
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."draft_entries" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."email_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "email" "text" NOT NULL,
    "type" "text" NOT NULL,
    "status" "text" NOT NULL,
    "error_message" "text",
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."email_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."email_templates" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" character varying(255) NOT NULL,
    "subject" character varying(500) NOT NULL,
    "body" "text" NOT NULL,
    "type" character varying(50) NOT NULL,
    "variables" "text"[] DEFAULT '{}'::"text"[],
    "is_active" boolean DEFAULT true,
    "description" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_by" "uuid"
);


ALTER TABLE "public"."email_templates" OWNER TO "postgres";


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
    "file_id" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "customer_document_id" "uuid",
    CONSTRAINT "check_dates" CHECK (("end_date" >= "start_date"))
);


ALTER TABLE "public"."emissions_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."export_history" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid",
    "user_id" "uuid",
    "file_name" character varying(255),
    "format" character varying(50),
    "filters" "jsonb" DEFAULT '{}'::"jsonb",
    "record_count" integer,
    "status" character varying(50) DEFAULT 'pending'::character varying,
    "file_url" "text",
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."export_history" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."facilities" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "postcode" character varying(20) NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    "is_active" boolean DEFAULT true,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "latitude" numeric(10,8),
    "longitude" numeric(11,8),
    "type" character varying(100),
    "address_line1" character varying(255),
    "address_line2" character varying(255),
    "city" character varying(100),
    "county" character varying(100),
    "country" character varying(100) DEFAULT 'United Kingdom'::character varying,
    "region" character varying(100),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."facilities" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."file_attachments" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "message_id" "uuid",
    "conversation_id" "uuid",
    "organization_id" "uuid",
    "file_name" "text" NOT NULL,
    "file_url" "text" NOT NULL,
    "file_size" integer,
    "file_type" "text",
    "mime_type" "text",
    "uploaded_by" "uuid",
    "uploaded_at" timestamp with time zone DEFAULT "now"(),
    "created_at" timestamp with time zone DEFAULT "now"()
);

ALTER TABLE ONLY "public"."file_attachments" REPLICA IDENTITY FULL;


ALTER TABLE "public"."file_attachments" OWNER TO "postgres";


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


CREATE OR REPLACE VIEW "public"."live_dashboard" AS
 SELECT "organization_id",
    "count"(*) FILTER (WHERE ("status" = 'pending'::"text")) AS "pending_count",
    "count"(*) FILTER (WHERE ("status" = 'processing'::"text")) AS "processing_count",
    "count"(*) FILTER (WHERE ("status" = 'extracted'::"text")) AS "extracted_count",
    "count"(*) FILTER (WHERE ("status" = 'organized'::"text")) AS "organized_count",
    "count"(*) FILTER (WHERE ("status" = 'approved'::"text")) AS "approved_count",
    "count"(*) FILTER (WHERE ("status" = 'rejected'::"text")) AS "rejected_count",
    "max"("updated_at") AS "last_activity"
   FROM "public"."customer_documents"
  GROUP BY "organization_id";


ALTER VIEW "public"."live_dashboard" OWNER TO "postgres";


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
    "priority_score" integer DEFAULT 0,
    "sla_deadline" timestamp with time zone,
    "sla_breached" boolean DEFAULT false,
    "escalation_level" integer DEFAULT 0,
    "customer_notified_at" timestamp with time zone,
    "customer_responded_at" timestamp with time zone,
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "customer_document_id" "uuid",
    CONSTRAINT "manual_review_queue_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'assigned'::"text", 'in_progress'::"text", 'completed'::"text", 'rejected'::"text"])))
);

ALTER TABLE ONLY "public"."manual_review_queue" REPLICA IDENTITY FULL;


ALTER TABLE "public"."manual_review_queue" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."message_activity_log" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "message_id" "uuid",
    "conversation_id" "uuid",
    "user_id" "uuid",
    "action_type" "text",
    "action_details" "jsonb",
    "ip_address" "text",
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "message_activity_log_action_type_check" CHECK (("action_type" = ANY (ARRAY['sent'::"text", 'read'::"text", 'deleted'::"text", 'archived'::"text", 'delivered'::"text"])))
);

ALTER TABLE ONLY "public"."message_activity_log" REPLICA IDENTITY FULL;


ALTER TABLE "public"."message_activity_log" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."messages" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "conversation_id" "uuid",
    "sender_id" "uuid",
    "receiver_id" "uuid",
    "organization_id" "uuid",
    "subject" "text",
    "content" "text" NOT NULL,
    "is_read" boolean DEFAULT false,
    "parent_message_id" "uuid",
    "sent_at" timestamp with time zone DEFAULT "now"(),
    "delivered_at" timestamp with time zone,
    "read_at" timestamp with time zone,
    "is_deleted" boolean DEFAULT false,
    "deleted_at" timestamp with time zone,
    "is_archived" boolean DEFAULT false,
    "archived_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "read_by" "uuid"[] DEFAULT '{}'::"uuid"[],
    "read_count" integer DEFAULT 0,
    "last_read_at" timestamp with time zone,
    "attachments" "jsonb" DEFAULT '[]'::"jsonb",
    "has_attachments" boolean DEFAULT false
);

ALTER TABLE ONLY "public"."messages" REPLICA IDENTITY FULL;


ALTER TABLE "public"."messages" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."notification_delivery_log" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "notification_id" "uuid",
    "user_id" "uuid",
    "channel" "text",
    "status" "text",
    "error_message" "text",
    "sent_at" timestamp with time zone,
    "delivered_at" timestamp with time zone,
    "opened_at" timestamp with time zone,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "notification_delivery_log_channel_check" CHECK (("channel" = ANY (ARRAY['in-app'::"text", 'email'::"text", 'push'::"text"]))),
    CONSTRAINT "notification_delivery_log_status_check" CHECK (("status" = ANY (ARRAY['queued'::"text", 'sent'::"text", 'delivered'::"text", 'failed'::"text", 'opened'::"text"])))
);


ALTER TABLE "public"."notification_delivery_log" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."notifications" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "organization_id" "uuid",
    "type" "text" NOT NULL,
    "title" "text" NOT NULL,
    "message" "text" NOT NULL,
    "link" "text",
    "is_read" boolean DEFAULT false,
    "read_at" timestamp with time zone,
    "priority" "text" DEFAULT 'normal'::"text",
    "sent_via" "text"[] DEFAULT ARRAY['in-app'::"text"],
    "email_sent" boolean DEFAULT false,
    "email_sent_at" timestamp with time zone,
    "push_sent" boolean DEFAULT false,
    "push_sent_at" timestamp with time zone,
    "is_dismissed" boolean DEFAULT false,
    "dismissed_at" timestamp with time zone,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "notifications_priority_check" CHECK (("priority" = ANY (ARRAY['low'::"text", 'normal'::"text", 'high'::"text", 'urgent'::"text"]))),
    CONSTRAINT "notifications_type_check" CHECK (("type" = ANY (ARRAY['document_uploaded'::"text", 'document_extracted'::"text", 'document_approved'::"text", 'document_rejected'::"text", 'review_assigned'::"text", 'review_completed'::"text", 'sla_breach'::"text", 'customer_feedback'::"text", 'system_alert'::"text", 'message_received'::"text", 'verification_required'::"text", 'verification_completed'::"text"])))
);

ALTER TABLE ONLY "public"."notifications" REPLICA IDENTITY FULL;


ALTER TABLE "public"."notifications" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."organization_files" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "path" "text" NOT NULL,
    "size_bytes" bigint NOT NULL,
    "file_type" character varying(50) NOT NULL,
    "mime_type" character varying(100) NOT NULL,
    "bucket" character varying(100) DEFAULT 'documents'::character varying,
    "uploaded_by" "uuid",
    "uploaded_at" timestamp with time zone DEFAULT "now"(),
    "last_accessed" timestamp with time zone,
    "access_count" integer DEFAULT 0,
    "is_active" boolean DEFAULT true,
    "deleted_at" timestamp with time zone,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "status" character varying(50) DEFAULT 'uploaded'::character varying,
    "status_updated_at" timestamp with time zone,
    "processing_started_at" timestamp with time zone,
    "review_ready_at" timestamp with time zone,
    "approved_at" timestamp with time zone,
    "rejected_at" timestamp with time zone,
    "rejection_reason" "text",
    "reviewed_by" "uuid",
    "approved_by" "uuid",
    CONSTRAINT "chk_status" CHECK ((("status")::"text" = ANY ((ARRAY['uploaded'::character varying, 'processing'::character varying, 'staff_review'::character varying, 'ready_for_review'::character varying, 'approved'::character varying, 'rejected'::character varying])::"text"[])))
);


ALTER TABLE "public"."organization_files" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."organization_members" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "role" character varying(20) NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    "is_active" boolean DEFAULT true,
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "organization_members_role_check" CHECK ((("role")::"text" = ANY ((ARRAY['admin'::character varying, 'editor'::character varying, 'viewer'::character varying])::"text"[])))
);


ALTER TABLE "public"."organization_members" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."organization_metadata" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "total_employees" integer DEFAULT 0,
    "full_time_employees" integer DEFAULT 0,
    "part_time_employees" integer DEFAULT 0,
    "contract_employees" integer DEFAULT 0,
    "average_employees" integer DEFAULT 0,
    "annual_revenue" numeric(15,2) DEFAULT 0,
    "ebitda" numeric(15,2) DEFAULT 0,
    "total_assets" numeric(15,2) DEFAULT 0,
    "total_facilities" integer DEFAULT 0,
    "total_floor_area_sqft" numeric(12,2) DEFAULT 0,
    "occupied_floor_area_sqft" numeric(12,2) DEFAULT 0,
    "renewable_energy_percentage" numeric(5,2) DEFAULT 0,
    "carbon_offset_percentage" numeric(5,2) DEFAULT 0,
    "energy_intensity" numeric(10,2) DEFAULT 0,
    "reporting_standard" character varying(50) DEFAULT 'SECR'::character varying,
    "fiscal_year_start" "date",
    "fiscal_year_end" "date",
    "primary_contact_name" character varying(255),
    "primary_contact_email" character varying(255),
    "primary_contact_phone" character varying(50),
    "sustainability_officer_name" character varying(255),
    "sustainability_officer_email" character varying(255),
    "industry_sector" character varying(100),
    "naics_code" character varying(20),
    "sic_code" character varying(20),
    "custom_metrics" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "updated_by" "uuid"
);


ALTER TABLE "public"."organization_metadata" OWNER TO "postgres";


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


CREATE TABLE IF NOT EXISTS "public"."password_reset_tokens" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "token" character varying(255) NOT NULL,
    "expires_at" timestamp with time zone NOT NULL,
    "used" boolean DEFAULT false,
    "used_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."password_reset_tokens" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."pending_invites" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "email" character varying(255) NOT NULL,
    "role" character varying(20) NOT NULL,
    "created_at" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "pending_invites_role_check" CHECK ((("role")::"text" = ANY ((ARRAY['admin'::character varying, 'editor'::character varying, 'viewer'::character varying])::"text"[])))
);


ALTER TABLE "public"."pending_invites" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."processing_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "file_id" "uuid",
    "organization_id" "uuid",
    "step" character varying(50) NOT NULL,
    "status" character varying(20) NOT NULL,
    "started_at" timestamp with time zone DEFAULT "now"(),
    "completed_at" timestamp with time zone,
    "duration_ms" integer,
    "details" "jsonb" DEFAULT '{}'::"jsonb",
    "error" "text",
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."processing_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."queue_settings" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "max_reviews_per_staff" integer DEFAULT 10,
    "sla_hours" integer DEFAULT 24,
    "auto_assign_enabled" boolean DEFAULT false,
    "escalation_hours" integer DEFAULT 48,
    "priority_weights" "jsonb" DEFAULT '{"low": 1, "high": 3, "medium": 2}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "updated_by" "uuid"
);


ALTER TABLE "public"."queue_settings" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."review_assignment_history" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "review_id" "uuid",
    "assigned_by" "uuid",
    "assigned_to" "uuid",
    "previous_assigned_to" "uuid",
    "action" character varying(50) NOT NULL,
    "note" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."review_assignment_history" OWNER TO "postgres";


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
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
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


CREATE OR REPLACE VIEW "public"."staff_activity_summary" AS
 SELECT "staff_id",
    "date_trunc"('day'::"text", "created_at") AS "activity_date",
    "action_type",
    "count"(*) AS "total_actions"
   FROM "public"."audit_logs"
  WHERE (("staff_id" IS NOT NULL) AND ("created_at" > ("now"() - '30 days'::interval)))
  GROUP BY "staff_id", ("date_trunc"('day'::"text", "created_at")), "action_type"
  ORDER BY ("date_trunc"('day'::"text", "created_at")) DESC;


ALTER VIEW "public"."staff_activity_summary" OWNER TO "postgres";


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
    "permissions" "jsonb" DEFAULT '{}'::"jsonb",
    "reviews_assigned" integer DEFAULT 0,
    "reviews_completed" integer DEFAULT 0,
    "avg_review_time_seconds" integer DEFAULT 0,
    "total_review_time_seconds" integer DEFAULT 0,
    "current_load" integer DEFAULT 0,
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."staff_profiles" OWNER TO "postgres";


COMMENT ON COLUMN "public"."staff_profiles"."updated_at" IS 'Updated at';



CREATE TABLE IF NOT EXISTS "public"."staff_workload" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "staff_id" "uuid",
    "assigned_reviews" integer DEFAULT 0,
    "in_progress_reviews" integer DEFAULT 0,
    "pending_reviews" integer DEFAULT 0,
    "completed_today" integer DEFAULT 0,
    "workload_score" double precision DEFAULT 0,
    "last_updated" timestamp with time zone DEFAULT "now"(),
    "date" "date" DEFAULT CURRENT_DATE,
    "updated_at" timestamp with time zone DEFAULT "now"()
);

ALTER TABLE ONLY "public"."staff_workload" REPLICA IDENTITY FULL;


ALTER TABLE "public"."staff_workload" OWNER TO "postgres";


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


CREATE TABLE IF NOT EXISTS "public"."typing_status" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "conversation_id" "uuid",
    "is_typing" boolean DEFAULT false,
    "started_at" timestamp with time zone,
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."typing_status" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."units" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "code" character varying(50) NOT NULL,
    "name" character varying(100) NOT NULL,
    "category" character varying(50) NOT NULL,
    "symbol" character varying(20),
    "conversion_factor" numeric(10,6) DEFAULT 1,
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."units" OWNER TO "postgres";


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
    "metadata" "jsonb",
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."upload_batches" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_activity_log" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "action" character varying(100) NOT NULL,
    "details" "jsonb" DEFAULT '{}'::"jsonb",
    "ip_address" character varying(45),
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
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
    CONSTRAINT "user_feedback_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'in_progress'::"text", 'resolved'::"text", 'closed'::"text"]))),
    CONSTRAINT "user_feedback_type_check" CHECK (("type" = ANY (ARRAY['bug'::"text", 'feature'::"text", 'suggestion'::"text", 'question'::"text", 'feedback'::"text"])))
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
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."user_invitations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_presence" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "status" "text",
    "last_seen_at" timestamp with time zone,
    "current_channel" "text",
    "metadata" "jsonb",
    CONSTRAINT "user_presence_status_check" CHECK (("status" = ANY (ARRAY['online'::"text", 'away'::"text", 'offline'::"text", 'busy'::"text"])))
);


ALTER TABLE "public"."user_presence" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."verification_activity_log" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "verification_id" "uuid",
    "user_id" "uuid",
    "action_type" "text",
    "action_details" "jsonb",
    "ip_address" "text",
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "verification_activity_log_action_type_check" CHECK (("action_type" = ANY (ARRAY['submitted'::"text", 'verified'::"text", 'rejected'::"text", 'needs_revision'::"text", 'escalated'::"text"])))
);


ALTER TABLE "public"."verification_activity_log" OWNER TO "postgres";


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



ALTER TABLE ONLY "public"."activity_feed"
    ADD CONSTRAINT "activity_feed_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."activity_logs"
    ADD CONSTRAINT "activity_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."assets"
    ADD CONSTRAINT "assets_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."beta_access_codes"
    ADD CONSTRAINT "beta_access_codes_code_key" UNIQUE ("code");



ALTER TABLE ONLY "public"."beta_access_codes"
    ADD CONSTRAINT "beta_access_codes_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_email_unique" UNIQUE ("email");



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversation_activity_log"
    ADD CONSTRAINT "conversation_activity_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversation_participants"
    ADD CONSTRAINT "conversation_participants_conversation_id_user_id_key" UNIQUE ("conversation_id", "user_id");



ALTER TABLE ONLY "public"."conversation_participants"
    ADD CONSTRAINT "conversation_participants_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customer_documents"
    ADD CONSTRAINT "customer_documents_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customer_review_log"
    ADD CONSTRAINT "customer_review_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customer_verifications"
    ADD CONSTRAINT "customer_verifications_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."defra_conversion_factors"
    ADD CONSTRAINT "defra_conversion_factors_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."defra_conversion_factors"
    ADD CONSTRAINT "defra_conversion_factors_reporting_year_activity_type_key" UNIQUE ("reporting_year", "activity_type");



ALTER TABLE ONLY "public"."document_activity_log"
    ADD CONSTRAINT "document_activity_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."document_types"
    ADD CONSTRAINT "document_types_code_key" UNIQUE ("code");



ALTER TABLE ONLY "public"."document_types"
    ADD CONSTRAINT "document_types_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."draft_entries"
    ADD CONSTRAINT "draft_entries_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."email_logs"
    ADD CONSTRAINT "email_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."email_templates"
    ADD CONSTRAINT "email_templates_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."export_history"
    ADD CONSTRAINT "export_history_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."facilities"
    ADD CONSTRAINT "facilities_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."file_attachments"
    ADD CONSTRAINT "file_attachments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."glossary"
    ADD CONSTRAINT "glossary_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."glossary"
    ADD CONSTRAINT "glossary_term_key" UNIQUE ("term");



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."message_activity_log"
    ADD CONSTRAINT "message_activity_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."notification_delivery_log"
    ADD CONSTRAINT "notification_delivery_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."notifications"
    ADD CONSTRAINT "notifications_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."organization_files"
    ADD CONSTRAINT "organization_files_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."organization_members"
    ADD CONSTRAINT "organization_members_organization_id_user_id_key" UNIQUE ("organization_id", "user_id");



ALTER TABLE ONLY "public"."organization_members"
    ADD CONSTRAINT "organization_members_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."organization_metadata"
    ADD CONSTRAINT "organization_metadata_organization_id_key" UNIQUE ("organization_id");



ALTER TABLE ONLY "public"."organization_metadata"
    ADD CONSTRAINT "organization_metadata_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."organizations"
    ADD CONSTRAINT "organizations_company_number_key" UNIQUE ("company_number");



ALTER TABLE ONLY "public"."organizations"
    ADD CONSTRAINT "organizations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."password_reset_tokens"
    ADD CONSTRAINT "password_reset_tokens_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."password_reset_tokens"
    ADD CONSTRAINT "password_reset_tokens_token_key" UNIQUE ("token");



ALTER TABLE ONLY "public"."password_reset_tokens"
    ADD CONSTRAINT "password_reset_tokens_user_id_key" UNIQUE ("user_id");



ALTER TABLE ONLY "public"."pending_invites"
    ADD CONSTRAINT "pending_invites_organization_id_email_key" UNIQUE ("organization_id", "email");



ALTER TABLE ONLY "public"."pending_invites"
    ADD CONSTRAINT "pending_invites_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."processing_logs"
    ADD CONSTRAINT "processing_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."queue_settings"
    ADD CONSTRAINT "queue_settings_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."review_assignment_history"
    ADD CONSTRAINT "review_assignment_history_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."review_audit_trail"
    ADD CONSTRAINT "review_audit_trail_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_name_key" UNIQUE ("name");



ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."staff_profiles"
    ADD CONSTRAINT "staff_profiles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."staff_workload"
    ADD CONSTRAINT "staff_workload_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."staff_workload"
    ADD CONSTRAINT "staff_workload_staff_id_date_key" UNIQUE ("staff_id", "date");



ALTER TABLE ONLY "public"."system_settings"
    ADD CONSTRAINT "system_settings_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."typing_status"
    ADD CONSTRAINT "typing_status_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."defra_conversion_factors"
    ADD CONSTRAINT "unique_year_activity" UNIQUE ("reporting_year", "activity_type");



ALTER TABLE ONLY "public"."units"
    ADD CONSTRAINT "units_code_key" UNIQUE ("code");



ALTER TABLE ONLY "public"."units"
    ADD CONSTRAINT "units_pkey" PRIMARY KEY ("id");



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



ALTER TABLE ONLY "public"."user_presence"
    ADD CONSTRAINT "user_presence_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."verification_activity_log"
    ADD CONSTRAINT "verification_activity_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."waitlist"
    ADD CONSTRAINT "waitlist_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."waitlist"
    ADD CONSTRAINT "waitlist_pkey" PRIMARY KEY ("id");



CREATE INDEX "idx_activity_action" ON "public"."activity_logs" USING "btree" ("action");



CREATE INDEX "idx_activity_created" ON "public"."activity_logs" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_activity_logs_action" ON "public"."activity_logs" USING "btree" ("action");



CREATE INDEX "idx_activity_logs_created" ON "public"."activity_logs" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_activity_logs_org" ON "public"."activity_logs" USING "btree" ("organization_id");



CREATE INDEX "idx_activity_logs_user" ON "public"."activity_logs" USING "btree" ("user_id");



CREATE INDEX "idx_activity_org" ON "public"."activity_logs" USING "btree" ("organization_id");



CREATE INDEX "idx_activity_user" ON "public"."activity_logs" USING "btree" ("user_id");



CREATE INDEX "idx_assets_active" ON "public"."assets" USING "btree" ("is_active");



CREATE INDEX "idx_assets_facility" ON "public"."assets" USING "btree" ("facility_id");



CREATE INDEX "idx_assets_type" ON "public"."assets" USING "btree" ("type");



CREATE INDEX "idx_audit_logs_action_type" ON "public"."audit_logs" USING "btree" ("action_type");



CREATE INDEX "idx_audit_logs_created" ON "public"."audit_logs" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_audit_logs_org_created" ON "public"."audit_logs" USING "btree" ("organization_id", "created_at" DESC);



CREATE INDEX "idx_audit_logs_organization" ON "public"."audit_logs" USING "btree" ("organization_id");



CREATE INDEX "idx_audit_logs_resource" ON "public"."audit_logs" USING "btree" ("resource_type", "resource_id");



CREATE INDEX "idx_audit_logs_user" ON "public"."audit_logs" USING "btree" ("user_id");



CREATE INDEX "idx_beta_access_codes_magic_token" ON "public"."beta_access_codes" USING "btree" ("magic_token");



CREATE INDEX "idx_beta_code" ON "public"."beta_access_codes" USING "btree" ("code");



CREATE INDEX "idx_beta_email" ON "public"."beta_access_codes" USING "btree" ("email");



CREATE INDEX "idx_beta_status" ON "public"."beta_access_codes" USING "btree" ("status");



CREATE INDEX "idx_conversation_participants_active" ON "public"."conversation_participants" USING "btree" ("is_active");



CREATE INDEX "idx_conversation_participants_conv" ON "public"."conversation_participants" USING "btree" ("conversation_id");



CREATE INDEX "idx_conversation_participants_user" ON "public"."conversation_participants" USING "btree" ("user_id");



CREATE INDEX "idx_conversations_customer" ON "public"."conversations" USING "btree" ("customer_id");



CREATE INDEX "idx_conversations_organization" ON "public"."conversations" USING "btree" ("organization_id");



CREATE INDEX "idx_conversations_staff" ON "public"."conversations" USING "btree" ("staff_id");



CREATE INDEX "idx_customer_documents_asset" ON "public"."customer_documents" USING "btree" ("asset_id");



CREATE INDEX "idx_customer_documents_member" ON "public"."customer_documents" USING "btree" ("organization_member_id");



CREATE INDEX "idx_customer_documents_org" ON "public"."customer_documents" USING "btree" ("organization_id");



CREATE INDEX "idx_customer_documents_period" ON "public"."customer_documents" USING "btree" ("billing_period_start", "billing_period_end");



CREATE INDEX "idx_customer_documents_status" ON "public"."customer_documents" USING "btree" ("status");



CREATE INDEX "idx_customer_documents_type" ON "public"."customer_documents" USING "btree" ("document_type_id");



CREATE INDEX "idx_customer_documents_type_code" ON "public"."customer_documents" USING "btree" ("document_type_code");



CREATE INDEX "idx_customer_review_file" ON "public"."customer_review_log" USING "btree" ("file_id");



CREATE INDEX "idx_customer_review_status" ON "public"."customer_review_log" USING "btree" ("status");



CREATE INDEX "idx_customer_verifications_document" ON "public"."customer_verifications" USING "btree" ("customer_document_id");



CREATE INDEX "idx_customer_verifications_status" ON "public"."customer_verifications" USING "btree" ("status");



CREATE INDEX "idx_defra_lookup" ON "public"."defra_conversion_factors" USING "btree" ("reporting_year", "activity_type");



CREATE INDEX "idx_doc_activity_created" ON "public"."document_activity_log" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_doc_activity_file" ON "public"."document_activity_log" USING "btree" ("file_id");



CREATE INDEX "idx_doc_activity_org" ON "public"."document_activity_log" USING "btree" ("organization_id");



CREATE INDEX "idx_documents_org_status" ON "public"."organization_files" USING "btree" ("organization_id", "status");



CREATE INDEX "idx_documents_status" ON "public"."organization_files" USING "btree" ("status");



CREATE INDEX "idx_draft_entries_file" ON "public"."draft_entries" USING "btree" ("file_id");



CREATE INDEX "idx_draft_entries_org" ON "public"."draft_entries" USING "btree" ("organization_id");



CREATE INDEX "idx_draft_entries_user" ON "public"."draft_entries" USING "btree" ("user_id");



CREATE INDEX "idx_email_logs_email" ON "public"."email_logs" USING "btree" ("email");



CREATE INDEX "idx_email_logs_type" ON "public"."email_logs" USING "btree" ("type");



CREATE INDEX "idx_email_templates_active" ON "public"."email_templates" USING "btree" ("is_active");



CREATE INDEX "idx_email_templates_type" ON "public"."email_templates" USING "btree" ("type");



CREATE INDEX "idx_emissions_asset" ON "public"."emissions_logs" USING "btree" ("asset_id");



CREATE INDEX "idx_emissions_created" ON "public"."emissions_logs" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_emissions_date" ON "public"."emissions_logs" USING "btree" ("start_date", "end_date");



CREATE INDEX "idx_emissions_date_range" ON "public"."emissions_logs" USING "btree" ("start_date", "end_date");



CREATE INDEX "idx_emissions_metadata" ON "public"."emissions_logs" USING "gin" ("metadata");



CREATE INDEX "idx_emissions_org" ON "public"."emissions_logs" USING "btree" ("organization_id");



CREATE INDEX "idx_export_created" ON "public"."export_history" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_export_history_created" ON "public"."export_history" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_export_history_org" ON "public"."export_history" USING "btree" ("organization_id");



CREATE INDEX "idx_export_history_user" ON "public"."export_history" USING "btree" ("user_id");



CREATE INDEX "idx_export_org" ON "public"."export_history" USING "btree" ("organization_id");



CREATE INDEX "idx_export_user" ON "public"."export_history" USING "btree" ("user_id");



CREATE INDEX "idx_facilities_active" ON "public"."facilities" USING "btree" ("is_active");



CREATE INDEX "idx_facilities_city" ON "public"."facilities" USING "btree" ("city");



CREATE INDEX "idx_facilities_country" ON "public"."facilities" USING "btree" ("country");



CREATE INDEX "idx_facilities_org" ON "public"."facilities" USING "btree" ("organization_id");



CREATE INDEX "idx_facilities_postcode" ON "public"."facilities" USING "btree" ("postcode");



CREATE INDEX "idx_facilities_type" ON "public"."facilities" USING "btree" ("type");



CREATE INDEX "idx_file_attachments_conversation" ON "public"."file_attachments" USING "btree" ("conversation_id");



CREATE INDEX "idx_file_attachments_message" ON "public"."file_attachments" USING "btree" ("message_id");



CREATE INDEX "idx_file_attachments_organization" ON "public"."file_attachments" USING "btree" ("organization_id");



CREATE INDEX "idx_files_active" ON "public"."organization_files" USING "btree" ("is_active");



CREATE INDEX "idx_files_name_fts" ON "public"."organization_files" USING "gin" ("to_tsvector"('"english"'::"regconfig", ("name")::"text"));



CREATE INDEX "idx_files_org" ON "public"."organization_files" USING "btree" ("organization_id");



CREATE INDEX "idx_files_status" ON "public"."organization_files" USING "btree" ("status");



CREATE INDEX "idx_files_uploaded" ON "public"."organization_files" USING "btree" ("uploaded_at" DESC);



CREATE INDEX "idx_glossary_active" ON "public"."glossary" USING "btree" ("is_active");



CREATE INDEX "idx_glossary_category" ON "public"."glossary" USING "btree" ("category");



CREATE INDEX "idx_glossary_fts" ON "public"."glossary" USING "gin" ("to_tsvector"('"english"'::"regconfig", (("term" || ' '::"text") || "definition")));



CREATE INDEX "idx_glossary_is_active" ON "public"."glossary" USING "btree" ("is_active");



CREATE INDEX "idx_glossary_term" ON "public"."glossary" USING "btree" ("term");



CREATE INDEX "idx_manual_review_queue_batch" ON "public"."manual_review_queue" USING "btree" ("batch_id");



CREATE INDEX "idx_manual_review_queue_created" ON "public"."manual_review_queue" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_manual_review_queue_document" ON "public"."manual_review_queue" USING "btree" ("customer_document_id");



CREATE INDEX "idx_manual_review_queue_org" ON "public"."manual_review_queue" USING "btree" ("organization_id");



CREATE INDEX "idx_manual_review_queue_status" ON "public"."manual_review_queue" USING "btree" ("status");



CREATE INDEX "idx_members_org" ON "public"."organization_members" USING "btree" ("organization_id");



CREATE INDEX "idx_members_user" ON "public"."organization_members" USING "btree" ("user_id");



CREATE INDEX "idx_messages_conversation" ON "public"."messages" USING "btree" ("conversation_id");



CREATE INDEX "idx_messages_receiver" ON "public"."messages" USING "btree" ("receiver_id");



CREATE INDEX "idx_messages_sender" ON "public"."messages" USING "btree" ("sender_id");



CREATE INDEX "idx_mrq_created" ON "public"."manual_review_queue" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_mrq_priority" ON "public"."manual_review_queue" USING "btree" ("priority_score" DESC);



CREATE INDEX "idx_mrq_status_assigned" ON "public"."manual_review_queue" USING "btree" ("status", "assigned_to");



CREATE INDEX "idx_notifications_created" ON "public"."notifications" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_notifications_is_read" ON "public"."notifications" USING "btree" ("is_read");



CREATE INDEX "idx_notifications_user" ON "public"."notifications" USING "btree" ("user_id");



CREATE INDEX "idx_org_files_active" ON "public"."organization_files" USING "btree" ("is_active");



CREATE INDEX "idx_org_files_org" ON "public"."organization_files" USING "btree" ("organization_id");



CREATE INDEX "idx_org_files_org_status" ON "public"."organization_files" USING "btree" ("organization_id", "status");



CREATE INDEX "idx_org_files_status" ON "public"."organization_files" USING "btree" ("status");



CREATE INDEX "idx_org_files_type" ON "public"."organization_files" USING "btree" ("file_type");



CREATE INDEX "idx_org_files_uploaded" ON "public"."organization_files" USING "btree" ("uploaded_at" DESC);



CREATE INDEX "idx_org_members_active" ON "public"."organization_members" USING "btree" ("is_active");



CREATE INDEX "idx_org_members_org" ON "public"."organization_members" USING "btree" ("organization_id");



CREATE INDEX "idx_org_members_org_user" ON "public"."organization_members" USING "btree" ("organization_id", "user_id");



CREATE INDEX "idx_org_members_role" ON "public"."organization_members" USING "btree" ("role");



CREATE INDEX "idx_org_members_user" ON "public"."organization_members" USING "btree" ("user_id");



CREATE INDEX "idx_org_metadata_org_id" ON "public"."organization_metadata" USING "btree" ("organization_id");



CREATE INDEX "idx_org_metadata_reporting_standard" ON "public"."organization_metadata" USING "btree" ("reporting_standard");



CREATE INDEX "idx_organizations_created_at" ON "public"."organizations" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_organizations_name" ON "public"."organizations" USING "btree" ("name");



CREATE INDEX "idx_organizations_subscription_status" ON "public"."organizations" USING "btree" ("subscription_status");



CREATE INDEX "idx_password_reset_token" ON "public"."password_reset_tokens" USING "btree" ("token");



CREATE INDEX "idx_password_reset_user" ON "public"."password_reset_tokens" USING "btree" ("user_id");



CREATE INDEX "idx_processing_logs_file" ON "public"."processing_logs" USING "btree" ("file_id");



CREATE INDEX "idx_processing_logs_step" ON "public"."processing_logs" USING "btree" ("step");



CREATE INDEX "idx_review_assignment_review" ON "public"."review_assignment_history" USING "btree" ("review_id");



CREATE INDEX "idx_review_assignment_to" ON "public"."review_assignment_history" USING "btree" ("assigned_to");



CREATE INDEX "idx_review_audit_trail_created_at" ON "public"."review_audit_trail" USING "btree" ("created_at");



CREATE INDEX "idx_review_audit_trail_performed_by" ON "public"."review_audit_trail" USING "btree" ("performed_by");



CREATE INDEX "idx_review_audit_trail_review_id" ON "public"."review_audit_trail" USING "btree" ("review_id");



CREATE INDEX "idx_review_queue_assigned" ON "public"."manual_review_queue" USING "btree" ("assigned_to");



CREATE INDEX "idx_review_queue_created" ON "public"."manual_review_queue" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_review_queue_priority" ON "public"."manual_review_queue" USING "btree" ("priority_score" DESC);



CREATE INDEX "idx_review_queue_sla" ON "public"."manual_review_queue" USING "btree" ("sla_deadline");



CREATE INDEX "idx_review_queue_status" ON "public"."manual_review_queue" USING "btree" ("status");



CREATE INDEX "idx_staff_profiles_active" ON "public"."staff_profiles" USING "btree" ("is_active");



CREATE INDEX "idx_staff_profiles_email" ON "public"."staff_profiles" USING "btree" ("email");



CREATE INDEX "idx_staff_profiles_role" ON "public"."staff_profiles" USING "btree" ("role");



CREATE INDEX "idx_staff_profiles_user" ON "public"."staff_profiles" USING "btree" ("user_id");



CREATE INDEX "idx_staff_workload_date" ON "public"."staff_workload" USING "btree" ("date");



CREATE INDEX "idx_staff_workload_staff" ON "public"."staff_workload" USING "btree" ("staff_id");



CREATE INDEX "idx_units_active" ON "public"."units" USING "btree" ("is_active");



CREATE INDEX "idx_units_category" ON "public"."units" USING "btree" ("category");



CREATE INDEX "idx_upload_batches_org" ON "public"."upload_batches" USING "btree" ("organization_id");



CREATE INDEX "idx_upload_batches_status" ON "public"."upload_batches" USING "btree" ("status");



CREATE INDEX "idx_waitlist_created" ON "public"."waitlist" USING "btree" ("created_at" DESC);



CREATE INDEX "idx_waitlist_email" ON "public"."waitlist" USING "btree" ("email");



CREATE INDEX "idx_waitlist_status" ON "public"."waitlist" USING "btree" ("status");



CREATE OR REPLACE VIEW "public"."conversation_details" AS
 SELECT "c"."id",
    "c"."organization_id",
    "c"."staff_id",
    "c"."customer_id",
    "c"."subject",
    "c"."status",
    "c"."last_message_at",
    "c"."created_by",
    "c"."closed_by",
    "c"."closed_at",
    "c"."is_urgent",
    "c"."priority",
    "c"."created_at",
    "c"."updated_at",
    "c"."read_by",
    "c"."unread_count",
    "c"."participant_count",
    "count"(DISTINCT "cp"."user_id") AS "total_participants",
    "json_agg"(DISTINCT "jsonb_build_object"('user_id', "cp"."user_id", 'joined_at', "cp"."joined_at", 'is_active', "cp"."is_active")) FILTER (WHERE ("cp"."user_id" IS NOT NULL)) AS "participants"
   FROM ("public"."conversations" "c"
     LEFT JOIN "public"."conversation_participants" "cp" ON (("cp"."conversation_id" = "c"."id")))
  GROUP BY "c"."id";



CREATE OR REPLACE TRIGGER "trigger_log_document_status" AFTER UPDATE OF "status" ON "public"."organization_files" FOR EACH ROW EXECUTE FUNCTION "public"."log_document_status_change"();



ALTER TABLE ONLY "public"."activity_feed"
    ADD CONSTRAINT "activity_feed_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."activity_feed"
    ADD CONSTRAINT "activity_feed_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."activity_logs"
    ADD CONSTRAINT "activity_logs_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."activity_logs"
    ADD CONSTRAINT "activity_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."assets"
    ADD CONSTRAINT "assets_facility_id_fkey" FOREIGN KEY ("facility_id") REFERENCES "public"."facilities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_organization_member_id_fkey" FOREIGN KEY ("organization_member_id") REFERENCES "public"."organization_members"("id");



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_staff_id_fkey" FOREIGN KEY ("staff_id") REFERENCES "public"."staff_profiles"("id");



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_beta_code_fkey" FOREIGN KEY ("beta_code") REFERENCES "public"."beta_access_codes"("code");



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_invited_by_fkey" FOREIGN KEY ("invited_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."conversation_activity_log"
    ADD CONSTRAINT "conversation_activity_log_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id");



ALTER TABLE ONLY "public"."conversation_activity_log"
    ADD CONSTRAINT "conversation_activity_log_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."conversation_participants"
    ADD CONSTRAINT "conversation_participants_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."conversation_participants"
    ADD CONSTRAINT "conversation_participants_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_closed_by_fkey" FOREIGN KEY ("closed_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_customer_id_fkey" FOREIGN KEY ("customer_id") REFERENCES "public"."organization_members"("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_staff_id_fkey" FOREIGN KEY ("staff_id") REFERENCES "public"."staff_profiles"("id");



ALTER TABLE ONLY "public"."customer_documents"
    ADD CONSTRAINT "customer_documents_asset_id_fkey" FOREIGN KEY ("asset_id") REFERENCES "public"."assets"("id");



ALTER TABLE ONLY "public"."customer_documents"
    ADD CONSTRAINT "customer_documents_classification_by_fkey" FOREIGN KEY ("classification_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."customer_documents"
    ADD CONSTRAINT "customer_documents_document_type_id_fkey" FOREIGN KEY ("document_type_id") REFERENCES "public"."document_types"("id");



ALTER TABLE ONLY "public"."customer_documents"
    ADD CONSTRAINT "customer_documents_manual_review_queue_id_fkey" FOREIGN KEY ("manual_review_queue_id") REFERENCES "public"."manual_review_queue"("id");



ALTER TABLE ONLY "public"."customer_documents"
    ADD CONSTRAINT "customer_documents_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."customer_documents"
    ADD CONSTRAINT "customer_documents_organization_member_id_fkey" FOREIGN KEY ("organization_member_id") REFERENCES "public"."organization_members"("id");



ALTER TABLE ONLY "public"."customer_review_log"
    ADD CONSTRAINT "customer_review_log_file_id_fkey" FOREIGN KEY ("file_id") REFERENCES "public"."organization_files"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."customer_review_log"
    ADD CONSTRAINT "customer_review_log_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."customer_review_log"
    ADD CONSTRAINT "customer_review_log_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."customer_verifications"
    ADD CONSTRAINT "customer_verifications_customer_document_id_fkey" FOREIGN KEY ("customer_document_id") REFERENCES "public"."customer_documents"("id");



ALTER TABLE ONLY "public"."customer_verifications"
    ADD CONSTRAINT "customer_verifications_customer_member_id_fkey" FOREIGN KEY ("customer_member_id") REFERENCES "public"."organization_members"("id");



ALTER TABLE ONLY "public"."customer_verifications"
    ADD CONSTRAINT "customer_verifications_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."customer_verifications"
    ADD CONSTRAINT "customer_verifications_rejected_by_fkey" FOREIGN KEY ("rejected_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."customer_verifications"
    ADD CONSTRAINT "customer_verifications_revision_requested_by_fkey" FOREIGN KEY ("revision_requested_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."customer_verifications"
    ADD CONSTRAINT "customer_verifications_submitted_by_fkey" FOREIGN KEY ("submitted_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."customer_verifications"
    ADD CONSTRAINT "customer_verifications_verified_by_fkey" FOREIGN KEY ("verified_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."document_activity_log"
    ADD CONSTRAINT "document_activity_log_file_id_fkey" FOREIGN KEY ("file_id") REFERENCES "public"."organization_files"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."document_activity_log"
    ADD CONSTRAINT "document_activity_log_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."document_activity_log"
    ADD CONSTRAINT "document_activity_log_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."draft_entries"
    ADD CONSTRAINT "draft_entries_file_id_fkey" FOREIGN KEY ("file_id") REFERENCES "public"."organization_files"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."draft_entries"
    ADD CONSTRAINT "draft_entries_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."draft_entries"
    ADD CONSTRAINT "draft_entries_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."email_templates"
    ADD CONSTRAINT "email_templates_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."email_templates"
    ADD CONSTRAINT "email_templates_updated_by_fkey" FOREIGN KEY ("updated_by") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_asset_id_fkey" FOREIGN KEY ("asset_id") REFERENCES "public"."assets"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_created_by_user_id_fkey" FOREIGN KEY ("created_by_user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_customer_document_id_fkey" FOREIGN KEY ("customer_document_id") REFERENCES "public"."customer_documents"("id");



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_defra_factor_id_fkey" FOREIGN KEY ("defra_factor_id") REFERENCES "public"."defra_conversion_factors"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_file_id_fkey" FOREIGN KEY ("file_id") REFERENCES "public"."organization_files"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."export_history"
    ADD CONSTRAINT "export_history_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."export_history"
    ADD CONSTRAINT "export_history_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."facilities"
    ADD CONSTRAINT "facilities_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."file_attachments"
    ADD CONSTRAINT "file_attachments_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."file_attachments"
    ADD CONSTRAINT "file_attachments_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "public"."messages"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."file_attachments"
    ADD CONSTRAINT "file_attachments_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."file_attachments"
    ADD CONSTRAINT "file_attachments_uploaded_by_fkey" FOREIGN KEY ("uploaded_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_assigned_by_fkey" FOREIGN KEY ("assigned_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_assigned_to_fkey" FOREIGN KEY ("assigned_to") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_batch_id_fkey" FOREIGN KEY ("batch_id") REFERENCES "public"."upload_batches"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_completed_by_fkey" FOREIGN KEY ("completed_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_customer_document_id_fkey" FOREIGN KEY ("customer_document_id") REFERENCES "public"."customer_documents"("id");



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."message_activity_log"
    ADD CONSTRAINT "message_activity_log_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id");



ALTER TABLE ONLY "public"."message_activity_log"
    ADD CONSTRAINT "message_activity_log_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "public"."messages"("id");



ALTER TABLE ONLY "public"."message_activity_log"
    ADD CONSTRAINT "message_activity_log_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_parent_message_id_fkey" FOREIGN KEY ("parent_message_id") REFERENCES "public"."messages"("id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_receiver_id_fkey" FOREIGN KEY ("receiver_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_sender_id_fkey" FOREIGN KEY ("sender_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."notification_delivery_log"
    ADD CONSTRAINT "notification_delivery_log_notification_id_fkey" FOREIGN KEY ("notification_id") REFERENCES "public"."notifications"("id");



ALTER TABLE ONLY "public"."notification_delivery_log"
    ADD CONSTRAINT "notification_delivery_log_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."notifications"
    ADD CONSTRAINT "notifications_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."notifications"
    ADD CONSTRAINT "notifications_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."organization_files"
    ADD CONSTRAINT "organization_files_approved_by_fkey" FOREIGN KEY ("approved_by") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."organization_files"
    ADD CONSTRAINT "organization_files_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."organization_files"
    ADD CONSTRAINT "organization_files_reviewed_by_fkey" FOREIGN KEY ("reviewed_by") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."organization_files"
    ADD CONSTRAINT "organization_files_uploaded_by_fkey" FOREIGN KEY ("uploaded_by") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."organization_members"
    ADD CONSTRAINT "organization_members_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."organization_members"
    ADD CONSTRAINT "organization_members_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."organization_metadata"
    ADD CONSTRAINT "organization_metadata_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."organization_metadata"
    ADD CONSTRAINT "organization_metadata_updated_by_fkey" FOREIGN KEY ("updated_by") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."password_reset_tokens"
    ADD CONSTRAINT "password_reset_tokens_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."pending_invites"
    ADD CONSTRAINT "pending_invites_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."processing_logs"
    ADD CONSTRAINT "processing_logs_file_id_fkey" FOREIGN KEY ("file_id") REFERENCES "public"."organization_files"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."processing_logs"
    ADD CONSTRAINT "processing_logs_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."queue_settings"
    ADD CONSTRAINT "queue_settings_updated_by_fkey" FOREIGN KEY ("updated_by") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."review_assignment_history"
    ADD CONSTRAINT "review_assignment_history_assigned_by_fkey" FOREIGN KEY ("assigned_by") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."review_assignment_history"
    ADD CONSTRAINT "review_assignment_history_assigned_to_fkey" FOREIGN KEY ("assigned_to") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."review_assignment_history"
    ADD CONSTRAINT "review_assignment_history_previous_assigned_to_fkey" FOREIGN KEY ("previous_assigned_to") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."review_assignment_history"
    ADD CONSTRAINT "review_assignment_history_review_id_fkey" FOREIGN KEY ("review_id") REFERENCES "public"."manual_review_queue"("id") ON DELETE CASCADE;



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



ALTER TABLE ONLY "public"."staff_workload"
    ADD CONSTRAINT "staff_workload_staff_id_fkey" FOREIGN KEY ("staff_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."system_settings"
    ADD CONSTRAINT "system_settings_updated_by_fkey" FOREIGN KEY ("updated_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."typing_status"
    ADD CONSTRAINT "typing_status_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id");



ALTER TABLE ONLY "public"."typing_status"
    ADD CONSTRAINT "typing_status_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



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



ALTER TABLE ONLY "public"."user_presence"
    ADD CONSTRAINT "user_presence_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."verification_activity_log"
    ADD CONSTRAINT "verification_activity_log_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."verification_activity_log"
    ADD CONSTRAINT "verification_activity_log_verification_id_fkey" FOREIGN KEY ("verification_id") REFERENCES "public"."customer_verifications"("id");



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



CREATE POLICY "Can see messages in conversation" ON "public"."messages" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."conversation_participants"
  WHERE (("conversation_participants"."conversation_id" = "messages"."conversation_id") AND ("conversation_participants"."user_id" = "auth"."uid"())))));



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



CREATE POLICY "Org members see documents" ON "public"."customer_documents" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."organization_members"
  WHERE (("organization_members"."organization_id" = "customer_documents"."organization_id") AND ("organization_members"."user_id" = "auth"."uid"())))));



CREATE POLICY "Organizations can view their own batches" ON "public"."upload_batches" FOR SELECT USING (("organization_id" IN ( SELECT "organization_members"."organization_id"
   FROM "public"."organization_members"
  WHERE ("organization_members"."user_id" = "auth"."uid"()))));



CREATE POLICY "Staff can insert queue items" ON "public"."manual_review_queue" FOR INSERT WITH CHECK (true);



CREATE POLICY "Staff can update queue items" ON "public"."manual_review_queue" FOR UPDATE USING (true) WITH CHECK (true);



CREATE POLICY "Staff can view their own profile" ON "public"."staff_profiles" FOR SELECT USING (("id" = "auth"."uid"()));



CREATE POLICY "Users can delete conversation participants" ON "public"."conversation_participants" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert conversation participants" ON "public"."conversation_participants" FOR INSERT WITH CHECK ((("auth"."uid"() = "user_id") OR (EXISTS ( SELECT 1
   FROM "public"."conversation_participants" "cp2"
  WHERE (("cp2"."conversation_id" = "conversation_participants"."conversation_id") AND ("cp2"."user_id" = "auth"."uid"()))))));



CREATE POLICY "Users can join conversations" ON "public"."conversation_participants" FOR INSERT WITH CHECK (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can leave conversations" ON "public"."conversation_participants" FOR DELETE USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can see conversation participants" ON "public"."conversation_participants" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."conversation_participants" "cp2"
  WHERE (("cp2"."conversation_id" = "conversation_participants"."conversation_id") AND ("cp2"."user_id" = "auth"."uid"())))));



CREATE POLICY "Users can see own notifications" ON "public"."notifications" FOR SELECT USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can update conversation participants" ON "public"."conversation_participants" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update own participation" ON "public"."conversation_participants" FOR UPDATE USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can view conversation participants" ON "public"."conversation_participants" FOR SELECT USING ((("auth"."uid"() = "user_id") OR (EXISTS ( SELECT 1
   FROM "public"."conversation_participants" "cp2"
  WHERE (("cp2"."conversation_id" = "conversation_participants"."conversation_id") AND ("cp2"."user_id" = "auth"."uid"()))))));



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



ALTER TABLE "public"."beta_access_codes" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."beta_users" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."defra_conversion_factors" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."emissions_logs" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."glossary" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."manual_review_queue" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."pending_invites" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."roles" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."staff_profiles" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."system_settings" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."upload_batches" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_activity_log" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_invitations" ENABLE ROW LEVEL SECURITY;


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";



GRANT ALL ON FUNCTION "public"."delete_old_audit_logs"() TO "anon";
GRANT ALL ON FUNCTION "public"."delete_old_audit_logs"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."delete_old_audit_logs"() TO "service_role";



GRANT ALL ON FUNCTION "public"."get_admin_customer_overview"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_admin_customer_overview"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_admin_customer_overview"() TO "service_role";



GRANT ALL ON FUNCTION "public"."get_admin_dashboard_stats"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_admin_dashboard_stats"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_admin_dashboard_stats"() TO "service_role";



GRANT ALL ON FUNCTION "public"."get_document_status_counts"("org_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."get_document_status_counts"("org_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_document_status_counts"("org_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."get_platform_users"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_platform_users"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_platform_users"() TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "service_role";



GRANT ALL ON FUNCTION "public"."log_document_status_change"() TO "anon";
GRANT ALL ON FUNCTION "public"."log_document_status_change"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."log_document_status_change"() TO "service_role";



GRANT ALL ON TABLE "public"."activity_categories" TO "anon";
GRANT ALL ON TABLE "public"."activity_categories" TO "authenticated";
GRANT ALL ON TABLE "public"."activity_categories" TO "service_role";



GRANT ALL ON TABLE "public"."activity_feed" TO "anon";
GRANT ALL ON TABLE "public"."activity_feed" TO "authenticated";
GRANT ALL ON TABLE "public"."activity_feed" TO "service_role";



GRANT ALL ON TABLE "public"."activity_logs" TO "anon";
GRANT ALL ON TABLE "public"."activity_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."activity_logs" TO "service_role";



GRANT ALL ON TABLE "public"."audit_logs" TO "anon";
GRANT ALL ON TABLE "public"."audit_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."audit_logs" TO "service_role";



GRANT ALL ON TABLE "public"."activity_summary" TO "anon";
GRANT ALL ON TABLE "public"."activity_summary" TO "authenticated";
GRANT ALL ON TABLE "public"."activity_summary" TO "service_role";



GRANT ALL ON TABLE "public"."assets" TO "anon";
GRANT ALL ON TABLE "public"."assets" TO "authenticated";
GRANT ALL ON TABLE "public"."assets" TO "service_role";



GRANT ALL ON TABLE "public"."beta_access_codes" TO "anon";
GRANT ALL ON TABLE "public"."beta_access_codes" TO "authenticated";
GRANT ALL ON TABLE "public"."beta_access_codes" TO "service_role";



GRANT ALL ON TABLE "public"."beta_users" TO "anon";
GRANT ALL ON TABLE "public"."beta_users" TO "authenticated";
GRANT ALL ON TABLE "public"."beta_users" TO "service_role";



GRANT ALL ON TABLE "public"."conversation_activity_log" TO "anon";
GRANT ALL ON TABLE "public"."conversation_activity_log" TO "authenticated";
GRANT ALL ON TABLE "public"."conversation_activity_log" TO "service_role";



GRANT ALL ON TABLE "public"."conversation_details" TO "anon";
GRANT ALL ON TABLE "public"."conversation_details" TO "authenticated";
GRANT ALL ON TABLE "public"."conversation_details" TO "service_role";



GRANT ALL ON TABLE "public"."conversation_participants" TO "anon";
GRANT ALL ON TABLE "public"."conversation_participants" TO "authenticated";
GRANT ALL ON TABLE "public"."conversation_participants" TO "service_role";



GRANT ALL ON TABLE "public"."conversations" TO "anon";
GRANT ALL ON TABLE "public"."conversations" TO "authenticated";
GRANT ALL ON TABLE "public"."conversations" TO "service_role";



GRANT ALL ON TABLE "public"."customer_activity_summary" TO "anon";
GRANT ALL ON TABLE "public"."customer_activity_summary" TO "authenticated";
GRANT ALL ON TABLE "public"."customer_activity_summary" TO "service_role";



GRANT ALL ON TABLE "public"."customer_documents" TO "anon";
GRANT ALL ON TABLE "public"."customer_documents" TO "authenticated";
GRANT ALL ON TABLE "public"."customer_documents" TO "service_role";



GRANT ALL ON TABLE "public"."customer_review_log" TO "anon";
GRANT ALL ON TABLE "public"."customer_review_log" TO "authenticated";
GRANT ALL ON TABLE "public"."customer_review_log" TO "service_role";



GRANT ALL ON TABLE "public"."customer_verifications" TO "anon";
GRANT ALL ON TABLE "public"."customer_verifications" TO "authenticated";
GRANT ALL ON TABLE "public"."customer_verifications" TO "service_role";



GRANT ALL ON TABLE "public"."defra_conversion_factors" TO "anon";
GRANT ALL ON TABLE "public"."defra_conversion_factors" TO "authenticated";
GRANT ALL ON TABLE "public"."defra_conversion_factors" TO "service_role";



GRANT ALL ON TABLE "public"."document_activity_log" TO "anon";
GRANT ALL ON TABLE "public"."document_activity_log" TO "authenticated";
GRANT ALL ON TABLE "public"."document_activity_log" TO "service_role";



GRANT ALL ON TABLE "public"."document_types" TO "anon";
GRANT ALL ON TABLE "public"."document_types" TO "authenticated";
GRANT ALL ON TABLE "public"."document_types" TO "service_role";



GRANT ALL ON TABLE "public"."draft_entries" TO "anon";
GRANT ALL ON TABLE "public"."draft_entries" TO "authenticated";
GRANT ALL ON TABLE "public"."draft_entries" TO "service_role";



GRANT ALL ON TABLE "public"."email_logs" TO "anon";
GRANT ALL ON TABLE "public"."email_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."email_logs" TO "service_role";



GRANT ALL ON TABLE "public"."email_templates" TO "anon";
GRANT ALL ON TABLE "public"."email_templates" TO "authenticated";
GRANT ALL ON TABLE "public"."email_templates" TO "service_role";



GRANT ALL ON TABLE "public"."emissions_logs" TO "anon";
GRANT ALL ON TABLE "public"."emissions_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."emissions_logs" TO "service_role";



GRANT ALL ON TABLE "public"."export_history" TO "anon";
GRANT ALL ON TABLE "public"."export_history" TO "authenticated";
GRANT ALL ON TABLE "public"."export_history" TO "service_role";



GRANT ALL ON TABLE "public"."facilities" TO "anon";
GRANT ALL ON TABLE "public"."facilities" TO "authenticated";
GRANT ALL ON TABLE "public"."facilities" TO "service_role";



GRANT ALL ON TABLE "public"."file_attachments" TO "anon";
GRANT ALL ON TABLE "public"."file_attachments" TO "authenticated";
GRANT ALL ON TABLE "public"."file_attachments" TO "service_role";



GRANT ALL ON TABLE "public"."glossary" TO "anon";
GRANT ALL ON TABLE "public"."glossary" TO "authenticated";
GRANT ALL ON TABLE "public"."glossary" TO "service_role";



GRANT ALL ON TABLE "public"."live_dashboard" TO "anon";
GRANT ALL ON TABLE "public"."live_dashboard" TO "authenticated";
GRANT ALL ON TABLE "public"."live_dashboard" TO "service_role";



GRANT ALL ON TABLE "public"."manual_review_queue" TO "anon";
GRANT ALL ON TABLE "public"."manual_review_queue" TO "authenticated";
GRANT ALL ON TABLE "public"."manual_review_queue" TO "service_role";



GRANT ALL ON TABLE "public"."message_activity_log" TO "anon";
GRANT ALL ON TABLE "public"."message_activity_log" TO "authenticated";
GRANT ALL ON TABLE "public"."message_activity_log" TO "service_role";



GRANT ALL ON TABLE "public"."messages" TO "anon";
GRANT ALL ON TABLE "public"."messages" TO "authenticated";
GRANT ALL ON TABLE "public"."messages" TO "service_role";



GRANT ALL ON TABLE "public"."notification_delivery_log" TO "anon";
GRANT ALL ON TABLE "public"."notification_delivery_log" TO "authenticated";
GRANT ALL ON TABLE "public"."notification_delivery_log" TO "service_role";



GRANT ALL ON TABLE "public"."notifications" TO "anon";
GRANT ALL ON TABLE "public"."notifications" TO "authenticated";
GRANT ALL ON TABLE "public"."notifications" TO "service_role";



GRANT ALL ON TABLE "public"."organization_files" TO "anon";
GRANT ALL ON TABLE "public"."organization_files" TO "authenticated";
GRANT ALL ON TABLE "public"."organization_files" TO "service_role";



GRANT ALL ON TABLE "public"."organization_members" TO "anon";
GRANT ALL ON TABLE "public"."organization_members" TO "authenticated";
GRANT ALL ON TABLE "public"."organization_members" TO "service_role";



GRANT ALL ON TABLE "public"."organization_metadata" TO "anon";
GRANT ALL ON TABLE "public"."organization_metadata" TO "authenticated";
GRANT ALL ON TABLE "public"."organization_metadata" TO "service_role";



GRANT ALL ON TABLE "public"."organizations" TO "anon";
GRANT ALL ON TABLE "public"."organizations" TO "authenticated";
GRANT ALL ON TABLE "public"."organizations" TO "service_role";



GRANT ALL ON TABLE "public"."password_reset_tokens" TO "anon";
GRANT ALL ON TABLE "public"."password_reset_tokens" TO "authenticated";
GRANT ALL ON TABLE "public"."password_reset_tokens" TO "service_role";



GRANT ALL ON TABLE "public"."pending_invites" TO "anon";
GRANT ALL ON TABLE "public"."pending_invites" TO "authenticated";
GRANT ALL ON TABLE "public"."pending_invites" TO "service_role";



GRANT ALL ON TABLE "public"."processing_logs" TO "anon";
GRANT ALL ON TABLE "public"."processing_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."processing_logs" TO "service_role";



GRANT ALL ON TABLE "public"."queue_settings" TO "anon";
GRANT ALL ON TABLE "public"."queue_settings" TO "authenticated";
GRANT ALL ON TABLE "public"."queue_settings" TO "service_role";



GRANT ALL ON TABLE "public"."review_assignment_history" TO "anon";
GRANT ALL ON TABLE "public"."review_assignment_history" TO "authenticated";
GRANT ALL ON TABLE "public"."review_assignment_history" TO "service_role";



GRANT ALL ON TABLE "public"."review_audit_trail" TO "anon";
GRANT ALL ON TABLE "public"."review_audit_trail" TO "authenticated";
GRANT ALL ON TABLE "public"."review_audit_trail" TO "service_role";



GRANT ALL ON TABLE "public"."roles" TO "anon";
GRANT ALL ON TABLE "public"."roles" TO "authenticated";
GRANT ALL ON TABLE "public"."roles" TO "service_role";



GRANT ALL ON TABLE "public"."staff_activity_summary" TO "anon";
GRANT ALL ON TABLE "public"."staff_activity_summary" TO "authenticated";
GRANT ALL ON TABLE "public"."staff_activity_summary" TO "service_role";



GRANT ALL ON TABLE "public"."staff_profiles" TO "anon";
GRANT ALL ON TABLE "public"."staff_profiles" TO "authenticated";
GRANT ALL ON TABLE "public"."staff_profiles" TO "service_role";



GRANT ALL ON TABLE "public"."staff_workload" TO "anon";
GRANT ALL ON TABLE "public"."staff_workload" TO "authenticated";
GRANT ALL ON TABLE "public"."staff_workload" TO "service_role";



GRANT ALL ON TABLE "public"."system_settings" TO "anon";
GRANT ALL ON TABLE "public"."system_settings" TO "authenticated";
GRANT ALL ON TABLE "public"."system_settings" TO "service_role";



GRANT ALL ON TABLE "public"."typing_status" TO "anon";
GRANT ALL ON TABLE "public"."typing_status" TO "authenticated";
GRANT ALL ON TABLE "public"."typing_status" TO "service_role";



GRANT ALL ON TABLE "public"."units" TO "anon";
GRANT ALL ON TABLE "public"."units" TO "authenticated";
GRANT ALL ON TABLE "public"."units" TO "service_role";



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



GRANT ALL ON TABLE "public"."user_presence" TO "anon";
GRANT ALL ON TABLE "public"."user_presence" TO "authenticated";
GRANT ALL ON TABLE "public"."user_presence" TO "service_role";



GRANT ALL ON TABLE "public"."verification_activity_log" TO "anon";
GRANT ALL ON TABLE "public"."verification_activity_log" TO "authenticated";
GRANT ALL ON TABLE "public"."verification_activity_log" TO "service_role";



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







