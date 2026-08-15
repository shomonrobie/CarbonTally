


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


CREATE EXTENSION IF NOT EXISTS "pg_net" WITH SCHEMA "extensions";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pg_trgm" WITH SCHEMA "public";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE OR REPLACE FUNCTION "public"."anonymise_user"("p_user_id" "uuid", "p_actor_id" "uuid" DEFAULT NULL::"uuid", "p_reason" "text" DEFAULT 'DSAR erasure request'::"text") RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
    v_email        varchar;
    v_actor        uuid;
    v_anon_email   text;
BEGIN
    -- ---- Guard 0: target must exist --------------------------------------
    SELECT u.email INTO v_email FROM public.users u WHERE u.id = p_user_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'anonymise_user: user % not found', p_user_id;
    END IF;

    -- ---- RC2-C3: session-only actor authority ----------------------------
    -- If a real session exists, the caller-supplied p_actor_id must match it;
    -- a mismatch proves a spoof attempt and aborts (anti-escalation).
    IF auth.uid() IS NOT NULL
       AND p_actor_id IS NOT NULL
       AND p_actor_id IS DISTINCT FROM auth.uid() THEN
        RAISE EXCEPTION
            'anonymise_user: spoofed actor id — caller-supplied p_actor_id (%) does not match the authenticated session (%)',
            p_actor_id, auth.uid();
    END IF;

    -- Effective actor: the session's identity; only in service context (no
    -- session) is the advisory p_actor_id used (and then the caller is
    -- service_role anyway, which bypasses RLS).
    v_actor := coalesce(auth.uid(), p_actor_id);

    IF v_actor IS NOT NULL
       AND v_actor IS DISTINCT FROM p_user_id
       AND NOT EXISTS (SELECT 1 FROM public.staff_profiles sp
                       WHERE sp.user_id = v_actor
                         AND coalesce(sp.is_active, true)) THEN
        RAISE EXCEPTION
            'anonymise_user: actor % is neither the data subject nor active staff — erasure refused', v_actor;
    END IF;

    -- ---- Guard 2: idempotence --------------------------------------------
    IF v_email LIKE 'deleted-%@anonymised.invalid' THEN
        RAISE NOTICE 'anonymise_user: user % already anonymised — no-op', p_user_id;
        RETURN;
    END IF;

    -- ---- RC2-H1: schema-qualified hash (pgcrypto lives in `extensions`) ---
    v_anon_email := 'deleted-' || encode(extensions.sha256(p_user_id::text::bytea), 'hex')
                    || '@anonymised.invalid';

    -- ---- Scrub: users (identity core; UUID preserved) --------------------
    UPDATE public.users
       SET email          = v_anon_email,
           first_name     = 'Deleted',
           last_name      = 'User',
           password_hash  = NULL,
           is_active      = false,
           email_verified = false
     WHERE id = p_user_id;

    -- ---- Scrub: consultant_profiles (contact/address PII block) ----------
    -- Company identity fields (company_name/number, vat_number) are retained:
    -- they belong to the FIRM, not the person, and underpin billing/audit.
    UPDATE public.consultant_profiles
       SET phone         = NULL,
           website       = NULL,
           email_from    = NULL,
           support_email = NULL,
           support_phone = NULL,
           address_line1 = NULL,
           address_line2 = NULL,
           city          = NULL,
           county        = NULL,
           postcode      = NULL,
           eircode       = NULL,
           api_key       = NULL,
           webhook_url   = NULL
     WHERE user_id = p_user_id;

    -- ---- Scrub: staff_profiles (internal staff PII) ----------------------
    UPDATE public.staff_profiles
       SET first_name = 'Deleted',
           last_name  = 'User',
           email      = v_anon_email,
           is_active  = false
     WHERE user_id = p_user_id;

    -- ---- Scrub: beta_users / user_feedback (email copies) ----------------
    UPDATE public.beta_users SET email = v_anon_email WHERE user_id = p_user_id;
    UPDATE public.user_feedback SET user_email = v_anon_email WHERE user_id = p_user_id;

    RAISE NOTICE 'anonymise_user: user % anonymised (reason: %; actor: %)',
        p_user_id, p_reason, coalesce(v_actor::text, 'service-context');
END;
$$;


ALTER FUNCTION "public"."anonymise_user"("p_user_id" "uuid", "p_actor_id" "uuid", "p_reason" "text") OWNER TO "postgres";


COMMENT ON FUNCTION "public"."anonymise_user"("p_user_id" "uuid", "p_actor_id" "uuid", "p_reason" "text") IS 'GDPR anonymise-in-place erasure (A-22). RC2-C3: authority derives from auth.uid() only — caller-supplied p_actor_id is advisory and, under a real session, must match auth.uid() or the call aborts (anti-spoof / anti-escalation). RC2-H1: sha256 resolved as extensions.sha256. Hashes users.email, sets name to Deleted/User, preserves UUID and all FK/audit aggregates. SECURITY DEFINER, pinned search_path. Idempotent, transactional, irreversible by design.';



CREATE OR REPLACE FUNCTION "public"."is_org_active"("p_org" "uuid") RETURNS boolean
    LANGUAGE "sql" STABLE SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$    SELECT EXISTS (
        SELECT 1 FROM public.organizations o
         WHERE o.id = p_org AND coalesce(o.is_active, true) = true
    );$$;


ALTER FUNCTION "public"."is_org_active"("p_org" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."is_org_admin_or_owner"("p_org" "uuid") RETURNS boolean
    LANGUAGE "sql" STABLE SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$    SELECT EXISTS (
        SELECT 1 FROM public.organization_members om
         WHERE om.organization_id = p_org
           AND om.user_id = auth.uid()
           AND coalesce(om.is_active, true) = true
           AND om.role IN ('owner','admin')
    );$$;


ALTER FUNCTION "public"."is_org_admin_or_owner"("p_org" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."is_org_consultant"("p_org" "uuid") RETURNS boolean
    LANGUAGE "sql" STABLE SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$    SELECT EXISTS (
        SELECT 1
          FROM public.consultant_firm_members cfm
         WHERE cfm.user_id = auth.uid()
           AND coalesce(cfm.is_active, true) = true
           AND (
               cfm.client_access @> ARRAY[p_org]
               OR EXISTS (
                   SELECT 1 FROM public.consultant_clients cc
                    WHERE cc.consultant_id = cfm.firm_id
                      AND cc.organization_id = p_org
               )
           )
    );$$;


ALTER FUNCTION "public"."is_org_consultant"("p_org" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."is_org_member"("p_org" "uuid") RETURNS boolean
    LANGUAGE "sql" STABLE SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$    SELECT EXISTS (
        SELECT 1
          FROM public.organization_members om
          JOIN public.organizations o ON o.id = om.organization_id
         WHERE om.organization_id = p_org
           AND om.user_id = auth.uid()
           AND coalesce(om.is_active, true) = true
           AND coalesce(o.is_active, true) = true
    );$$;


ALTER FUNCTION "public"."is_org_member"("p_org" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."set_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."set_updated_at"() OWNER TO "postgres";


COMMENT ON FUNCTION "public"."set_updated_at"() IS 'Generic BEFORE UPDATE trigger function: stamps NEW.updated_at := now(). Companion to the 006 updated_at maintenance triggers. SECURITY INVOKER (runs with the updating role''s rights; the trigger fires regardless of RLS).';


SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."activity_categories" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "activity_type" "text" NOT NULL,
    "esrs_e1_category" "text",
    "issb_category" "text",
    "ghg_protocol_scope" "text",
    "ghg_protocol_category" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."activity_categories" OWNER TO "postgres";


COMMENT ON TABLE "public"."activity_categories" IS 'Activity classification reference data';



CREATE TABLE IF NOT EXISTS "public"."activity_feed" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid",
    "user_id" "uuid",
    "event_type" "text",
    "event_data" "jsonb",
    "is_read" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."activity_feed" OWNER TO "postgres";


COMMENT ON TABLE "public"."activity_feed" IS 'Activity feed';



CREATE TABLE IF NOT EXISTS "public"."activity_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "organization_id" "uuid",
    "action" character varying NOT NULL,
    "resource_type" character varying NOT NULL,
    "resource_id" "uuid",
    "details" "jsonb",
    "ip_address" character varying,
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "metadata" "jsonb",
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."activity_logs" OWNER TO "postgres";


COMMENT ON TABLE "public"."activity_logs" IS 'Activity log';



CREATE TABLE IF NOT EXISTS "public"."ai_content_history" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "report_id" "uuid",
    "prompt_type" character varying NOT NULL,
    "prompt_text" "text",
    "model_used" character varying,
    "generated_content" "text",
    "content_format" character varying,
    "tokens_used" integer,
    "processing_time_ms" integer,
    "cost" numeric,
    "user_rating" integer,
    "user_feedback" "text",
    "was_accepted" boolean,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    CONSTRAINT "ai_content_history_cost_check" CHECK ((("cost" IS NULL) OR ("cost" >= (0)::numeric))),
    CONSTRAINT "ai_content_history_processing_time_ms_check" CHECK ((("processing_time_ms" IS NULL) OR ("processing_time_ms" >= 0))),
    CONSTRAINT "ai_content_history_tokens_used_check" CHECK ((("tokens_used" IS NULL) OR ("tokens_used" >= 0))),
    CONSTRAINT "ai_content_history_user_rating_check" CHECK ((("user_rating" IS NULL) OR (("user_rating" >= 1) AND ("user_rating" <= 5))))
);


ALTER TABLE "public"."ai_content_history" OWNER TO "postgres";


COMMENT ON TABLE "public"."ai_content_history" IS 'AI generation history';



CREATE TABLE IF NOT EXISTS "public"."approval_decisions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "approval_request_id" "uuid" NOT NULL,
    "decision_by" "uuid" NOT NULL,
    "decision_at" timestamp with time zone DEFAULT "now"(),
    "decision" character varying NOT NULL,
    "reason" "text",
    "comments" "text",
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."approval_decisions" OWNER TO "postgres";


COMMENT ON TABLE "public"."approval_decisions" IS 'Approval decisions';



CREATE TABLE IF NOT EXISTS "public"."approval_requests" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "assignment_id" "uuid" NOT NULL,
    "requested_by" "uuid" NOT NULL,
    "requested_at" timestamp with time zone DEFAULT "now"(),
    "approval_type" character varying NOT NULL,
    "status" character varying,
    "priority" character varying,
    "notes" "text",
    "sla_deadline" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."approval_requests" OWNER TO "postgres";


COMMENT ON TABLE "public"."approval_requests" IS 'Approval requests';



CREATE TABLE IF NOT EXISTS "public"."assets" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "facility_id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "is_active" boolean DEFAULT true,
    "metadata" "jsonb",
    "capacity" numeric,
    "capacity_unit" character varying,
    "serial_number" character varying,
    "installation_date" "date",
    "type" character varying,
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "organization_id" "uuid",
    CONSTRAINT "assets_capacity_check" CHECK ((("capacity" IS NULL) OR ("capacity" >= (0)::numeric)))
);


ALTER TABLE "public"."assets" OWNER TO "postgres";


COMMENT ON TABLE "public"."assets" IS 'Assets within facilities';



CREATE TABLE IF NOT EXISTS "public"."audit_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
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
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."audit_logs" OWNER TO "postgres";


COMMENT ON TABLE "public"."audit_logs" IS 'Audit log';



CREATE TABLE IF NOT EXISTS "public"."audit_trail" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "action_type" character varying NOT NULL,
    "table_name" character varying NOT NULL,
    "record_id" "uuid" NOT NULL,
    "performed_by" "uuid" NOT NULL,
    "performed_at" timestamp with time zone,
    "old_data" "jsonb",
    "new_data" "jsonb",
    "changes" "jsonb",
    "ip_address" "inet",
    "user_agent" "text",
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."audit_trail" OWNER TO "postgres";


COMMENT ON TABLE "public"."audit_trail" IS 'Generic audit trail';



CREATE TABLE IF NOT EXISTS "public"."beta_access_codes" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "code" "text" NOT NULL,
    "email" "text",
    "status" "text",
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "used_at" timestamp with time zone,
    "magic_token" "text",
    "token_created_at" timestamp with time zone,
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."beta_access_codes" OWNER TO "postgres";


COMMENT ON TABLE "public"."beta_access_codes" IS 'Beta access codes';



CREATE TABLE IF NOT EXISTS "public"."beta_users" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "email" "text" NOT NULL,
    "beta_code" "text",
    "access_level" "text",
    "invited_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "last_active_at" timestamp with time zone,
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."beta_users" OWNER TO "postgres";


COMMENT ON TABLE "public"."beta_users" IS 'Beta users';



CREATE TABLE IF NOT EXISTS "public"."business_hours" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "day_of_week" character varying NOT NULL,
    "is_working_day" boolean DEFAULT true,
    "start_time" time without time zone,
    "end_time" time without time zone,
    "is_holiday" boolean DEFAULT false,
    "holiday_name" character varying,
    "timezone" character varying,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."business_hours" OWNER TO "postgres";


COMMENT ON TABLE "public"."business_hours" IS 'Business hours configuration';



CREATE TABLE IF NOT EXISTS "public"."calculation_snapshots" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "activity" character varying NOT NULL,
    "activity_type" character varying NOT NULL,
    "quantity" numeric NOT NULL,
    "quantity_unit" character varying NOT NULL,
    "co2e_multiplier" numeric NOT NULL,
    "co2e_kg" numeric NOT NULL,
    "scope" character varying,
    "date" "date" NOT NULL,
    "factor_id" "uuid" NOT NULL,
    "factor_source" character varying,
    "factor_set" character varying,
    "import_batch_id" "uuid",
    "reporting_year" integer NOT NULL,
    "methodology" character varying NOT NULL,
    "algorithm_version" character varying NOT NULL,
    "content_hash" character varying(64) NOT NULL,
    "calculated_at" timestamp with time zone DEFAULT "now"(),
    "calculated_by" character varying,
    "request_id" "uuid",
    CONSTRAINT "calculation_snapshots_co2e_kg_check" CHECK (("co2e_kg" >= (0)::numeric)),
    CONSTRAINT "calculation_snapshots_quantity_check" CHECK (("quantity" >= (0)::numeric))
);


ALTER TABLE "public"."calculation_snapshots" OWNER TO "postgres";


COMMENT ON TABLE "public"."calculation_snapshots" IS 'Immutable forensic record of every emissions calculation. Append-only; never updated or deleted (Backend v2.1 ADR-5).';



COMMENT ON COLUMN "public"."calculation_snapshots"."co2e_multiplier" IS 'Exact factor value used at calculation time (Decimal precision preserved).';



COMMENT ON COLUMN "public"."calculation_snapshots"."factor_id" IS 'emission_factors.id used. ON DELETE RESTRICT — a referenced factor can never be deleted.';



COMMENT ON COLUMN "public"."calculation_snapshots"."algorithm_version" IS 'Engine/algorithm version (Backend v2.1, e.g. 2.1.0) for methodology traceability.';



COMMENT ON COLUMN "public"."calculation_snapshots"."content_hash" IS 'SHA-256 hex digest of all calculation inputs for tamper detection and reproducibility verification.';



COMMENT ON COLUMN "public"."calculation_snapshots"."request_id" IS 'Originating API request id; correlates with audit trail and domain events.';



CREATE TABLE IF NOT EXISTS "public"."consultant_billing" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "consultant_id" "uuid" NOT NULL,
    "client_id" "uuid",
    "plan" character varying,
    "auto_extraction_limit" integer,
    "manual_extraction_credit" integer,
    "auto_extraction_used" integer,
    "manual_extraction_used" integer,
    "billing_cycle" character varying,
    "subscription_start_date" timestamp with time zone,
    "subscription_end_date" timestamp with time zone,
    "auto_extraction_price" numeric,
    "manual_extraction_price" numeric,
    "last_invoice_date" timestamp with time zone,
    "next_invoice_date" timestamp with time zone,
    "stripe_subscription_id" character varying,
    "stripe_customer_id" character varying,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "currency" character varying DEFAULT 'GBP'::character varying,
    CONSTRAINT "consultant_billing_auto_extraction_price_check" CHECK ((("auto_extraction_price" IS NULL) OR ("auto_extraction_price" >= (0)::numeric))),
    CONSTRAINT "consultant_billing_auto_extraction_used_check" CHECK ((("auto_extraction_used" IS NULL) OR ("auto_extraction_used" >= 0))),
    CONSTRAINT "consultant_billing_currency_check" CHECK ((("currency" IS NULL) OR (("currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[])))),
    CONSTRAINT "consultant_billing_currency_in_list" CHECK ((("currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[]))),
    CONSTRAINT "consultant_billing_manual_extraction_price_check" CHECK ((("manual_extraction_price" IS NULL) OR ("manual_extraction_price" >= (0)::numeric))),
    CONSTRAINT "consultant_billing_manual_extraction_used_check" CHECK ((("manual_extraction_used" IS NULL) OR ("manual_extraction_used" >= 0)))
);


ALTER TABLE "public"."consultant_billing" OWNER TO "postgres";


COMMENT ON TABLE "public"."consultant_billing" IS 'Consultant billing';



COMMENT ON COLUMN "public"."consultant_billing"."currency" IS 'ISO 4217 currency (C3, APPROVE). IN (GBP,EUR) enforced in 002 (K2).';



CREATE TABLE IF NOT EXISTS "public"."consultant_clients" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "consultant_id" "uuid" NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "client_name" character varying NOT NULL,
    "client_industry" character varying,
    "client_contact_email" character varying,
    "client_contact_name" character varying,
    "client_contact_phone" character varying,
    "status" character varying,
    "billing_plan" character varying,
    "billing_cycle" character varying,
    "notes" "text",
    "tags" "text"[],
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid"
);


ALTER TABLE "public"."consultant_clients" OWNER TO "postgres";


COMMENT ON TABLE "public"."consultant_clients" IS 'Consultant-client relationships';



CREATE TABLE IF NOT EXISTS "public"."consultant_firm_members" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "firm_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "role" character varying NOT NULL,
    "can_manage_clients" boolean DEFAULT false,
    "can_upload_documents" boolean DEFAULT false,
    "can_generate_reports" boolean DEFAULT false,
    "can_manage_team" boolean DEFAULT false,
    "client_access" "uuid"[],
    "is_active" boolean DEFAULT true,
    "invited_by" "uuid",
    "invited_at" timestamp with time zone,
    "joined_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "role_id" "uuid",
    "permissions" "jsonb"
);


ALTER TABLE "public"."consultant_firm_members" OWNER TO "postgres";


COMMENT ON TABLE "public"."consultant_firm_members" IS 'Consultant firm team members';



CREATE TABLE IF NOT EXISTS "public"."consultant_profiles" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "company_name" character varying NOT NULL,
    "company_number" character varying,
    "website" character varying,
    "phone" character varying,
    "brand_name" character varying,
    "logo_url" "text",
    "primary_color" character varying,
    "secondary_color" character varying,
    "footer_text" "text",
    "email_from" character varying,
    "default_plan" character varying,
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "address_line1" character varying,
    "address_line2" character varying,
    "city" character varying,
    "county" character varying,
    "postcode" character varying,
    "country" character varying,
    "eircode" character varying,
    "vat_number" character varying,
    "registration_region" character varying,
    "tax_region" character varying,
    "tax_rate" numeric,
    "firm_type" character varying,
    "firm_size" character varying,
    "industries_served" "text"[],
    "expertise" "text"[],
    "certifications" "text"[],
    "annual_revenue" numeric,
    "revenue_currency" character varying,
    "employee_count" integer,
    "founded_year" integer,
    "partner_since" "date",
    "partner_status" character varying,
    "partner_tier" character varying,
    "commission_rate" numeric,
    "referral_code" character varying,
    "co_branding_enabled" boolean DEFAULT false,
    "api_key" character varying,
    "webhook_url" "text",
    "client_portal_url" "text",
    "support_hours" character varying,
    "support_phone" character varying,
    "support_email" character varying,
    CONSTRAINT "consultant_profiles_country_check" CHECK ((("country" IS NULL) OR (("country")::"text" = ANY ((ARRAY['GB'::character varying, 'IE'::character varying])::"text"[])))),
    CONSTRAINT "consultant_profiles_country_in_list" CHECK ((("country")::"text" = ANY ((ARRAY['GB'::character varying, 'IE'::character varying])::"text"[]))),
    CONSTRAINT "consultant_profiles_revenue_currency_check" CHECK ((("revenue_currency" IS NULL) OR (("revenue_currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[])))),
    CONSTRAINT "consultant_profiles_revenue_currency_in_list" CHECK ((("revenue_currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[])))
);


ALTER TABLE "public"."consultant_profiles" OWNER TO "postgres";


COMMENT ON TABLE "public"."consultant_profiles" IS 'Consultant firm profiles';



CREATE TABLE IF NOT EXISTS "public"."consultant_tasks" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "consultant_id" "uuid" NOT NULL,
    "client_id" "uuid",
    "task_title" character varying NOT NULL,
    "task_description" "text",
    "task_type" character varying,
    "priority" character varying,
    "status" character varying,
    "assigned_to" "uuid",
    "assigned_by" "uuid",
    "due_date" timestamp with time zone,
    "completed_at" timestamp with time zone,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."consultant_tasks" OWNER TO "postgres";


COMMENT ON TABLE "public"."consultant_tasks" IS 'Consultant tasks';



CREATE TABLE IF NOT EXISTS "public"."conversation_activity_log" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "conversation_id" "uuid",
    "user_id" "uuid",
    "action_type" "text",
    "action_details" "jsonb",
    "ip_address" "text",
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."conversation_activity_log" OWNER TO "postgres";


COMMENT ON TABLE "public"."conversation_activity_log" IS 'Conversation activity log';



CREATE TABLE IF NOT EXISTS "public"."conversation_participants" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "conversation_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "joined_at" timestamp with time zone DEFAULT "now"(),
    "last_read_at" timestamp with time zone,
    "is_active" boolean DEFAULT true,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."conversation_participants" OWNER TO "postgres";


COMMENT ON TABLE "public"."conversation_participants" IS 'Conversation participants';



CREATE TABLE IF NOT EXISTS "public"."conversations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "staff_id" "uuid",
    "customer_id" "uuid",
    "subject" "text",
    "status" "text",
    "last_message_at" timestamp with time zone,
    "created_by" "uuid",
    "closed_by" "uuid",
    "closed_at" timestamp with time zone,
    "is_urgent" boolean DEFAULT false,
    "priority" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "read_by" "uuid"[],
    "unread_count" integer DEFAULT 0,
    "participant_count" integer DEFAULT 0
);


ALTER TABLE "public"."conversations" OWNER TO "postgres";


COMMENT ON TABLE "public"."conversations" IS 'Conversation threads';



CREATE TABLE IF NOT EXISTS "public"."customer_communication" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "staff_id" "uuid" NOT NULL,
    "communication_type" character varying NOT NULL,
    "subject" character varying,
    "content" "text" NOT NULL,
    "is_internal" boolean DEFAULT false,
    "sent_by" "uuid" NOT NULL,
    "sent_at" timestamp with time zone,
    "is_read" boolean DEFAULT false,
    "read_at" timestamp with time zone,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."customer_communication" OWNER TO "postgres";


COMMENT ON TABLE "public"."customer_communication" IS 'Customer communication records';



CREATE TABLE IF NOT EXISTS "public"."customer_documents" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "organization_member_id" "uuid" NOT NULL,
    "asset_id" "uuid",
    "file_name" "text" NOT NULL,
    "file_url" "text" NOT NULL,
    "file_type" "text" NOT NULL,
    "upload_date" timestamp with time zone DEFAULT "now"(),
    "status" "text" DEFAULT 'uploaded'::"text" NOT NULL,
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
    "processing_queue_id" "uuid",
    "supplier_id" "uuid",
    "product_category_id" "uuid",
    "processing_method" character varying,
    "processing_status" character varying,
    "processing_completed_at" timestamp with time zone,
    "extracted_data" "jsonb",
    "mapped_data" "jsonb",
    "calculated_emissions_kg_co2e" numeric,
    "updated_by" "uuid",
    "uploaded_by" "uuid",
    "processing_started_at" timestamp with time zone,
    "file_checksum" "text",
    CONSTRAINT "customer_documents_calculated_emissions_kg_co2e_check" CHECK ((("calculated_emissions_kg_co2e" IS NULL) OR ("calculated_emissions_kg_co2e" >= (0)::numeric))),
    CONSTRAINT "customer_documents_confidence_score_check" CHECK ((("confidence_score" IS NULL) OR (("confidence_score" >= (0)::double precision) AND ("confidence_score" <= (100)::double precision)))),
    CONSTRAINT "customer_documents_status_check" CHECK (("status" = ANY (ARRAY['uploaded'::"text", 'pending'::"text", 'processing'::"text", 'processed'::"text", 'manual_review'::"text", 'verified'::"text", 'approved'::"text", 'rejected'::"text", 'failed'::"text"])))
);


ALTER TABLE "public"."customer_documents" OWNER TO "postgres";


COMMENT ON TABLE "public"."customer_documents" IS 'Customer document storage';



COMMENT ON COLUMN "public"."customer_documents"."file_checksum" IS 'SHA-256 hex of uploaded file (C6, APPROVE). NOT unique in v1.0.';



CREATE TABLE IF NOT EXISTS "public"."customer_review_log" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "file_id" "uuid",
    "organization_id" "uuid",
    "user_id" "uuid",
    "status" character varying NOT NULL,
    "notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."customer_review_log" OWNER TO "postgres";


COMMENT ON TABLE "public"."customer_review_log" IS 'Customer review log';



CREATE TABLE IF NOT EXISTS "public"."customer_subscriptions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "plan" character varying NOT NULL,
    "status" character varying,
    "ai_extraction_limit" integer,
    "ai_extraction_used" integer,
    "batch_upload_limit" integer,
    "batch_upload_per_day" integer,
    "manual_extraction_pages_included" integer,
    "manual_extraction_pages_used" integer,
    "price_per_ai_extra" numeric,
    "price_per_manual_page" numeric,
    "currency" character varying,
    "features" "jsonb",
    "stripe_subscription_id" character varying,
    "stripe_customer_id" character varying,
    "stripe_price_id" character varying,
    "billing_period_start" "date",
    "billing_period_end" "date",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "updated_by" "uuid",
    "cancelled_at" timestamp with time zone,
    "cancelled_by" "uuid",
    CONSTRAINT "customer_subscriptions_ai_extraction_used_check" CHECK ((("ai_extraction_used" IS NULL) OR ("ai_extraction_used" >= 0))),
    CONSTRAINT "customer_subscriptions_currency_check" CHECK ((("currency" IS NULL) OR (("currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[])))),
    CONSTRAINT "customer_subscriptions_currency_in_list" CHECK ((("currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[]))),
    CONSTRAINT "customer_subscriptions_manual_extraction_pages_used_check" CHECK ((("manual_extraction_pages_used" IS NULL) OR ("manual_extraction_pages_used" >= 0))),
    CONSTRAINT "customer_subscriptions_price_per_ai_extra_check" CHECK ((("price_per_ai_extra" IS NULL) OR ("price_per_ai_extra" >= (0)::numeric))),
    CONSTRAINT "customer_subscriptions_price_per_manual_page_check" CHECK ((("price_per_manual_page" IS NULL) OR ("price_per_manual_page" >= (0)::numeric))),
    CONSTRAINT "customer_subscriptions_status_check" CHECK ((("status")::"text" = ANY ((ARRAY['trialing'::character varying, 'active'::character varying, 'past_due'::character varying, 'paused'::character varying, 'cancelled'::character varying, 'expired'::character varying, 'incomplete'::character varying, 'incomplete_expired'::character varying, 'unpaid'::character varying])::"text"[])))
);


ALTER TABLE "public"."customer_subscriptions" OWNER TO "postgres";


COMMENT ON TABLE "public"."customer_subscriptions" IS 'Customer subscriptions';



CREATE TABLE IF NOT EXISTS "public"."customer_verifications" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "customer_document_id" "uuid",
    "organization_id" "uuid" NOT NULL,
    "customer_member_id" "uuid",
    "status" "text",
    "notes" "text",
    "submitted_at" timestamp with time zone,
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
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."customer_verifications" OWNER TO "postgres";


COMMENT ON TABLE "public"."customer_verifications" IS 'Customer verifications';



CREATE TABLE IF NOT EXISTS "public"."dashboard_metrics" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "metric_type" character varying NOT NULL,
    "metric_name" character varying NOT NULL,
    "metric_value" "jsonb" NOT NULL,
    "period" character varying,
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."dashboard_metrics" OWNER TO "postgres";


COMMENT ON TABLE "public"."dashboard_metrics" IS 'Dashboard metrics cache';



CREATE TABLE IF NOT EXISTS "public"."document_activity_log" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "file_id" "uuid",
    "organization_id" "uuid",
    "user_id" "uuid",
    "action" character varying NOT NULL,
    "details" "jsonb",
    "ip_address" character varying,
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."document_activity_log" OWNER TO "postgres";


COMMENT ON TABLE "public"."document_activity_log" IS 'Document activity log';



CREATE TABLE IF NOT EXISTS "public"."document_processing_queue" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "customer_document_id" "uuid",
    "processing_type" character varying NOT NULL,
    "status" character varying DEFAULT 'pending'::character varying,
    "file_name" character varying NOT NULL,
    "file_url" "text" NOT NULL,
    "file_size_bytes" bigint,
    "file_type" character varying,
    "page_count" integer,
    "ai_extraction_result" "jsonb",
    "ai_confidence_score" numeric,
    "ai_extraction_method" character varying,
    "ai_extracted_at" timestamp with time zone,
    "ai_processing_time_ms" integer,
    "ai_mapped_facility_id" "uuid",
    "ai_mapped_asset_id" "uuid",
    "ai_mapped_supplier_id" "uuid",
    "ai_mapping_confidence" numeric,
    "ai_mapped_document_type_code" character varying,
    "manual_requested_by" "uuid",
    "manual_requested_at" timestamp with time zone,
    "manual_assigned_to" "uuid",
    "manual_assigned_by" "uuid",
    "manual_assigned_at" timestamp with time zone,
    "manual_extraction_result" "jsonb",
    "manual_extracted_by" "uuid",
    "manual_extracted_at" timestamp with time zone,
    "manual_notes" "text",
    "qc_required" boolean DEFAULT false NOT NULL,
    "qc_by" "uuid",
    "qc_at" timestamp with time zone,
    "qc_notes" "text",
    "qc_approved" boolean,
    "customer_reviewed_by" "uuid",
    "customer_reviewed_at" timestamp with time zone,
    "customer_approved" boolean DEFAULT false NOT NULL,
    "customer_rejection_reason" "text",
    "customer_notes" "text",
    "calculated_emissions_kg_co2e" numeric,
    "emission_factor_used" "uuid",
    "emission_calculation_method" character varying,
    "batch_id" "uuid",
    "batch_sequence" integer,
    "processing_cost" numeric,
    "billing_currency" character varying,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "updated_by" "uuid",
    "completed_at" timestamp with time zone,
    "metadata" "jsonb",
    "workflow_error_count" integer DEFAULT 0,
    "workflow_next_retry_at" timestamp with time zone,
    CONSTRAINT "document_processing_queue_ai_confidence_score_check" CHECK ((("ai_confidence_score" IS NULL) OR (("ai_confidence_score" >= (0)::numeric) AND ("ai_confidence_score" <= (100)::numeric)))),
    CONSTRAINT "document_processing_queue_ai_mapping_confidence_check" CHECK ((("ai_mapping_confidence" IS NULL) OR (("ai_mapping_confidence" >= (0)::numeric) AND ("ai_mapping_confidence" <= (100)::numeric)))),
    CONSTRAINT "document_processing_queue_billing_currency_check" CHECK ((("billing_currency" IS NULL) OR (("billing_currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[])))),
    CONSTRAINT "document_processing_queue_billing_currency_in_list" CHECK ((("billing_currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[]))),
    CONSTRAINT "document_processing_queue_calculated_emissions_kg_co2e_check" CHECK ((("calculated_emissions_kg_co2e" IS NULL) OR ("calculated_emissions_kg_co2e" >= (0)::numeric))),
    CONSTRAINT "document_processing_queue_file_size_bytes_check" CHECK ((("file_size_bytes" IS NULL) OR ("file_size_bytes" >= 0))),
    CONSTRAINT "document_processing_queue_page_count_check" CHECK ((("page_count" IS NULL) OR ("page_count" >= 0))),
    CONSTRAINT "document_processing_queue_processing_cost_check" CHECK ((("processing_cost" IS NULL) OR ("processing_cost" >= (0)::numeric))),
    CONSTRAINT "document_processing_queue_status_check" CHECK ((("status")::"text" = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'ai_extracted'::character varying, 'manual_review'::character varying, 'manual_extraction'::character varying, 'qc'::character varying, 'customer_review'::character varying, 'approved'::character varying, 'rejected'::character varying, 'completed'::character varying, 'failed'::character varying])::"text"[])))
);


ALTER TABLE "public"."document_processing_queue" OWNER TO "postgres";


COMMENT ON TABLE "public"."document_processing_queue" IS 'Document processing queue';



COMMENT ON COLUMN "public"."document_processing_queue"."workflow_error_count" IS 'Count of failed workflow transitions for this document (retry cap).';



COMMENT ON COLUMN "public"."document_processing_queue"."workflow_next_retry_at" IS 'Earliest timestamp at which a retry of this workflow may be attempted.';



CREATE TABLE IF NOT EXISTS "public"."document_type_categories" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "code" character varying NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "category_group" character varying,
    "default_priority" integer DEFAULT 0,
    "requires_facility" boolean DEFAULT false,
    "requires_asset" boolean DEFAULT false,
    "requires_supplier" boolean DEFAULT false,
    "requires_date_range" boolean DEFAULT false,
    "default_defra_activity_type" character varying,
    "default_scope" character varying,
    "is_active" boolean DEFAULT true,
    "is_system" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."document_type_categories" OWNER TO "postgres";


COMMENT ON TABLE "public"."document_type_categories" IS 'Document type classification reference';



CREATE TABLE IF NOT EXISTS "public"."document_types" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "code" "text" NOT NULL,
    "name" "text" NOT NULL,
    "category" "text" NOT NULL,
    "description" "text",
    "file_extensions" "text"[],
    "is_active" boolean DEFAULT true,
    "requires_asset" boolean DEFAULT false,
    "requires_date_range" boolean DEFAULT false,
    "requires_facility" boolean DEFAULT false,
    "priority" integer DEFAULT 0,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."document_types" OWNER TO "postgres";


COMMENT ON TABLE "public"."document_types" IS 'Document type reference';



CREATE TABLE IF NOT EXISTS "public"."domain_events" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "event_type" character varying NOT NULL,
    "occurred_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "correlation_id" "uuid" NOT NULL,
    "aggregate_id" "uuid" NOT NULL,
    "aggregate_type" character varying NOT NULL,
    "payload" "jsonb" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."domain_events" OWNER TO "postgres";


COMMENT ON TABLE "public"."domain_events" IS 'Append-only domain event store. Written by the EventBus, read by audit and replay (Backend v2.1 §14).';



COMMENT ON COLUMN "public"."domain_events"."correlation_id" IS 'Links every event triggered by a single API request (equals the request id).';



COMMENT ON COLUMN "public"."domain_events"."payload" IS 'Typed event fields serialized as JSON (matches the concrete DomainEvent subclass).';



CREATE TABLE IF NOT EXISTS "public"."draft_entries" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "file_id" "uuid",
    "organization_id" "uuid",
    "user_id" "uuid",
    "data" "jsonb",
    "progress" integer,
    "sections_completed" "jsonb",
    "last_updated" timestamp with time zone DEFAULT "now"(),
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "draft_entries_progress_check" CHECK ((("progress" IS NULL) OR (("progress" >= 0) AND ("progress" <= 100))))
);


ALTER TABLE "public"."draft_entries" OWNER TO "postgres";


COMMENT ON TABLE "public"."draft_entries" IS 'Draft entries';



CREATE TABLE IF NOT EXISTS "public"."email_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "email" "text" NOT NULL,
    "type" "text" NOT NULL,
    "status" "text" NOT NULL,
    "error_message" "text",
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."email_logs" OWNER TO "postgres";


COMMENT ON TABLE "public"."email_logs" IS 'Email logs';



CREATE TABLE IF NOT EXISTS "public"."email_templates" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" character varying NOT NULL,
    "subject" character varying NOT NULL,
    "body" "text" NOT NULL,
    "type" character varying NOT NULL,
    "variables" "text"[],
    "is_active" boolean DEFAULT true,
    "description" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_by" "uuid"
);


ALTER TABLE "public"."email_templates" OWNER TO "postgres";


COMMENT ON TABLE "public"."email_templates" IS 'Email template reference';



CREATE TABLE IF NOT EXISTS "public"."emission_factors" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "reporting_year" integer NOT NULL,
    "activity_type" character varying NOT NULL,
    "co2e_multiplier" numeric NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "unit" "text",
    "scope" "text",
    "factor_source" "text",
    "factor_set" "text",
    "country" character varying,
    "region_deprecated" character varying,
    "import_batch_id" "uuid",
    CONSTRAINT "emission_factors_co2e_multiplier_check" CHECK (("co2e_multiplier" >= (0)::numeric)),
    CONSTRAINT "emission_factors_co2e_multiplier_nonneg" CHECK (("co2e_multiplier" >= (0)::numeric)),
    CONSTRAINT "emission_factors_country_check" CHECK ((("country")::"text" = ANY ((ARRAY['GB'::character varying, 'IE'::character varying])::"text"[]))),
    CONSTRAINT "emission_factors_country_in_list" CHECK ((("country")::"text" = ANY ((ARRAY['GB'::character varying, 'IE'::character varying])::"text"[])))
);


ALTER TABLE "public"."emission_factors" OWNER TO "postgres";


COMMENT ON TABLE "public"."emission_factors" IS 'Emission factors reference';



COMMENT ON COLUMN "public"."emission_factors"."unit" IS 'Unit the co2e_multiplier applies to (C4, APPROVE). Free text by design; NOT an FK.';



COMMENT ON COLUMN "public"."emission_factors"."scope" IS 'GHG Protocol scope label (C4, APPROVE).';



COMMENT ON COLUMN "public"."emission_factors"."factor_source" IS 'Source authority: DEFRA-DESNZ, later SEAI/EPA (C4, APPROVE).';



COMMENT ON COLUMN "public"."emission_factors"."factor_set" IS 'Factor vintage/set aligned with system_settings.default_emission_factor_set (C4, APPROVE).';



COMMENT ON COLUMN "public"."emission_factors"."country" IS 'Jurisdiction: GB or IE (C4, APPROVE). Feeds the RC2 factor natural key (002 H3).';



COMMENT ON COLUMN "public"."emission_factors"."region_deprecated" IS 'Legacy free-text region folded into country during C4 backfill and retired non-destructively (C4, APPROVE). Do not read; drop after consumer audit.';



COMMENT ON COLUMN "public"."emission_factors"."import_batch_id" IS 'Provenance link to the import_batches row that created this factor (Backend v2.1 §17).';



CREATE TABLE IF NOT EXISTS "public"."emissions_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "asset_id" "uuid",
    "emission_factor_id" "uuid",
    "start_date" "date" NOT NULL,
    "end_date" "date" NOT NULL,
    "raw_quantity" numeric NOT NULL,
    "calculated_kg_co2e" numeric NOT NULL,
    "created_by_user_id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "metadata" "jsonb",
    "file_id" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "customer_document_id" "uuid",
    "organization_member_id" "uuid",
    "supplier_id" "uuid",
    "product_category_id" "uuid",
    "data_source" character varying,
    "confidence_score" numeric,
    "verified_by" "uuid",
    "verified_at" timestamp with time zone,
    "updated_by" "uuid",
    "unit" "text",
    "scope" "text",
    "snapshot_id" "uuid",
    CONSTRAINT "emissions_logs_calculated_kg_co2e_check" CHECK (("calculated_kg_co2e" >= (0)::numeric)),
    CONSTRAINT "emissions_logs_calculated_kg_co2e_nonneg" CHECK (("calculated_kg_co2e" >= (0)::numeric)),
    CONSTRAINT "emissions_logs_confidence_score_check" CHECK ((("confidence_score" IS NULL) OR (("confidence_score" >= (0)::numeric) AND ("confidence_score" <= (100)::numeric)))),
    CONSTRAINT "emissions_logs_raw_quantity_check" CHECK (("raw_quantity" >= (0)::numeric)),
    CONSTRAINT "emissions_logs_raw_quantity_nonneg" CHECK (("raw_quantity" >= (0)::numeric))
);


ALTER TABLE "public"."emissions_logs" OWNER TO "postgres";


COMMENT ON TABLE "public"."emissions_logs" IS 'Emission records';



COMMENT ON COLUMN "public"."emissions_logs"."unit" IS 'Unit of raw_quantity, backfilled via factor join. Deliberately not an FK (RC2-H2).';



COMMENT ON COLUMN "public"."emissions_logs"."scope" IS 'GHG Protocol scope label (C5, APPROVE).';



COMMENT ON COLUMN "public"."emissions_logs"."snapshot_id" IS 'Optional link to the immutable calculation_snapshots forensic record (Backend v2.1 §13).';



CREATE TABLE IF NOT EXISTS "public"."export_history" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid",
    "user_id" "uuid",
    "file_name" character varying,
    "format" character varying,
    "filters" "jsonb",
    "record_count" integer,
    "status" character varying,
    "file_url" "text",
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."export_history" OWNER TO "postgres";


COMMENT ON TABLE "public"."export_history" IS 'Export history';



CREATE TABLE IF NOT EXISTS "public"."facilities" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "postcode" character varying,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "is_active" boolean DEFAULT true,
    "metadata" "jsonb",
    "latitude" numeric,
    "longitude" numeric,
    "type" character varying,
    "address_line1" character varying,
    "address_line2" character varying,
    "city" character varying,
    "county" character varying,
    "country" character varying,
    "region" character varying,
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "eircode" character varying,
    "meter_mpan_mprn" character varying,
    CONSTRAINT "facilities_country_check" CHECK ((("country" IS NULL) OR (("country")::"text" = ANY ((ARRAY['GB'::character varying, 'IE'::character varying])::"text"[])))),
    CONSTRAINT "facilities_country_in_list" CHECK ((("country")::"text" = ANY ((ARRAY['GB'::character varying, 'IE'::character varying])::"text"[]))),
    CONSTRAINT "facilities_postcode_or_eircode_check" CHECK ((("postcode" IS NOT NULL) OR ("eircode" IS NOT NULL)))
);


ALTER TABLE "public"."facilities" OWNER TO "postgres";


COMMENT ON TABLE "public"."facilities" IS 'Organization facilities/locations';



COMMENT ON COLUMN "public"."facilities"."eircode" IS 'Irish Eircode (C1, APPROVE). Pairwise presence with postcode is enforced by facilities_postcode_or_eircode_check (002 conformance). API-layer format validation (K9 rejected).';



COMMENT ON COLUMN "public"."facilities"."meter_mpan_mprn" IS 'Meter MPAN/MPRN free format (C9, APPROVE). API normalisation.';



CREATE TABLE IF NOT EXISTS "public"."factor_aliases" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid",
    "alias_text" character varying NOT NULL,
    "target_activity_type" character varying NOT NULL,
    "target_provider_key" character varying NOT NULL,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."factor_aliases" OWNER TO "postgres";


COMMENT ON TABLE "public"."factor_aliases" IS 'Organisation-specific and global activity aliases for factor matching (Backend v2.1 §11.3).';



COMMENT ON COLUMN "public"."factor_aliases"."organization_id" IS 'NULL = global alias; otherwise organisation-scoped.';



COMMENT ON COLUMN "public"."factor_aliases"."target_activity_type" IS 'RC2 activity_type the alias resolves to (e.g. Fuels > Liquid fuels > Diesel ...).';



COMMENT ON COLUMN "public"."factor_aliases"."target_provider_key" IS 'Provider the target factor belongs to (defra, seai, ...).';



CREATE TABLE IF NOT EXISTS "public"."file_attachments" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "message_id" "uuid",
    "conversation_id" "uuid",
    "organization_id" "uuid" NOT NULL,
    "file_name" "text" NOT NULL,
    "file_url" "text" NOT NULL,
    "file_size" bigint,
    "file_type" "text",
    "mime_type" "text",
    "uploaded_by" "uuid",
    "uploaded_at" timestamp with time zone DEFAULT "now"(),
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "file_attachments_file_size_check" CHECK (("file_size" >= 0))
);


ALTER TABLE "public"."file_attachments" OWNER TO "postgres";


COMMENT ON TABLE "public"."file_attachments" IS 'Message file attachments';



CREATE TABLE IF NOT EXISTS "public"."glossary" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
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


COMMENT ON TABLE "public"."glossary" IS 'Glossary of terms';



CREATE TABLE IF NOT EXISTS "public"."import_batches" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "provider_key" character varying NOT NULL,
    "provider_version" character varying NOT NULL,
    "source_file" "text" NOT NULL,
    "source_checksum" character varying(64) NOT NULL,
    "reporting_year" integer NOT NULL,
    "status" character varying DEFAULT 'pending'::character varying NOT NULL,
    "rows_total" integer DEFAULT 0,
    "rows_imported" integer DEFAULT 0,
    "rows_skipped" integer DEFAULT 0,
    "rows_duplicate" integer DEFAULT 0,
    "errors" "jsonb",
    "is_active" boolean DEFAULT false NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "rolled_back_from" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "import_batches_status_check" CHECK ((("status")::"text" = ANY ((ARRAY['pending'::character varying, 'importing'::character varying, 'completed'::character varying, 'failed'::character varying, 'rolled_back'::character varying])::"text"[])))
);


ALTER TABLE "public"."import_batches" OWNER TO "postgres";


COMMENT ON TABLE "public"."import_batches" IS 'Versioned import batches for emission-factor provider datasets (Backend v2.1, Import Platform).';



COMMENT ON COLUMN "public"."import_batches"."provider_key" IS 'Provider identifier: defra, seai, epa, ademe, ipcc, custom.';



COMMENT ON COLUMN "public"."import_batches"."provider_version" IS 'Provider-defined dataset version, e.g. 2025.1 (DEFRA), 2024 (SEAI).';



COMMENT ON COLUMN "public"."import_batches"."source_checksum" IS 'SHA-256 hex digest of the publisher source file for independent verification.';



COMMENT ON COLUMN "public"."import_batches"."status" IS 'pending → importing → completed | failed | rolled_back.';



COMMENT ON COLUMN "public"."import_batches"."is_active" IS 'At most one batch per (provider_key, reporting_year) is active; inactive batches remain for provenance.';



COMMENT ON COLUMN "public"."import_batches"."rolled_back_from" IS 'Replacement batch id when this batch was rolled back (non-destructive rollback chain).';



CREATE TABLE IF NOT EXISTS "public"."login_history" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "staff_id" "uuid" NOT NULL,
    "login_at" timestamp with time zone,
    "logout_at" timestamp with time zone,
    "ip_address" "inet",
    "user_agent" "text",
    "session_id" "uuid",
    "is_successful" boolean,
    "failure_reason" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."login_history" OWNER TO "postgres";


COMMENT ON TABLE "public"."login_history" IS 'Login history';



CREATE TABLE IF NOT EXISTS "public"."manual_extraction_batches" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "batch_name" character varying NOT NULL,
    "batch_description" "text",
    "total_documents" integer NOT NULL,
    "total_pages" integer NOT NULL,
    "total_cost" numeric NOT NULL,
    "price_per_page" numeric,
    "currency" character varying,
    "status" character varying,
    "estimated_completion_date" timestamp with time zone,
    "actual_completion_date" timestamp with time zone,
    "sla_deadline" timestamp with time zone,
    "sla_breached" boolean DEFAULT false,
    "assigned_to" "uuid",
    "assigned_by" "uuid",
    "assigned_at" timestamp with time zone,
    "qc_by" "uuid",
    "qc_at" timestamp with time zone,
    "qc_notes" "text",
    "qc_approved" boolean,
    "customer_notes" "text",
    "staff_notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "updated_by" "uuid",
    "completed_by" "uuid",
    "completed_at" timestamp with time zone,
    CONSTRAINT "manual_extraction_batches_currency_check" CHECK ((("currency" IS NULL) OR (("currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[])))),
    CONSTRAINT "manual_extraction_batches_currency_in_list" CHECK ((("currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[]))),
    CONSTRAINT "manual_extraction_batches_price_per_page_check" CHECK ((("price_per_page" IS NULL) OR ("price_per_page" >= (0)::numeric))),
    CONSTRAINT "manual_extraction_batches_total_cost_check" CHECK (("total_cost" >= (0)::numeric)),
    CONSTRAINT "manual_extraction_batches_total_documents_check" CHECK (("total_documents" >= 0)),
    CONSTRAINT "manual_extraction_batches_total_pages_check" CHECK (("total_pages" >= 0))
);


ALTER TABLE "public"."manual_extraction_batches" OWNER TO "postgres";


COMMENT ON TABLE "public"."manual_extraction_batches" IS 'Manual extraction batches';



CREATE TABLE IF NOT EXISTS "public"."manual_extraction_items" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "batch_id" "uuid" NOT NULL,
    "document_processing_queue_id" "uuid",
    "file_name" character varying NOT NULL,
    "file_url" "text" NOT NULL,
    "page_count" integer NOT NULL,
    "document_type" character varying,
    "status" character varying,
    "extracted_data" "jsonb",
    "mapped_data" "jsonb",
    "mapped_facility_id" "uuid",
    "mapped_asset_id" "uuid",
    "mapped_supplier_id" "uuid",
    "calculated_emissions_kg_co2e" numeric,
    "emission_factor_used" "uuid",
    "extracted_by" "uuid",
    "extracted_at" timestamp with time zone,
    "qc_by" "uuid",
    "qc_at" timestamp with time zone,
    "qc_notes" "text",
    "quality_score" integer,
    "customer_reviewed_by" "uuid",
    "customer_reviewed_at" timestamp with time zone,
    "customer_approved" boolean,
    "customer_rejection_reason" "text",
    "customer_notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "manual_extraction_items_calculated_emissions_kg_co2e_check" CHECK ((("calculated_emissions_kg_co2e" IS NULL) OR ("calculated_emissions_kg_co2e" >= (0)::numeric))),
    CONSTRAINT "manual_extraction_items_page_count_check" CHECK (("page_count" >= 0)),
    CONSTRAINT "manual_extraction_items_quality_score_check" CHECK ((("quality_score" IS NULL) OR (("quality_score" >= 0) AND ("quality_score" <= 100))))
);


ALTER TABLE "public"."manual_extraction_items" OWNER TO "postgres";


COMMENT ON TABLE "public"."manual_extraction_items" IS 'Manual extraction items';



CREATE TABLE IF NOT EXISTS "public"."manual_review_queue" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "file_url" "text" NOT NULL,
    "file_name" "text" NOT NULL,
    "file_type" "text" NOT NULL,
    "data_type" "text" NOT NULL,
    "status" "text" NOT NULL,
    "auto_extraction_result" "jsonb",
    "manual_extraction_result" "jsonb",
    "assigned_to" "uuid",
    "priority" integer,
    "customer_notes" "text",
    "staff_notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "completed_at" timestamp with time zone,
    "estimated_completion_hours" integer,
    "batch_id" "uuid",
    "assigned_by" "uuid",
    "started_at" timestamp with time zone,
    "completed_by" "uuid",
    "data_entry" "jsonb",
    "review_time_seconds" integer,
    "priority_score" integer,
    "sla_deadline" timestamp with time zone,
    "sla_breached" boolean DEFAULT false,
    "escalation_level" integer,
    "customer_notified_at" timestamp with time zone,
    "customer_responded_at" timestamp with time zone,
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "customer_document_id" "uuid",
    "entity_id" "uuid"
);


ALTER TABLE "public"."manual_review_queue" OWNER TO "postgres";


COMMENT ON TABLE "public"."manual_review_queue" IS 'Manual review queue items';



COMMENT ON COLUMN "public"."manual_review_queue"."entity_id" IS 'Processing Entity performing this Work Item (NULL = CarbonTally internal; ADR-V3-001 Q5). ON DELETE RESTRICT preserves attribution.';



CREATE TABLE IF NOT EXISTS "public"."message_activity_log" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "message_id" "uuid",
    "conversation_id" "uuid",
    "user_id" "uuid",
    "action_type" "text",
    "action_details" "jsonb",
    "ip_address" "text",
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."message_activity_log" OWNER TO "postgres";


COMMENT ON TABLE "public"."message_activity_log" IS 'Message activity log';



CREATE TABLE IF NOT EXISTS "public"."messages" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "conversation_id" "uuid",
    "sender_id" "uuid",
    "receiver_id" "uuid",
    "organization_id" "uuid" NOT NULL,
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
    "read_by" "uuid"[],
    "read_count" integer DEFAULT 0,
    "last_read_at" timestamp with time zone,
    "attachments" "jsonb",
    "has_attachments" boolean DEFAULT false
);


ALTER TABLE "public"."messages" OWNER TO "postgres";


COMMENT ON TABLE "public"."messages" IS 'Messages within conversations';



CREATE TABLE IF NOT EXISTS "public"."notification_delivery" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "notification_id" "uuid" NOT NULL,
    "channel" character varying NOT NULL,
    "status" character varying,
    "sent_at" timestamp with time zone,
    "delivered_at" timestamp with time zone,
    "opened_at" timestamp with time zone,
    "error_message" "text",
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."notification_delivery" OWNER TO "postgres";


COMMENT ON TABLE "public"."notification_delivery" IS 'Notification delivery tracking';



CREATE TABLE IF NOT EXISTS "public"."notification_templates" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "template_type" character varying NOT NULL,
    "name" character varying NOT NULL,
    "subject" character varying NOT NULL,
    "body" "text" NOT NULL,
    "variables" "jsonb",
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_by" "uuid"
);


ALTER TABLE "public"."notification_templates" OWNER TO "postgres";


COMMENT ON TABLE "public"."notification_templates" IS 'Notification template reference';



CREATE TABLE IF NOT EXISTS "public"."notifications" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "recipient_type" character varying NOT NULL,
    "recipient_id" "uuid" NOT NULL,
    "notification_type" character varying NOT NULL,
    "title" character varying NOT NULL,
    "message" "text" NOT NULL,
    "priority" character varying,
    "link" "text",
    "metadata" "jsonb",
    "is_read" boolean DEFAULT false,
    "read_at" timestamp with time zone,
    "is_dismissed" boolean DEFAULT false,
    "dismissed_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."notifications" OWNER TO "postgres";


COMMENT ON TABLE "public"."notifications" IS 'User notifications';



CREATE TABLE IF NOT EXISTS "public"."organization_files" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "path" "text" NOT NULL,
    "size_bytes" bigint NOT NULL,
    "file_type" character varying NOT NULL,
    "mime_type" character varying NOT NULL,
    "bucket" character varying,
    "uploaded_by" "uuid",
    "uploaded_at" timestamp with time zone DEFAULT "now"(),
    "last_accessed" timestamp with time zone,
    "access_count" integer DEFAULT 0,
    "is_active" boolean DEFAULT true,
    "deleted_at" timestamp with time zone,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "status" character varying,
    "status_updated_at" timestamp with time zone,
    "processing_started_at" timestamp with time zone,
    "review_ready_at" timestamp with time zone,
    "approved_at" timestamp with time zone,
    "rejected_at" timestamp with time zone,
    "rejection_reason" "text",
    "reviewed_by" "uuid",
    "approved_by" "uuid",
    CONSTRAINT "organization_files_size_bytes_check" CHECK (("size_bytes" >= 0))
);


ALTER TABLE "public"."organization_files" OWNER TO "postgres";


COMMENT ON TABLE "public"."organization_files" IS 'Organization file storage';



CREATE TABLE IF NOT EXISTS "public"."organization_members" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "role" character varying NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "is_active" boolean DEFAULT true,
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "organization_members_role_check" CHECK ((("role")::"text" = ANY ((ARRAY['owner'::character varying, 'admin'::character varying, 'member'::character varying, 'viewer'::character varying])::"text"[])))
);


ALTER TABLE "public"."organization_members" OWNER TO "postgres";


COMMENT ON TABLE "public"."organization_members" IS 'Organization membership';



CREATE TABLE IF NOT EXISTS "public"."organization_metadata" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "total_employees" integer,
    "full_time_employees" integer,
    "part_time_employees" integer,
    "contract_employees" integer,
    "average_employees" integer,
    "annual_revenue" numeric,
    "ebitda" numeric,
    "total_assets" numeric,
    "total_facilities" integer,
    "total_floor_area_sqft" numeric,
    "occupied_floor_area_sqft" numeric,
    "renewable_energy_percentage" numeric,
    "carbon_offset_percentage" numeric,
    "energy_intensity" numeric,
    "reporting_standard" character varying,
    "fiscal_year_start" "date",
    "fiscal_year_end" "date",
    "primary_contact_name" character varying,
    "primary_contact_email" character varying,
    "primary_contact_phone" character varying,
    "sustainability_officer_name" character varying,
    "sustainability_officer_email" character varying,
    "industry_sector" character varying,
    "naics_code" character varying,
    "sic_code" character varying,
    "custom_metrics" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "updated_by" "uuid",
    "total_floor_area_sqm" numeric,
    "occupied_floor_area_sqm" numeric,
    CONSTRAINT "organization_metadata_carbon_offset_percentage_check" CHECK ((("carbon_offset_percentage" IS NULL) OR (("carbon_offset_percentage" >= (0)::numeric) AND ("carbon_offset_percentage" <= (100)::numeric)))),
    CONSTRAINT "organization_metadata_renewable_energy_percentage_check" CHECK ((("renewable_energy_percentage" IS NULL) OR (("renewable_energy_percentage" >= (0)::numeric) AND ("renewable_energy_percentage" <= (100)::numeric))))
);


ALTER TABLE "public"."organization_metadata" OWNER TO "postgres";


COMMENT ON TABLE "public"."organization_metadata" IS 'Organization extended metadata';



COMMENT ON COLUMN "public"."organization_metadata"."total_floor_area_sqm" IS 'Total floor area m² (C10, APPROVE).';



COMMENT ON COLUMN "public"."organization_metadata"."occupied_floor_area_sqm" IS 'Occupied floor area m² (C10, APPROVE).';



CREATE TABLE IF NOT EXISTS "public"."organizations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" character varying NOT NULL,
    "company_number" character varying,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "logo_url" "text",
    "industry" "text",
    "sector" "text",
    "company_size" "text",
    "vat_number" "text",
    "registration_number" "text",
    "registered_address" "text",
    "country" "text",
    "timezone" "text",
    "currency" "text" DEFAULT 'GBP'::"text",
    "financial_year_end" "date",
    "reporting_standard" "text",
    "secr_enabled" boolean DEFAULT false,
    "esrs_enabled" boolean DEFAULT false,
    "issb_enabled" boolean DEFAULT false,
    "default_factor_year" integer,
    "preferred_units" "text",
    "website" "text",
    "primary_contact_email" "text",
    "primary_contact_name" "text",
    "billing_contact_email" "text",
    "billing_contact_name" "text",
    "subscription_status" "text",
    "trial_start_date" timestamp with time zone,
    "trial_end_date" timestamp with time zone,
    "subscription_tier" "text",
    "subscription_id" "text",
    "billing_address" "text",
    "tax_rate" numeric,
    "metadata" "jsonb",
    "address_line1" character varying,
    "address_line2" character varying,
    "city" character varying,
    "county" character varying,
    "postcode" character varying,
    "eircode" character varying,
    "language" character varying,
    "locale" character varying,
    "vat_region" character varying,
    "vat_registered" boolean DEFAULT false,
    "tax_region" character varying,
    "registration_region" character varying,
    "sic_code" character varying,
    "naics_code" character varying,
    "nace_code" character varying,
    "business_structure" character varying,
    "is_public" boolean DEFAULT false,
    "is_listed" boolean DEFAULT false,
    "isin" character varying,
    "cik" character varying,
    "sedol" character varying,
    "lei" character varying,
    "reporting_frequency" character varying,
    "accounting_standard" character varying,
    "sustainability_standard" character varying,
    "carbon_tax_region" character varying,
    "data_protection_officer" character varying,
    "privacy_policy_url" "text",
    "terms_url" "text",
    "is_active" boolean DEFAULT true NOT NULL,
    "archived_at" timestamp with time zone,
    CONSTRAINT "organizations_country_in_list" CHECK (("country" = ANY (ARRAY['GB'::"text", 'IE'::"text"]))),
    CONSTRAINT "organizations_currency_in_list" CHECK (("currency" = ANY (ARRAY['GBP'::"text", 'EUR'::"text"])))
);


ALTER TABLE "public"."organizations" OWNER TO "postgres";


COMMENT ON TABLE "public"."organizations" IS 'Organization/tenant root';



COMMENT ON COLUMN "public"."organizations"."is_active" IS 'Tenant lifecycle flag (C2, APPROVE). NOT NULL DEFAULT true. RLS suspend predicate.';



COMMENT ON COLUMN "public"."organizations"."archived_at" IS 'Tenant archival timestamp (C2, APPROVE). NULL = never archived.';



CREATE TABLE IF NOT EXISTS "public"."password_reset_tokens" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "token" character varying NOT NULL,
    "expires_at" timestamp with time zone NOT NULL,
    "used" boolean DEFAULT false,
    "used_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."password_reset_tokens" OWNER TO "postgres";


COMMENT ON TABLE "public"."password_reset_tokens" IS 'Password reset tokens';



CREATE TABLE IF NOT EXISTS "public"."pending_invites" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "email" character varying NOT NULL,
    "role" character varying NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."pending_invites" OWNER TO "postgres";


COMMENT ON TABLE "public"."pending_invites" IS 'Pending invites';



CREATE TABLE IF NOT EXISTS "public"."processing_assignments" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "queue_id" "uuid" NOT NULL,
    "assigned_to" "uuid" NOT NULL,
    "assigned_by" "uuid" NOT NULL,
    "assignment_status" character varying,
    "started_at" timestamp with time zone,
    "completed_at" timestamp with time zone,
    "processing_time_seconds" integer,
    "notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."processing_assignments" OWNER TO "postgres";


COMMENT ON TABLE "public"."processing_assignments" IS 'Queue task assignments';



CREATE TABLE IF NOT EXISTS "public"."processing_audit_trail" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "queue_id" "uuid" NOT NULL,
    "action" character varying NOT NULL,
    "performed_by" "uuid",
    "performed_by_staff" "uuid",
    "performed_by_type" character varying,
    "previous_value" "jsonb",
    "new_value" "jsonb",
    "notes" "text",
    "duration_ms" integer,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."processing_audit_trail" OWNER TO "postgres";


COMMENT ON TABLE "public"."processing_audit_trail" IS 'Processing audit trail';



CREATE TABLE IF NOT EXISTS "public"."processing_entities" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "status" character varying DEFAULT 'active'::character varying NOT NULL,
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_by" "uuid",
    CONSTRAINT "processing_entities_status_check" CHECK ((("status")::"text" = ANY ((ARRAY['active'::character varying, 'remediation'::character varying, 'suspended'::character varying, 'terminated'::character varying])::"text"[])))
);


ALTER TABLE "public"."processing_entities" OWNER TO "postgres";


COMMENT ON TABLE "public"."processing_entities" IS 'First-class Human Data Processing Entity (ADR-V3-001 — Option B, dedicated table). Distinct from Customer/Organization, User, Entity Staff, Consultant and CarbonTally internal staff. Lifecycle: active / remediation / suspended / terminated. Contract metadata fields deferred to V3 schema design (Q1) — carried in metadata JSONB.';



COMMENT ON COLUMN "public"."processing_entities"."status" IS 'Lifecycle status (Q6): active / remediation / suspended / terminated. Entity rows are never hard-deleted while referenced; lifecycle changes preserve history.';



COMMENT ON COLUMN "public"."processing_entities"."metadata" IS 'Flexible contract/commercial metadata (Q1 — exact fields deferred to V3 design).';



CREATE TABLE IF NOT EXISTS "public"."processing_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "file_id" "uuid",
    "organization_id" "uuid",
    "step" character varying NOT NULL,
    "status" character varying NOT NULL,
    "started_at" timestamp with time zone,
    "completed_at" timestamp with time zone,
    "duration_ms" integer,
    "details" "jsonb",
    "error" "text",
    "metadata" "jsonb",
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."processing_logs" OWNER TO "postgres";


COMMENT ON TABLE "public"."processing_logs" IS 'Processing logs';



CREATE TABLE IF NOT EXISTS "public"."processing_queue" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "document_id" "uuid" NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "batch_id" "uuid",
    "document_type" character varying NOT NULL,
    "priority" integer,
    "priority_score" integer,
    "queue_status" character varying DEFAULT 'pending'::character varying NOT NULL,
    "sla_deadline" timestamp with time zone,
    "sla_breached" boolean DEFAULT false NOT NULL,
    "estimated_completion_hours" integer,
    "actual_completion_hours" integer,
    "page_count" integer,
    "file_size_bytes" bigint,
    "notes" "text",
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_by" "uuid",
    CONSTRAINT "processing_queue_file_size_bytes_check" CHECK ((("file_size_bytes" IS NULL) OR ("file_size_bytes" >= 0))),
    CONSTRAINT "processing_queue_queue_status_check" CHECK ((("queue_status")::"text" = ANY ((ARRAY['pending'::character varying, 'assigned'::character varying, 'in_progress'::character varying, 'on_hold'::character varying, 'completed'::character varying, 'cancelled'::character varying])::"text"[])))
);


ALTER TABLE "public"."processing_queue" OWNER TO "postgres";


COMMENT ON TABLE "public"."processing_queue" IS 'Processing queue';



CREATE TABLE IF NOT EXISTS "public"."processing_steps" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "assignment_id" "uuid" NOT NULL,
    "step_name" character varying NOT NULL,
    "step_order" integer NOT NULL,
    "status" character varying,
    "started_at" timestamp with time zone,
    "completed_at" timestamp with time zone,
    "duration_seconds" integer,
    "notes" "text",
    "errors" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."processing_steps" OWNER TO "postgres";


COMMENT ON TABLE "public"."processing_steps" IS 'Processing step tracking';



CREATE TABLE IF NOT EXISTS "public"."processing_time_log" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "assignment_id" "uuid" NOT NULL,
    "staff_id" "uuid" NOT NULL,
    "activity_type" character varying NOT NULL,
    "start_time" timestamp with time zone NOT NULL,
    "end_time" timestamp with time zone,
    "duration_seconds" integer,
    "paused_duration_seconds" integer,
    "notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."processing_time_log" OWNER TO "postgres";


COMMENT ON TABLE "public"."processing_time_log" IS 'Processing time logs';



CREATE TABLE IF NOT EXISTS "public"."product_categories" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "category_type" character varying,
    "ghg_protocol_scope" character varying,
    "ghg_protocol_category" character varying,
    "esrs_e1_category" character varying,
    "issb_category" character varying,
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "updated_by" "uuid",
    "metadata" "jsonb"
);


ALTER TABLE "public"."product_categories" OWNER TO "postgres";


COMMENT ON TABLE "public"."product_categories" IS 'Product categories per organization';



CREATE TABLE IF NOT EXISTS "public"."qc_checklists" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "document_type" character varying NOT NULL,
    "checklist_name" character varying NOT NULL,
    "checklist_items" "jsonb" NOT NULL,
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_by" "uuid"
);


ALTER TABLE "public"."qc_checklists" OWNER TO "postgres";


COMMENT ON TABLE "public"."qc_checklists" IS 'QC checklists';



CREATE TABLE IF NOT EXISTS "public"."qc_checks" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "assignment_id" "uuid" NOT NULL,
    "qc_by" "uuid" NOT NULL,
    "qc_status" character varying,
    "qc_score" integer,
    "checks_passed" integer,
    "checks_failed" integer,
    "notes" "text",
    "reviewed_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "qc_checks_qc_score_check" CHECK ((("qc_score" IS NULL) OR (("qc_score" >= 0) AND ("qc_score" <= 100))))
);


ALTER TABLE "public"."qc_checks" OWNER TO "postgres";


COMMENT ON TABLE "public"."qc_checks" IS 'QC check results';



CREATE TABLE IF NOT EXISTS "public"."qc_errors" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "qc_check_id" "uuid" NOT NULL,
    "error_type" character varying NOT NULL,
    "field_name" character varying,
    "expected_value" "text",
    "actual_value" "text",
    "severity" character varying,
    "notes" "text",
    "is_resolved" boolean DEFAULT false,
    "resolved_at" timestamp with time zone,
    "resolved_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."qc_errors" OWNER TO "postgres";


COMMENT ON TABLE "public"."qc_errors" IS 'QC errors';



CREATE TABLE IF NOT EXISTS "public"."queue_settings" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "setting_key" character varying NOT NULL,
    "setting_value" "jsonb" NOT NULL,
    "description" "text",
    "updated_by" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."queue_settings" OWNER TO "postgres";


COMMENT ON TABLE "public"."queue_settings" IS 'Queue configuration settings';



CREATE TABLE IF NOT EXISTS "public"."reassignment_history" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "assignment_id" "uuid" NOT NULL,
    "previous_staff_id" "uuid",
    "new_staff_id" "uuid" NOT NULL,
    "reassigned_by" "uuid" NOT NULL,
    "reason" character varying,
    "notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."reassignment_history" OWNER TO "postgres";


COMMENT ON TABLE "public"."reassignment_history" IS 'Reassignment history';



CREATE TABLE IF NOT EXISTS "public"."report_comments" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "report_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "section_id" character varying,
    "comment" "text" NOT NULL,
    "comment_type" character varying,
    "is_resolved" boolean DEFAULT false,
    "resolved_at" timestamp with time zone,
    "resolved_by" "uuid",
    "resolution_notes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."report_comments" OWNER TO "postgres";


COMMENT ON TABLE "public"."report_comments" IS 'Report comments';



CREATE TABLE IF NOT EXISTS "public"."report_generation_queue" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "user_id" "uuid",
    "template_id" "uuid",
    "report_type" character varying NOT NULL,
    "reporting_year" integer NOT NULL,
    "report_name" character varying,
    "data_sources" "jsonb",
    "status" character varying,
    "progress_percentage" integer,
    "current_step" character varying,
    "generated_content" "jsonb",
    "user_edits" "jsonb",
    "final_report_url" "text",
    "final_report_file_name" character varying,
    "final_report_size_bytes" bigint,
    "ai_model_used" character varying,
    "ai_tokens_used" integer,
    "ai_cost" numeric,
    "ai_processing_time_ms" integer,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "started_at" timestamp with time zone,
    "completed_at" timestamp with time zone,
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "updated_by" "uuid",
    "metadata" "jsonb",
    "error_log" "text",
    CONSTRAINT "report_generation_queue_ai_cost_check" CHECK ((("ai_cost" IS NULL) OR ("ai_cost" >= (0)::numeric))),
    CONSTRAINT "report_generation_queue_final_report_size_bytes_check" CHECK ((("final_report_size_bytes" IS NULL) OR ("final_report_size_bytes" >= 0))),
    CONSTRAINT "report_generation_queue_progress_percentage_check" CHECK ((("progress_percentage" IS NULL) OR (("progress_percentage" >= 0) AND ("progress_percentage" <= 100))))
);


ALTER TABLE "public"."report_generation_queue" OWNER TO "postgres";


COMMENT ON TABLE "public"."report_generation_queue" IS 'Report generation queue';



CREATE TABLE IF NOT EXISTS "public"."report_templates" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid",
    "name" character varying NOT NULL,
    "description" "text",
    "report_type" character varying NOT NULL,
    "template_structure" "jsonb" NOT NULL,
    "ai_prompts" "jsonb",
    "logo_url" "text",
    "primary_color" character varying,
    "secondary_color" character varying,
    "font_family" character varying,
    "is_active" boolean DEFAULT true,
    "is_default" boolean DEFAULT false,
    "is_system" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "updated_by" "uuid"
);


ALTER TABLE "public"."report_templates" OWNER TO "postgres";


COMMENT ON TABLE "public"."report_templates" IS 'Report templates';



CREATE TABLE IF NOT EXISTS "public"."report_versions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "report_id" "uuid" NOT NULL,
    "version_number" integer NOT NULL,
    "content" "jsonb",
    "file_url" "text",
    "file_name" character varying,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "notes" "text",
    "change_summary" "text",
    "is_current" boolean DEFAULT false
);


ALTER TABLE "public"."report_versions" OWNER TO "postgres";


COMMENT ON TABLE "public"."report_versions" IS 'Report version history';



CREATE TABLE IF NOT EXISTS "public"."review_assignment_history" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "review_id" "uuid",
    "assigned_by" "uuid",
    "assigned_to" "uuid",
    "previous_assigned_to" "uuid",
    "action" character varying NOT NULL,
    "note" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."review_assignment_history" OWNER TO "postgres";


COMMENT ON TABLE "public"."review_assignment_history" IS 'Review assignment history';



CREATE TABLE IF NOT EXISTS "public"."review_audit_trail" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
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


COMMENT ON TABLE "public"."review_audit_trail" IS 'Review audit trail';



CREATE TABLE IF NOT EXISTS "public"."roles" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "permissions" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."roles" OWNER TO "postgres";


COMMENT ON TABLE "public"."roles" IS 'Role definitions for RBAC';



CREATE TABLE IF NOT EXISTS "public"."sla_compliance" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "document_type" character varying NOT NULL,
    "queue_id" "uuid" NOT NULL,
    "sla_deadline" timestamp with time zone NOT NULL,
    "completed_at" timestamp with time zone,
    "is_breached" boolean,
    "breach_reason" "text",
    "breach_time_minutes" integer,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."sla_compliance" OWNER TO "postgres";


COMMENT ON TABLE "public"."sla_compliance" IS 'SLA compliance tracking';



CREATE TABLE IF NOT EXISTS "public"."sla_definitions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "document_type" character varying NOT NULL,
    "priority_level" character varying NOT NULL,
    "sla_hours" integer NOT NULL,
    "escalation_hours" integer,
    "is_active" boolean DEFAULT true,
    "description" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "sla_definitions_sla_hours_check" CHECK (("sla_hours" >= 0))
);


ALTER TABLE "public"."sla_definitions" OWNER TO "postgres";


COMMENT ON TABLE "public"."sla_definitions" IS 'SLA definitions';



CREATE TABLE IF NOT EXISTS "public"."staff_activity_log" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "staff_id" "uuid" NOT NULL,
    "activity_type" character varying NOT NULL,
    "activity_details" "jsonb",
    "ip_address" "inet",
    "user_agent" "text",
    "session_id" "uuid",
    "duration_seconds" integer,
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."staff_activity_log" OWNER TO "postgres";


COMMENT ON TABLE "public"."staff_activity_log" IS 'Staff activity log';



CREATE TABLE IF NOT EXISTS "public"."staff_daily_performance" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "staff_id" "uuid" NOT NULL,
    "date" "date" NOT NULL,
    "total_assigned" integer,
    "completed" integer,
    "rejected" integer,
    "qc_passed" integer,
    "qc_failed" integer,
    "total_processing_time_seconds" integer,
    "avg_time_per_document_seconds" integer,
    "productivity_score" numeric,
    "quality_score" numeric,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."staff_daily_performance" OWNER TO "postgres";


COMMENT ON TABLE "public"."staff_daily_performance" IS 'Staff daily performance';



CREATE TABLE IF NOT EXISTS "public"."staff_performance" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "staff_id" "uuid" NOT NULL,
    "period_start" "date" NOT NULL,
    "period_end" "date" NOT NULL,
    "period_type" character varying NOT NULL,
    "total_assigned" integer,
    "total_completed" integer,
    "total_rejected" integer,
    "avg_processing_time_seconds" integer,
    "qc_pass_rate" numeric,
    "accuracy_rate" numeric,
    "productivity_score" numeric,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."staff_performance" OWNER TO "postgres";


COMMENT ON TABLE "public"."staff_performance" IS 'Staff performance metrics';



CREATE TABLE IF NOT EXISTS "public"."staff_profiles" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "first_name" character varying NOT NULL,
    "last_name" character varying NOT NULL,
    "email" character varying NOT NULL,
    "role_id" "uuid",
    "is_active" boolean DEFAULT true,
    "hire_date" "date",
    "skills" "jsonb",
    "max_concurrent_tasks" integer,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_by" "uuid",
    "entity_id" "uuid"
);


ALTER TABLE "public"."staff_profiles" OWNER TO "postgres";


COMMENT ON TABLE "public"."staff_profiles" IS 'Staff profiles';



COMMENT ON COLUMN "public"."staff_profiles"."entity_id" IS 'NULL = CarbonTally internal processing staff (positive convention, NOT unknown). Populated = staff member belonging to the referenced Processing Entity (ADR-V3-001 Q5). ON DELETE RESTRICT preserves attribution; entity rows are never hard-deleted while staff reference them.';



CREATE TABLE IF NOT EXISTS "public"."staff_roles" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "permissions" "jsonb" NOT NULL,
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_by" "uuid"
);


ALTER TABLE "public"."staff_roles" OWNER TO "postgres";


COMMENT ON TABLE "public"."staff_roles" IS 'Staff role definitions';



CREATE TABLE IF NOT EXISTS "public"."staff_workload" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "staff_id" "uuid" NOT NULL,
    "assigned_tasks" integer,
    "in_progress_tasks" integer,
    "pending_tasks" integer,
    "completed_today" integer,
    "workload_score" numeric,
    "capacity_percentage" numeric,
    "date" "date",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "staff_workload_assigned_tasks_check" CHECK ((("assigned_tasks" IS NULL) OR ("assigned_tasks" >= 0))),
    CONSTRAINT "staff_workload_completed_today_check" CHECK ((("completed_today" IS NULL) OR ("completed_today" >= 0))),
    CONSTRAINT "staff_workload_in_progress_tasks_check" CHECK ((("in_progress_tasks" IS NULL) OR ("in_progress_tasks" >= 0))),
    CONSTRAINT "staff_workload_pending_tasks_check" CHECK ((("pending_tasks" IS NULL) OR ("pending_tasks" >= 0)))
);


ALTER TABLE "public"."staff_workload" OWNER TO "postgres";


COMMENT ON TABLE "public"."staff_workload" IS 'Staff workload tracking';



CREATE TABLE IF NOT EXISTS "public"."supplier_categories" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "category_group" character varying,
    "default_emission_factor" numeric,
    "default_emission_factor_unit" character varying,
    "ghg_protocol_category" character varying,
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."supplier_categories" OWNER TO "postgres";


COMMENT ON TABLE "public"."supplier_categories" IS 'Supplier category reference';



CREATE TABLE IF NOT EXISTS "public"."suppliers" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "type" character varying,
    "supplier_category_id" "uuid",
    "contact_name" character varying,
    "contact_email" character varying,
    "contact_phone" character varying,
    "address" "text",
    "website" character varying,
    "tax_id" character varying,
    "registration_number" character varying,
    "annual_emissions_scope1" numeric,
    "annual_emissions_scope2" numeric,
    "annual_emissions_scope3" numeric,
    "reporting_year" integer,
    "emission_factor_scope1" numeric,
    "emission_factor_scope2" numeric,
    "emission_factor_scope3" numeric,
    "emission_factor_unit" character varying,
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "created_by" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "updated_by" "uuid",
    "metadata" "jsonb",
    "address_line1" character varying,
    "address_line2" character varying,
    "city" character varying,
    "county" character varying,
    "postcode" character varying,
    "country" character varying,
    "eircode" character varying,
    "tax_region" character varying,
    "tax_rate" numeric,
    "vat_number" character varying,
    "company_number" character varying,
    "registration_region" character varying,
    "primary_contact" character varying,
    "primary_email" character varying,
    "primary_phone" character varying,
    "supplier_type" character varying,
    "annual_emissions" numeric,
    "emission_factor" numeric,
    "supplier_rating" numeric,
    "is_certified" boolean DEFAULT false,
    "certification_type" "text",
    "certification_expiry" "date",
    "contract_start" "date",
    "contract_end" "date",
    "payment_terms" character varying,
    "payment_currency" character varying,
    "bank_name" character varying,
    "bank_account" character varying,
    "iban" character varying,
    "swift_code" character varying,
    "risk_score" numeric,
    "compliance_status" character varying,
    "sort_code" character varying,
    CONSTRAINT "suppliers_annual_emissions_check" CHECK ((("annual_emissions" IS NULL) OR ("annual_emissions" >= (0)::numeric))),
    CONSTRAINT "suppliers_annual_emissions_scope1_check" CHECK ((("annual_emissions_scope1" IS NULL) OR ("annual_emissions_scope1" >= (0)::numeric))),
    CONSTRAINT "suppliers_annual_emissions_scope2_check" CHECK ((("annual_emissions_scope2" IS NULL) OR ("annual_emissions_scope2" >= (0)::numeric))),
    CONSTRAINT "suppliers_annual_emissions_scope3_check" CHECK ((("annual_emissions_scope3" IS NULL) OR ("annual_emissions_scope3" >= (0)::numeric))),
    CONSTRAINT "suppliers_country_check" CHECK ((("country" IS NULL) OR (("country")::"text" = ANY ((ARRAY['GB'::character varying, 'IE'::character varying])::"text"[])))),
    CONSTRAINT "suppliers_country_in_list" CHECK ((("country")::"text" = ANY ((ARRAY['GB'::character varying, 'IE'::character varying])::"text"[]))),
    CONSTRAINT "suppliers_emission_factor_check" CHECK ((("emission_factor" IS NULL) OR ("emission_factor" >= (0)::numeric))),
    CONSTRAINT "suppliers_emission_factor_scope1_check" CHECK ((("emission_factor_scope1" IS NULL) OR ("emission_factor_scope1" >= (0)::numeric))),
    CONSTRAINT "suppliers_emission_factor_scope2_check" CHECK ((("emission_factor_scope2" IS NULL) OR ("emission_factor_scope2" >= (0)::numeric))),
    CONSTRAINT "suppliers_emission_factor_scope3_check" CHECK ((("emission_factor_scope3" IS NULL) OR ("emission_factor_scope3" >= (0)::numeric))),
    CONSTRAINT "suppliers_payment_currency_check" CHECK ((("payment_currency" IS NULL) OR (("payment_currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[])))),
    CONSTRAINT "suppliers_payment_currency_in_list" CHECK ((("payment_currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[]))),
    CONSTRAINT "suppliers_risk_score_check" CHECK ((("risk_score" IS NULL) OR (("risk_score" >= (0)::numeric) AND ("risk_score" <= (100)::numeric)))),
    CONSTRAINT "suppliers_supplier_rating_check" CHECK ((("supplier_rating" IS NULL) OR (("supplier_rating" >= (0)::numeric) AND ("supplier_rating" <= (100)::numeric))))
);


ALTER TABLE "public"."suppliers" OWNER TO "postgres";


COMMENT ON TABLE "public"."suppliers" IS 'Supplier records';



COMMENT ON COLUMN "public"."suppliers"."sort_code" IS 'UK bank sort code, digits only, API-normalised (C8, APPROVE). PII register.';



CREATE TABLE IF NOT EXISTS "public"."system_settings" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "setting_key" character varying NOT NULL,
    "setting_value" "jsonb" NOT NULL,
    "setting_type" character varying,
    "description" "text",
    "is_editable" boolean DEFAULT true,
    "updated_by" "uuid",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "created_at" timestamp with time zone DEFAULT "now"(),
    "default_currency" character varying DEFAULT 'GBP'::character varying,
    "default_language" character varying,
    "default_timezone" character varying,
    "default_region" character varying,
    "default_reporting_standard" character varying,
    "date_format" character varying,
    "time_format" character varying,
    "number_format" character varying,
    "week_start_day" character varying,
    "default_tax_region" character varying,
    "default_tax_rate" numeric,
    "default_vat_rate" numeric,
    "default_emission_factor_set" character varying,
    "default_emission_factor_year" integer,
    "carbon_tax_region" character varying,
    "carbon_tax_rate" numeric,
    "carbon_tax_unit" character varying,
    "emission_verification_required" boolean DEFAULT false,
    "emission_verification_standard" character varying,
    "sla_default_hours" integer,
    "sla_escalation_hours" integer,
    "sla_breach_alert_enabled" boolean DEFAULT true,
    "sla_breach_alert_recipients" "text",
    "max_upload_size_mb" integer,
    "max_batch_size_mb" integer,
    "max_file_upload_daily" integer,
    "max_documents_per_batch" integer,
    "max_pages_per_document" integer,
    "api_rate_limit" integer,
    "api_rate_limit_burst" integer,
    "webhook_retry_count" integer,
    "webhook_retry_delay" integer,
    "webhook_timeout_seconds" integer,
    "session_timeout_minutes" integer,
    "session_extend_on_activity" boolean DEFAULT true,
    "two_factor_required" boolean DEFAULT false,
    "two_factor_method" character varying,
    "password_expiry_days" integer,
    "password_min_length" integer,
    "password_require_special" boolean DEFAULT true,
    "password_require_number" boolean DEFAULT true,
    "password_require_uppercase" boolean DEFAULT true,
    "password_require_lowercase" boolean DEFAULT true,
    "login_attempts_max" integer,
    "login_attempts_lockout_minutes" integer,
    "audit_log_retention_days" integer,
    "data_retention_days" integer,
    "document_retention_days" integer,
    "backup_frequency" character varying,
    "backup_retention_days" integer,
    "backup_storage_location" "text",
    CONSTRAINT "system_settings_default_currency_check" CHECK ((("default_currency" IS NULL) OR (("default_currency")::"text" = ANY ((ARRAY['GBP'::character varying, 'EUR'::character varying])::"text"[]))))
);


ALTER TABLE "public"."system_settings" OWNER TO "postgres";


COMMENT ON TABLE "public"."system_settings" IS 'System configuration settings';



CREATE TABLE IF NOT EXISTS "public"."team_performance" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "date" "date" NOT NULL,
    "total_staff_active" integer,
    "total_assigned" integer,
    "total_completed" integer,
    "total_rejected" integer,
    "avg_processing_time_seconds" integer,
    "qc_pass_rate" numeric,
    "sla_compliance_rate" numeric,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."team_performance" OWNER TO "postgres";


COMMENT ON TABLE "public"."team_performance" IS 'Team performance';



CREATE TABLE IF NOT EXISTS "public"."typing_status" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "conversation_id" "uuid",
    "is_typing" boolean DEFAULT false,
    "started_at" timestamp with time zone,
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."typing_status" OWNER TO "postgres";


COMMENT ON TABLE "public"."typing_status" IS 'Typing status';



CREATE TABLE IF NOT EXISTS "public"."units" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "code" character varying NOT NULL,
    "name" character varying NOT NULL,
    "category" character varying NOT NULL,
    "symbol" character varying,
    "conversion_factor" numeric,
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."units" OWNER TO "postgres";


COMMENT ON TABLE "public"."units" IS 'Unit of measurement reference';



CREATE TABLE IF NOT EXISTS "public"."upload_batches" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "batch_name" character varying,
    "total_files" integer,
    "processed_files" integer,
    "status" "text",
    "created_by_user_id" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "completed_at" timestamp with time zone,
    "metadata" "jsonb",
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "batch_type" character varying,
    "estimated_processing_time" timestamp with time zone,
    "error_count" integer,
    "manual_extraction_requested" boolean DEFAULT false,
    "manual_extraction_batch_id" "uuid",
    "created_by" "uuid",
    "updated_by" "uuid",
    "entity_id" "uuid"
);


ALTER TABLE "public"."upload_batches" OWNER TO "postgres";


COMMENT ON TABLE "public"."upload_batches" IS 'Upload batches';



COMMENT ON COLUMN "public"."upload_batches"."entity_id" IS 'Processing Entity allocated this batch (NULL = CarbonTally internal; ADR-V3-001 Q5). ON DELETE RESTRICT preserves attribution.';



CREATE TABLE IF NOT EXISTS "public"."usage_tracking" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid" NOT NULL,
    "usage_date" "date",
    "usage_month" "date",
    "ai_files_processed" integer,
    "batch_files_uploaded" integer,
    "manual_pages_extracted" integer,
    "reports_generated" integer,
    "total_storage_bytes" bigint,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "usage_tracking_ai_files_processed_check" CHECK ((("ai_files_processed" IS NULL) OR ("ai_files_processed" >= 0))),
    CONSTRAINT "usage_tracking_batch_files_uploaded_check" CHECK ((("batch_files_uploaded" IS NULL) OR ("batch_files_uploaded" >= 0))),
    CONSTRAINT "usage_tracking_manual_pages_extracted_check" CHECK ((("manual_pages_extracted" IS NULL) OR ("manual_pages_extracted" >= 0))),
    CONSTRAINT "usage_tracking_reports_generated_check" CHECK ((("reports_generated" IS NULL) OR ("reports_generated" >= 0))),
    CONSTRAINT "usage_tracking_total_storage_bytes_check" CHECK ((("total_storage_bytes" IS NULL) OR ("total_storage_bytes" >= 0)))
);


ALTER TABLE "public"."usage_tracking" OWNER TO "postgres";


COMMENT ON TABLE "public"."usage_tracking" IS 'Usage tracking';



CREATE TABLE IF NOT EXISTS "public"."user_activity_log" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "action" character varying NOT NULL,
    "details" "jsonb",
    "ip_address" character varying,
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."user_activity_log" OWNER TO "postgres";


COMMENT ON TABLE "public"."user_activity_log" IS 'User activity log';



CREATE TABLE IF NOT EXISTS "public"."user_feedback" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "organization_id" "uuid",
    "user_id" "uuid",
    "user_email" "text" NOT NULL,
    "type" "text" NOT NULL,
    "title" "text" NOT NULL,
    "description" "text" NOT NULL,
    "severity" "text",
    "status" "text",
    "rating" integer,
    "screenshot_url" "text",
    "browser_info" "text",
    "os_info" "text",
    "url" "text",
    "assigned_to" "uuid",
    "resolved_at" timestamp with time zone,
    "resolution_notes" "text",
    "metadata" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "user_feedback_rating_check" CHECK ((("rating" IS NULL) OR (("rating" >= 1) AND ("rating" <= 5))))
);


ALTER TABLE "public"."user_feedback" OWNER TO "postgres";


COMMENT ON TABLE "public"."user_feedback" IS 'User feedback';



CREATE TABLE IF NOT EXISTS "public"."user_invitations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "email" character varying NOT NULL,
    "role_id" "uuid",
    "organization_id" "uuid",
    "invited_by" "uuid",
    "token" character varying NOT NULL,
    "status" character varying,
    "expires_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."user_invitations" OWNER TO "postgres";


COMMENT ON TABLE "public"."user_invitations" IS 'User invitations';



CREATE TABLE IF NOT EXISTS "public"."user_presence" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "status" "text",
    "last_seen_at" timestamp with time zone,
    "current_channel" "text",
    "metadata" "jsonb"
);


ALTER TABLE "public"."user_presence" OWNER TO "postgres";


COMMENT ON TABLE "public"."user_presence" IS 'User presence';



CREATE TABLE IF NOT EXISTS "public"."users" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "email" character varying NOT NULL,
    "password_hash" character varying,
    "first_name" character varying,
    "last_name" character varying,
    "user_type" character varying,
    "is_active" boolean DEFAULT true,
    "email_verified" boolean DEFAULT false,
    "last_login" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "is_anonymised" boolean DEFAULT false
);


ALTER TABLE "public"."users" OWNER TO "postgres";


COMMENT ON TABLE "public"."users" IS 'User accounts (auth.users mirror)';



CREATE TABLE IF NOT EXISTS "public"."verification_activity_log" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "verification_id" "uuid",
    "user_id" "uuid",
    "action_type" "text",
    "action_details" "jsonb",
    "ip_address" "text",
    "user_agent" "text",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."verification_activity_log" OWNER TO "postgres";


COMMENT ON TABLE "public"."verification_activity_log" IS 'Verification activity log';



CREATE TABLE IF NOT EXISTS "public"."verification_logs" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "document_id" "uuid" NOT NULL,
    "verified_by" "uuid" NOT NULL,
    "verified_at" timestamp with time zone,
    "verification_status" character varying NOT NULL,
    "verification_notes" "text",
    "verification_data" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."verification_logs" OWNER TO "postgres";


COMMENT ON TABLE "public"."verification_logs" IS 'Verification logs';



CREATE TABLE IF NOT EXISTS "public"."waitlist" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "email" "text" NOT NULL,
    "full_name" "text",
    "company_name" "text",
    "company_size" "text",
    "interested_in" "text",
    "source" "text",
    "status" "text",
    "invited_at" timestamp with time zone,
    "activated_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."waitlist" OWNER TO "postgres";


COMMENT ON TABLE "public"."waitlist" IS 'Waitlist';



ALTER TABLE ONLY "public"."activity_categories"
    ADD CONSTRAINT "activity_categories_activity_type_key" UNIQUE ("activity_type");



ALTER TABLE ONLY "public"."activity_categories"
    ADD CONSTRAINT "activity_categories_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."activity_feed"
    ADD CONSTRAINT "activity_feed_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."activity_logs"
    ADD CONSTRAINT "activity_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."ai_content_history"
    ADD CONSTRAINT "ai_content_history_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."approval_decisions"
    ADD CONSTRAINT "approval_decisions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."approval_requests"
    ADD CONSTRAINT "approval_requests_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."assets"
    ADD CONSTRAINT "assets_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."audit_logs"
    ADD CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."audit_trail"
    ADD CONSTRAINT "audit_trail_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."beta_access_codes"
    ADD CONSTRAINT "beta_access_codes_code_key" UNIQUE ("code");



ALTER TABLE ONLY "public"."beta_access_codes"
    ADD CONSTRAINT "beta_access_codes_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."beta_users"
    ADD CONSTRAINT "beta_users_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."business_hours"
    ADD CONSTRAINT "business_hours_day_of_week_key" UNIQUE ("day_of_week");



ALTER TABLE ONLY "public"."business_hours"
    ADD CONSTRAINT "business_hours_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."calculation_snapshots"
    ADD CONSTRAINT "calculation_snapshots_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."consultant_billing"
    ADD CONSTRAINT "consultant_billing_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."consultant_clients"
    ADD CONSTRAINT "consultant_clients_consultant_id_organization_id_key" UNIQUE ("consultant_id", "organization_id");



ALTER TABLE ONLY "public"."consultant_clients"
    ADD CONSTRAINT "consultant_clients_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."consultant_firm_members"
    ADD CONSTRAINT "consultant_firm_members_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."consultant_profiles"
    ADD CONSTRAINT "consultant_profiles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."consultant_tasks"
    ADD CONSTRAINT "consultant_tasks_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversation_activity_log"
    ADD CONSTRAINT "conversation_activity_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversation_participants"
    ADD CONSTRAINT "conversation_participants_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customer_communication"
    ADD CONSTRAINT "customer_communication_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customer_documents"
    ADD CONSTRAINT "customer_documents_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customer_review_log"
    ADD CONSTRAINT "customer_review_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customer_subscriptions"
    ADD CONSTRAINT "customer_subscriptions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customer_verifications"
    ADD CONSTRAINT "customer_verifications_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."dashboard_metrics"
    ADD CONSTRAINT "dashboard_metrics_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."document_activity_log"
    ADD CONSTRAINT "document_activity_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."document_processing_queue"
    ADD CONSTRAINT "document_processing_queue_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."document_type_categories"
    ADD CONSTRAINT "document_type_categories_code_key" UNIQUE ("code");



ALTER TABLE ONLY "public"."document_type_categories"
    ADD CONSTRAINT "document_type_categories_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."document_types"
    ADD CONSTRAINT "document_types_code_key" UNIQUE ("code");



ALTER TABLE ONLY "public"."document_types"
    ADD CONSTRAINT "document_types_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."domain_events"
    ADD CONSTRAINT "domain_events_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."draft_entries"
    ADD CONSTRAINT "draft_entries_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."email_logs"
    ADD CONSTRAINT "email_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."email_templates"
    ADD CONSTRAINT "email_templates_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."emission_factors"
    ADD CONSTRAINT "emission_factors_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."export_history"
    ADD CONSTRAINT "export_history_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."facilities"
    ADD CONSTRAINT "facilities_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."factor_aliases"
    ADD CONSTRAINT "factor_aliases_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."file_attachments"
    ADD CONSTRAINT "file_attachments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."glossary"
    ADD CONSTRAINT "glossary_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."glossary"
    ADD CONSTRAINT "glossary_term_key" UNIQUE ("term");



ALTER TABLE ONLY "public"."import_batches"
    ADD CONSTRAINT "import_batches_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."login_history"
    ADD CONSTRAINT "login_history_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."manual_extraction_batches"
    ADD CONSTRAINT "manual_extraction_batches_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."manual_extraction_items"
    ADD CONSTRAINT "manual_extraction_items_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."message_activity_log"
    ADD CONSTRAINT "message_activity_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."notification_delivery"
    ADD CONSTRAINT "notification_delivery_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."notification_templates"
    ADD CONSTRAINT "notification_templates_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."notification_templates"
    ADD CONSTRAINT "notification_templates_template_type_key" UNIQUE ("template_type");



ALTER TABLE ONLY "public"."notifications"
    ADD CONSTRAINT "notifications_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."organization_files"
    ADD CONSTRAINT "organization_files_pkey" PRIMARY KEY ("id");



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



ALTER TABLE ONLY "public"."pending_invites"
    ADD CONSTRAINT "pending_invites_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."processing_assignments"
    ADD CONSTRAINT "processing_assignments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."processing_audit_trail"
    ADD CONSTRAINT "processing_audit_trail_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."processing_entities"
    ADD CONSTRAINT "processing_entities_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."processing_logs"
    ADD CONSTRAINT "processing_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."processing_queue"
    ADD CONSTRAINT "processing_queue_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."processing_steps"
    ADD CONSTRAINT "processing_steps_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."processing_time_log"
    ADD CONSTRAINT "processing_time_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."product_categories"
    ADD CONSTRAINT "product_categories_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."qc_checklists"
    ADD CONSTRAINT "qc_checklists_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."qc_checks"
    ADD CONSTRAINT "qc_checks_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."qc_errors"
    ADD CONSTRAINT "qc_errors_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."queue_settings"
    ADD CONSTRAINT "queue_settings_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."queue_settings"
    ADD CONSTRAINT "queue_settings_setting_key_key" UNIQUE ("setting_key");



ALTER TABLE ONLY "public"."reassignment_history"
    ADD CONSTRAINT "reassignment_history_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."report_comments"
    ADD CONSTRAINT "report_comments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."report_generation_queue"
    ADD CONSTRAINT "report_generation_queue_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."report_templates"
    ADD CONSTRAINT "report_templates_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."report_versions"
    ADD CONSTRAINT "report_versions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."report_versions"
    ADD CONSTRAINT "report_versions_report_id_version_number_key" UNIQUE ("report_id", "version_number");



ALTER TABLE ONLY "public"."review_assignment_history"
    ADD CONSTRAINT "review_assignment_history_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."review_audit_trail"
    ADD CONSTRAINT "review_audit_trail_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_name_key" UNIQUE ("name");



ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."sla_compliance"
    ADD CONSTRAINT "sla_compliance_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."sla_definitions"
    ADD CONSTRAINT "sla_definitions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."staff_activity_log"
    ADD CONSTRAINT "staff_activity_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."staff_daily_performance"
    ADD CONSTRAINT "staff_daily_performance_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."staff_performance"
    ADD CONSTRAINT "staff_performance_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."staff_profiles"
    ADD CONSTRAINT "staff_profiles_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."staff_profiles"
    ADD CONSTRAINT "staff_profiles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."staff_roles"
    ADD CONSTRAINT "staff_roles_name_key" UNIQUE ("name");



ALTER TABLE ONLY "public"."staff_roles"
    ADD CONSTRAINT "staff_roles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."staff_workload"
    ADD CONSTRAINT "staff_workload_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."supplier_categories"
    ADD CONSTRAINT "supplier_categories_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."suppliers"
    ADD CONSTRAINT "suppliers_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."system_settings"
    ADD CONSTRAINT "system_settings_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."system_settings"
    ADD CONSTRAINT "system_settings_setting_key_key" UNIQUE ("setting_key");



ALTER TABLE ONLY "public"."team_performance"
    ADD CONSTRAINT "team_performance_date_key" UNIQUE ("date");



ALTER TABLE ONLY "public"."team_performance"
    ADD CONSTRAINT "team_performance_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."typing_status"
    ADD CONSTRAINT "typing_status_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."units"
    ADD CONSTRAINT "units_code_key" UNIQUE ("code");



ALTER TABLE ONLY "public"."units"
    ADD CONSTRAINT "units_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."upload_batches"
    ADD CONSTRAINT "upload_batches_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."usage_tracking"
    ADD CONSTRAINT "usage_tracking_organization_id_usage_month_key" UNIQUE ("organization_id", "usage_month");



ALTER TABLE ONLY "public"."usage_tracking"
    ADD CONSTRAINT "usage_tracking_pkey" PRIMARY KEY ("id");



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



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."verification_activity_log"
    ADD CONSTRAINT "verification_activity_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."verification_logs"
    ADD CONSTRAINT "verification_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."waitlist"
    ADD CONSTRAINT "waitlist_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."waitlist"
    ADD CONSTRAINT "waitlist_pkey" PRIMARY KEY ("id");



CREATE INDEX "consultant_firm_members_client_access_gin" ON "public"."consultant_firm_members" USING "gin" ("client_access");



CREATE INDEX "conversation_participants_conv_user_idx" ON "public"."conversation_participants" USING "btree" ("conversation_id", "user_id");



CREATE INDEX "customer_documents_document_type_id_idx" ON "public"."customer_documents" USING "btree" ("document_type_id");



CREATE INDEX "customer_documents_org_created_idx" ON "public"."customer_documents" USING "btree" ("organization_id", "created_at" DESC);



CREATE INDEX "customer_documents_supplier_id_idx" ON "public"."customer_documents" USING "btree" ("supplier_id");



CREATE INDEX "dpq_claim_idx" ON "public"."document_processing_queue" USING "btree" ("status", "created_at") WHERE (("status")::"text" = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'manual_review'::character varying, 'manual_extraction'::character varying, 'qc'::character varying, 'customer_review'::character varying])::"text"[]));



CREATE INDEX "dpq_customer_document_id_idx" ON "public"."document_processing_queue" USING "btree" ("customer_document_id");



CREATE INDEX "dpq_emission_factor_used_idx" ON "public"."document_processing_queue" USING "btree" ("emission_factor_used");



CREATE UNIQUE INDEX "emission_factors_year_activity_country_uniq" ON "public"."emission_factors" USING "btree" ("reporting_year", "activity_type", COALESCE("country", 'GB'::character varying), COALESCE("unit", '{no-unit}'::"text"), COALESCE("scope", '{no-scope}'::"text"));



CREATE INDEX "emissions_logs_asset_id_idx" ON "public"."emissions_logs" USING "btree" ("asset_id");



CREATE INDEX "emissions_logs_emission_factor_id_idx" ON "public"."emissions_logs" USING "btree" ("emission_factor_id");



CREATE INDEX "emissions_logs_org_start_date_idx" ON "public"."emissions_logs" USING "btree" ("organization_id", "start_date");



CREATE INDEX "facilities_org_idx" ON "public"."facilities" USING "btree" ("organization_id");



CREATE INDEX "idx_domain_events_aggregate" ON "public"."domain_events" USING "btree" ("aggregate_type", "aggregate_id");



CREATE INDEX "idx_domain_events_correlation" ON "public"."domain_events" USING "btree" ("correlation_id");



CREATE INDEX "idx_emission_factors_import_batch" ON "public"."emission_factors" USING "btree" ("import_batch_id");



CREATE INDEX "idx_emissions_logs_snapshot" ON "public"."emissions_logs" USING "btree" ("snapshot_id");



CREATE UNIQUE INDEX "idx_factor_aliases_unique" ON "public"."factor_aliases" USING "btree" (COALESCE("organization_id", '00000000-0000-0000-0000-000000000000'::"uuid"), "alias_text");



CREATE INDEX "idx_manual_review_queue_entity_id" ON "public"."manual_review_queue" USING "btree" ("entity_id");



CREATE INDEX "idx_staff_profiles_entity_id" ON "public"."staff_profiles" USING "btree" ("entity_id");



CREATE INDEX "idx_upload_batches_entity_id" ON "public"."upload_batches" USING "btree" ("entity_id");



CREATE INDEX "messages_conversation_created_idx" ON "public"."messages" USING "btree" ("conversation_id", "created_at");



CREATE INDEX "notifications_unread_recipient_idx" ON "public"."notifications" USING "btree" ("recipient_id", "created_at") WHERE ("is_read" = false);



CREATE INDEX "organizations_name_trgm_idx" ON "public"."organizations" USING "gin" ("name" "public"."gin_trgm_ops");



CREATE INDEX "password_reset_tokens_user_id_idx" ON "public"."password_reset_tokens" USING "btree" ("user_id");



CREATE INDEX "processing_queue_claim_idx" ON "public"."processing_queue" USING "btree" ("queue_status", "created_at") WHERE (("queue_status")::"text" = ANY ((ARRAY['pending'::character varying, 'assigned'::character varying, 'in_progress'::character varying])::"text"[]));



CREATE INDEX "report_generation_queue_claim_idx" ON "public"."report_generation_queue" USING "btree" ("status", "created_at") WHERE (("status")::"text" = ANY ((ARRAY['pending'::character varying, 'queued'::character varying, 'processing'::character varying])::"text"[]));



CREATE INDEX "suppliers_name_trgm_idx" ON "public"."suppliers" USING "gin" ("name" "public"."gin_trgm_ops");



CREATE UNIQUE INDEX "suppliers_org_company_number_uniq" ON "public"."suppliers" USING "btree" ("organization_id", "company_number") WHERE ("company_number" IS NOT NULL);



CREATE INDEX "suppliers_org_idx" ON "public"."suppliers" USING "btree" ("organization_id");



CREATE UNIQUE INDEX "suppliers_org_vat_number_uniq" ON "public"."suppliers" USING "btree" ("organization_id", "vat_number") WHERE ("vat_number" IS NOT NULL);



CREATE INDEX "suppliers_vat_number_trgm_idx" ON "public"."suppliers" USING "gin" ("vat_number" "public"."gin_trgm_ops");



CREATE UNIQUE INDEX "usage_tracking_org_month_uniq" ON "public"."usage_tracking" USING "btree" ("organization_id", COALESCE("usage_month", '1900-01-01'::"date"));



CREATE OR REPLACE TRIGGER "trg_set_updated_at_activity_categories" BEFORE UPDATE ON "public"."activity_categories" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_approval_decisions" BEFORE UPDATE ON "public"."approval_decisions" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_approval_requests" BEFORE UPDATE ON "public"."approval_requests" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_assets" BEFORE UPDATE ON "public"."assets" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_beta_access_codes" BEFORE UPDATE ON "public"."beta_access_codes" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_beta_users" BEFORE UPDATE ON "public"."beta_users" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_business_hours" BEFORE UPDATE ON "public"."business_hours" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_consultant_billing" BEFORE UPDATE ON "public"."consultant_billing" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_consultant_clients" BEFORE UPDATE ON "public"."consultant_clients" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_consultant_firm_members" BEFORE UPDATE ON "public"."consultant_firm_members" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_consultant_profiles" BEFORE UPDATE ON "public"."consultant_profiles" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_consultant_tasks" BEFORE UPDATE ON "public"."consultant_tasks" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_conversation_participants" BEFORE UPDATE ON "public"."conversation_participants" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_conversations" BEFORE UPDATE ON "public"."conversations" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_customer_communication" BEFORE UPDATE ON "public"."customer_communication" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_customer_documents" BEFORE UPDATE ON "public"."customer_documents" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_customer_review_log" BEFORE UPDATE ON "public"."customer_review_log" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_customer_subscriptions" BEFORE UPDATE ON "public"."customer_subscriptions" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_customer_verifications" BEFORE UPDATE ON "public"."customer_verifications" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_document_processing_queue" BEFORE UPDATE ON "public"."document_processing_queue" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_document_type_categories" BEFORE UPDATE ON "public"."document_type_categories" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_document_types" BEFORE UPDATE ON "public"."document_types" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_draft_entries" BEFORE UPDATE ON "public"."draft_entries" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_email_templates" BEFORE UPDATE ON "public"."email_templates" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_emission_factors" BEFORE UPDATE ON "public"."emission_factors" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_emissions_logs" BEFORE UPDATE ON "public"."emissions_logs" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_export_history" BEFORE UPDATE ON "public"."export_history" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_facilities" BEFORE UPDATE ON "public"."facilities" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_glossary" BEFORE UPDATE ON "public"."glossary" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_manual_extraction_batches" BEFORE UPDATE ON "public"."manual_extraction_batches" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_manual_extraction_items" BEFORE UPDATE ON "public"."manual_extraction_items" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_manual_review_queue" BEFORE UPDATE ON "public"."manual_review_queue" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_messages" BEFORE UPDATE ON "public"."messages" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_notification_delivery" BEFORE UPDATE ON "public"."notification_delivery" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_notification_templates" BEFORE UPDATE ON "public"."notification_templates" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_notifications" BEFORE UPDATE ON "public"."notifications" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_organization_files" BEFORE UPDATE ON "public"."organization_files" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_organization_members" BEFORE UPDATE ON "public"."organization_members" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_organization_metadata" BEFORE UPDATE ON "public"."organization_metadata" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_organizations" BEFORE UPDATE ON "public"."organizations" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_password_reset_tokens" BEFORE UPDATE ON "public"."password_reset_tokens" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_pending_invites" BEFORE UPDATE ON "public"."pending_invites" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_processing_assignments" BEFORE UPDATE ON "public"."processing_assignments" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_processing_queue" BEFORE UPDATE ON "public"."processing_queue" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_processing_steps" BEFORE UPDATE ON "public"."processing_steps" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_processing_time_log" BEFORE UPDATE ON "public"."processing_time_log" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_product_categories" BEFORE UPDATE ON "public"."product_categories" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_qc_checklists" BEFORE UPDATE ON "public"."qc_checklists" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_qc_checks" BEFORE UPDATE ON "public"."qc_checks" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_qc_errors" BEFORE UPDATE ON "public"."qc_errors" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_queue_settings" BEFORE UPDATE ON "public"."queue_settings" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_report_comments" BEFORE UPDATE ON "public"."report_comments" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_report_generation_queue" BEFORE UPDATE ON "public"."report_generation_queue" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_report_templates" BEFORE UPDATE ON "public"."report_templates" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_review_assignment_history" BEFORE UPDATE ON "public"."review_assignment_history" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_roles" BEFORE UPDATE ON "public"."roles" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_sla_compliance" BEFORE UPDATE ON "public"."sla_compliance" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_sla_definitions" BEFORE UPDATE ON "public"."sla_definitions" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_staff_daily_performance" BEFORE UPDATE ON "public"."staff_daily_performance" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_staff_performance" BEFORE UPDATE ON "public"."staff_performance" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_staff_profiles" BEFORE UPDATE ON "public"."staff_profiles" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_staff_roles" BEFORE UPDATE ON "public"."staff_roles" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_staff_workload" BEFORE UPDATE ON "public"."staff_workload" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_supplier_categories" BEFORE UPDATE ON "public"."supplier_categories" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_suppliers" BEFORE UPDATE ON "public"."suppliers" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_system_settings" BEFORE UPDATE ON "public"."system_settings" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_team_performance" BEFORE UPDATE ON "public"."team_performance" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_typing_status" BEFORE UPDATE ON "public"."typing_status" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_units" BEFORE UPDATE ON "public"."units" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_upload_batches" BEFORE UPDATE ON "public"."upload_batches" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_usage_tracking" BEFORE UPDATE ON "public"."usage_tracking" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_user_feedback" BEFORE UPDATE ON "public"."user_feedback" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_user_invitations" BEFORE UPDATE ON "public"."user_invitations" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_users" BEFORE UPDATE ON "public"."users" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



CREATE OR REPLACE TRIGGER "trg_set_updated_at_waitlist" BEFORE UPDATE ON "public"."waitlist" FOR EACH ROW EXECUTE FUNCTION "public"."set_updated_at"();



ALTER TABLE ONLY "public"."ai_content_history"
    ADD CONSTRAINT "ai_content_history_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."approval_decisions"
    ADD CONSTRAINT "approval_decisions_approval_request_id_fkey" FOREIGN KEY ("approval_request_id") REFERENCES "public"."approval_requests"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."approval_requests"
    ADD CONSTRAINT "approval_requests_assignment_id_fkey" FOREIGN KEY ("assignment_id") REFERENCES "public"."processing_assignments"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."assets"
    ADD CONSTRAINT "assets_facility_id_fkey" FOREIGN KEY ("facility_id") REFERENCES "public"."facilities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."assets"
    ADD CONSTRAINT "assets_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id");



ALTER TABLE ONLY "public"."calculation_snapshots"
    ADD CONSTRAINT "calculation_snapshots_factor_id_fkey" FOREIGN KEY ("factor_id") REFERENCES "public"."emission_factors"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."calculation_snapshots"
    ADD CONSTRAINT "calculation_snapshots_import_batch_id_fkey" FOREIGN KEY ("import_batch_id") REFERENCES "public"."import_batches"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."calculation_snapshots"
    ADD CONSTRAINT "calculation_snapshots_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."consultant_billing"
    ADD CONSTRAINT "consultant_billing_consultant_id_fkey" FOREIGN KEY ("consultant_id") REFERENCES "public"."consultant_profiles"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."consultant_clients"
    ADD CONSTRAINT "consultant_clients_consultant_id_fkey" FOREIGN KEY ("consultant_id") REFERENCES "public"."consultant_profiles"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."consultant_clients"
    ADD CONSTRAINT "consultant_clients_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."consultant_firm_members"
    ADD CONSTRAINT "consultant_firm_members_firm_id_fkey" FOREIGN KEY ("firm_id") REFERENCES "public"."consultant_profiles"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."consultant_firm_members"
    ADD CONSTRAINT "consultant_firm_members_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."consultant_profiles"
    ADD CONSTRAINT "consultant_profiles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."consultant_tasks"
    ADD CONSTRAINT "consultant_tasks_consultant_id_fkey" FOREIGN KEY ("consultant_id") REFERENCES "public"."consultant_profiles"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."conversation_participants"
    ADD CONSTRAINT "conversation_participants_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."customer_communication"
    ADD CONSTRAINT "customer_communication_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."customer_documents"
    ADD CONSTRAINT "customer_documents_document_type_id_fkey" FOREIGN KEY ("document_type_id") REFERENCES "public"."document_types"("id");



ALTER TABLE ONLY "public"."customer_documents"
    ADD CONSTRAINT "customer_documents_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."customer_documents"
    ADD CONSTRAINT "customer_documents_organization_member_id_fkey" FOREIGN KEY ("organization_member_id") REFERENCES "public"."organization_members"("id");



ALTER TABLE ONLY "public"."customer_subscriptions"
    ADD CONSTRAINT "customer_subscriptions_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."document_processing_queue"
    ADD CONSTRAINT "document_processing_queue_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."document_processing_queue"
    ADD CONSTRAINT "dpq_ai_mapped_asset_id_fkey" FOREIGN KEY ("ai_mapped_asset_id") REFERENCES "public"."assets"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."document_processing_queue"
    ADD CONSTRAINT "dpq_ai_mapped_facility_id_fkey" FOREIGN KEY ("ai_mapped_facility_id") REFERENCES "public"."facilities"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."document_processing_queue"
    ADD CONSTRAINT "dpq_ai_mapped_supplier_id_fkey" FOREIGN KEY ("ai_mapped_supplier_id") REFERENCES "public"."suppliers"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."document_processing_queue"
    ADD CONSTRAINT "dpq_emission_factor_used_fkey" FOREIGN KEY ("emission_factor_used") REFERENCES "public"."emission_factors"("id");



ALTER TABLE ONLY "public"."emission_factors"
    ADD CONSTRAINT "emission_factors_import_batch_id_fkey" FOREIGN KEY ("import_batch_id") REFERENCES "public"."import_batches"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_asset_id_fkey" FOREIGN KEY ("asset_id") REFERENCES "public"."assets"("id");



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_emission_factor_id_fkey" FOREIGN KEY ("emission_factor_id") REFERENCES "public"."emission_factors"("id");



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."emissions_logs"
    ADD CONSTRAINT "emissions_logs_snapshot_id_fkey" FOREIGN KEY ("snapshot_id") REFERENCES "public"."calculation_snapshots"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."facilities"
    ADD CONSTRAINT "facilities_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."factor_aliases"
    ADD CONSTRAINT "factor_aliases_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."file_attachments"
    ADD CONSTRAINT "file_attachments_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "public"."messages"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."import_batches"
    ADD CONSTRAINT "import_batches_rolled_back_from_fkey" FOREIGN KEY ("rolled_back_from") REFERENCES "public"."import_batches"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."manual_extraction_batches"
    ADD CONSTRAINT "manual_extraction_batches_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."manual_extraction_items"
    ADD CONSTRAINT "manual_extraction_items_batch_id_fkey" FOREIGN KEY ("batch_id") REFERENCES "public"."manual_extraction_batches"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_entity_id_fkey" FOREIGN KEY ("entity_id") REFERENCES "public"."processing_entities"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."manual_review_queue"
    ADD CONSTRAINT "manual_review_queue_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."notification_delivery"
    ADD CONSTRAINT "notification_delivery_notification_id_fkey" FOREIGN KEY ("notification_id") REFERENCES "public"."notifications"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."organization_files"
    ADD CONSTRAINT "organization_files_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."organization_members"
    ADD CONSTRAINT "organization_members_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."organization_members"
    ADD CONSTRAINT "organization_members_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."organization_metadata"
    ADD CONSTRAINT "organization_metadata_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."pending_invites"
    ADD CONSTRAINT "pending_invites_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."processing_assignments"
    ADD CONSTRAINT "processing_assignments_queue_id_fkey" FOREIGN KEY ("queue_id") REFERENCES "public"."processing_queue"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."processing_queue"
    ADD CONSTRAINT "processing_queue_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."processing_steps"
    ADD CONSTRAINT "processing_steps_assignment_id_fkey" FOREIGN KEY ("assignment_id") REFERENCES "public"."processing_assignments"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."qc_checks"
    ADD CONSTRAINT "qc_checks_assignment_id_fkey" FOREIGN KEY ("assignment_id") REFERENCES "public"."processing_assignments"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."qc_errors"
    ADD CONSTRAINT "qc_errors_qc_check_id_fkey" FOREIGN KEY ("qc_check_id") REFERENCES "public"."qc_checks"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."report_generation_queue"
    ADD CONSTRAINT "report_generation_queue_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."report_templates"
    ADD CONSTRAINT "report_templates_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."staff_performance"
    ADD CONSTRAINT "staff_performance_staff_id_fkey" FOREIGN KEY ("staff_id") REFERENCES "public"."staff_profiles"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."staff_profiles"
    ADD CONSTRAINT "staff_profiles_entity_id_fkey" FOREIGN KEY ("entity_id") REFERENCES "public"."processing_entities"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."staff_profiles"
    ADD CONSTRAINT "staff_profiles_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "public"."staff_roles"("id");



ALTER TABLE ONLY "public"."staff_profiles"
    ADD CONSTRAINT "staff_profiles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."staff_workload"
    ADD CONSTRAINT "staff_workload_staff_id_fkey" FOREIGN KEY ("staff_id") REFERENCES "public"."staff_profiles"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."suppliers"
    ADD CONSTRAINT "suppliers_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."suppliers"
    ADD CONSTRAINT "suppliers_supplier_category_id_fkey" FOREIGN KEY ("supplier_category_id") REFERENCES "public"."supplier_categories"("id");



ALTER TABLE ONLY "public"."typing_status"
    ADD CONSTRAINT "typing_status_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."upload_batches"
    ADD CONSTRAINT "upload_batches_entity_id_fkey" FOREIGN KEY ("entity_id") REFERENCES "public"."processing_entities"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."usage_tracking"
    ADD CONSTRAINT "usage_tracking_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_invitations"
    ADD CONSTRAINT "user_invitations_organization_id_fkey" FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id") ON DELETE CASCADE;



CREATE POLICY "activity_categories_authenticated_read" ON "public"."activity_categories" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "activity_feed_tenant_delete" ON "public"."activity_feed" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "activity_feed_tenant_insert" ON "public"."activity_feed" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "activity_feed_tenant_select" ON "public"."activity_feed" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "activity_feed_tenant_update" ON "public"."activity_feed" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "activity_logs_tenant_delete" ON "public"."activity_logs" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "activity_logs_tenant_insert" ON "public"."activity_logs" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "activity_logs_tenant_select" ON "public"."activity_logs" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "activity_logs_tenant_update" ON "public"."activity_logs" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "ai_content_history_tenant_delete" ON "public"."ai_content_history" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "ai_content_history_tenant_insert" ON "public"."ai_content_history" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "ai_content_history_tenant_select" ON "public"."ai_content_history" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "ai_content_history_tenant_update" ON "public"."ai_content_history" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "aliases_delete_own" ON "public"."factor_aliases" FOR DELETE TO "authenticated" USING ((("organization_id" IS NOT NULL) AND "public"."is_org_member"("organization_id")));



CREATE POLICY "aliases_insert_own" ON "public"."factor_aliases" FOR INSERT TO "authenticated" WITH CHECK ((("organization_id" IS NOT NULL) AND "public"."is_org_member"("organization_id")));



CREATE POLICY "aliases_select_own" ON "public"."factor_aliases" FOR SELECT TO "authenticated" USING ((("organization_id" IS NULL) OR "public"."is_org_member"("organization_id")));



CREATE POLICY "assets_tenant_delete" ON "public"."assets" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "assets_tenant_insert" ON "public"."assets" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "assets_tenant_select" ON "public"."assets" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "assets_tenant_update" ON "public"."assets" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "audit_logs_tenant_delete" ON "public"."audit_logs" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "audit_logs_tenant_insert" ON "public"."audit_logs" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "audit_logs_tenant_select" ON "public"."audit_logs" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "audit_logs_tenant_update" ON "public"."audit_logs" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "calc_snapshots_select_own" ON "public"."calculation_snapshots" FOR SELECT TO "authenticated" USING ("public"."is_org_member"("organization_id"));



ALTER TABLE "public"."calculation_snapshots" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "cc_delete_own_firm" ON "public"."consultant_clients" FOR DELETE TO "authenticated" USING ((EXISTS ( SELECT 1
   FROM "public"."consultant_firm_members" "me"
  WHERE (("me"."firm_id" = "consultant_clients"."consultant_id") AND ("me"."user_id" = "auth"."uid"()) AND COALESCE("me"."is_active", true) AND ("me"."can_manage_clients" = true)))));



CREATE POLICY "cc_insert_own_firm" ON "public"."consultant_clients" FOR INSERT TO "authenticated" WITH CHECK ((EXISTS ( SELECT 1
   FROM "public"."consultant_firm_members" "me"
  WHERE (("me"."firm_id" = "consultant_clients"."consultant_id") AND ("me"."user_id" = "auth"."uid"()) AND COALESCE("me"."is_active", true) AND ("me"."can_manage_clients" = true)))));



CREATE POLICY "cc_select_own_firm" ON "public"."consultant_clients" FOR SELECT TO "authenticated" USING ((EXISTS ( SELECT 1
   FROM "public"."consultant_firm_members" "me"
  WHERE (("me"."firm_id" = "consultant_clients"."consultant_id") AND ("me"."user_id" = "auth"."uid"()) AND COALESCE("me"."is_active", true)))));



CREATE POLICY "cc_update_own_firm" ON "public"."consultant_clients" FOR UPDATE TO "authenticated" USING ((EXISTS ( SELECT 1
   FROM "public"."consultant_firm_members" "me"
  WHERE (("me"."firm_id" = "consultant_clients"."consultant_id") AND ("me"."user_id" = "auth"."uid"()) AND COALESCE("me"."is_active", true) AND ("me"."can_manage_clients" = true)))));



CREATE POLICY "cfm_select_self_or_team_admin" ON "public"."consultant_firm_members" FOR SELECT TO "authenticated" USING ((("user_id" = "auth"."uid"()) OR (EXISTS ( SELECT 1
   FROM "public"."consultant_firm_members" "me"
  WHERE (("me"."firm_id" = "consultant_firm_members"."firm_id") AND ("me"."user_id" = "auth"."uid"()) AND COALESCE("me"."is_active", true) AND ("me"."can_manage_team" = true))))));



CREATE POLICY "cfm_update_self_or_team_admin" ON "public"."consultant_firm_members" FOR UPDATE TO "authenticated" USING (("user_id" = "auth"."uid"())) WITH CHECK (("user_id" = "auth"."uid"()));



CREATE POLICY "consultant_clients_tenant_delete" ON "public"."consultant_clients" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "consultant_clients_tenant_insert" ON "public"."consultant_clients" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "consultant_clients_tenant_select" ON "public"."consultant_clients" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "consultant_clients_tenant_update" ON "public"."consultant_clients" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "conversations_tenant_delete" ON "public"."conversations" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "conversations_tenant_insert" ON "public"."conversations" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "conversations_tenant_select" ON "public"."conversations" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "conversations_tenant_update" ON "public"."conversations" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "cp_select_own" ON "public"."consultant_profiles" FOR SELECT TO "authenticated" USING (("user_id" = "auth"."uid"()));



CREATE POLICY "customer_communication_tenant_delete" ON "public"."customer_communication" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_communication_tenant_insert" ON "public"."customer_communication" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_communication_tenant_select" ON "public"."customer_communication" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "customer_communication_tenant_update" ON "public"."customer_communication" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_documents_tenant_delete" ON "public"."customer_documents" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_documents_tenant_insert" ON "public"."customer_documents" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_documents_tenant_select" ON "public"."customer_documents" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "customer_documents_tenant_update" ON "public"."customer_documents" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_review_log_tenant_delete" ON "public"."customer_review_log" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_review_log_tenant_insert" ON "public"."customer_review_log" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_review_log_tenant_select" ON "public"."customer_review_log" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "customer_review_log_tenant_update" ON "public"."customer_review_log" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_subscriptions_tenant_delete" ON "public"."customer_subscriptions" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_subscriptions_tenant_insert" ON "public"."customer_subscriptions" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_subscriptions_tenant_select" ON "public"."customer_subscriptions" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "customer_subscriptions_tenant_update" ON "public"."customer_subscriptions" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_verifications_tenant_delete" ON "public"."customer_verifications" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_verifications_tenant_insert" ON "public"."customer_verifications" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "customer_verifications_tenant_select" ON "public"."customer_verifications" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "customer_verifications_tenant_update" ON "public"."customer_verifications" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "document_activity_log_tenant_delete" ON "public"."document_activity_log" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "document_activity_log_tenant_insert" ON "public"."document_activity_log" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "document_activity_log_tenant_select" ON "public"."document_activity_log" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "document_activity_log_tenant_update" ON "public"."document_activity_log" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "document_processing_queue_tenant_delete" ON "public"."document_processing_queue" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "document_processing_queue_tenant_insert" ON "public"."document_processing_queue" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "document_processing_queue_tenant_select" ON "public"."document_processing_queue" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "document_processing_queue_tenant_update" ON "public"."document_processing_queue" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "document_type_categories_authenticated_read" ON "public"."document_type_categories" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "document_types_authenticated_read" ON "public"."document_types" FOR SELECT TO "authenticated" USING (true);



ALTER TABLE "public"."domain_events" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "draft_entries_tenant_delete" ON "public"."draft_entries" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "draft_entries_tenant_insert" ON "public"."draft_entries" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "draft_entries_tenant_select" ON "public"."draft_entries" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "draft_entries_tenant_update" ON "public"."draft_entries" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "email_templates_authenticated_read" ON "public"."email_templates" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "emissions_logs_tenant_delete" ON "public"."emissions_logs" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "emissions_logs_tenant_insert" ON "public"."emissions_logs" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "emissions_logs_tenant_select" ON "public"."emissions_logs" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "emissions_logs_tenant_update" ON "public"."emissions_logs" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "export_history_tenant_delete" ON "public"."export_history" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "export_history_tenant_insert" ON "public"."export_history" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "export_history_tenant_select" ON "public"."export_history" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "export_history_tenant_update" ON "public"."export_history" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "facilities_tenant_delete" ON "public"."facilities" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "facilities_tenant_insert" ON "public"."facilities" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "facilities_tenant_select" ON "public"."facilities" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "facilities_tenant_update" ON "public"."facilities" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



ALTER TABLE "public"."factor_aliases" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "file_attachments_tenant_delete" ON "public"."file_attachments" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "file_attachments_tenant_insert" ON "public"."file_attachments" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "file_attachments_tenant_select" ON "public"."file_attachments" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "file_attachments_tenant_update" ON "public"."file_attachments" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "glossary_authenticated_read" ON "public"."glossary" FOR SELECT TO "authenticated" USING (true);



ALTER TABLE "public"."import_batches" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "manual_extraction_batches_tenant_delete" ON "public"."manual_extraction_batches" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "manual_extraction_batches_tenant_insert" ON "public"."manual_extraction_batches" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "manual_extraction_batches_tenant_select" ON "public"."manual_extraction_batches" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "manual_extraction_batches_tenant_update" ON "public"."manual_extraction_batches" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "manual_review_queue_tenant_delete" ON "public"."manual_review_queue" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "manual_review_queue_tenant_insert" ON "public"."manual_review_queue" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "manual_review_queue_tenant_select" ON "public"."manual_review_queue" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "manual_review_queue_tenant_update" ON "public"."manual_review_queue" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "messages_tenant_delete" ON "public"."messages" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "messages_tenant_insert" ON "public"."messages" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "messages_tenant_select" ON "public"."messages" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "messages_tenant_update" ON "public"."messages" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "notification_templates_authenticated_read" ON "public"."notification_templates" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "om_insert_admin" ON "public"."organization_members" FOR INSERT TO "authenticated" WITH CHECK ((EXISTS ( SELECT 1
   FROM "public"."organization_members" "admin_om"
  WHERE (("admin_om"."organization_id" = "organization_members"."organization_id") AND ("admin_om"."user_id" = "auth"."uid"()) AND (("admin_om"."role")::"text" = ANY ((ARRAY['owner'::character varying, 'admin'::character varying])::"text"[])) AND COALESCE("admin_om"."is_active", true)))));



CREATE POLICY "om_select_self_or_admin" ON "public"."organization_members" FOR SELECT TO "authenticated" USING ((("user_id" = "auth"."uid"()) OR (EXISTS ( SELECT 1
   FROM "public"."organization_members" "admin_om"
  WHERE (("admin_om"."organization_id" = "organization_members"."organization_id") AND ("admin_om"."user_id" = "auth"."uid"()) AND (("admin_om"."role")::"text" = ANY ((ARRAY['owner'::character varying, 'admin'::character varying])::"text"[])) AND COALESCE("admin_om"."is_active", true))))));



CREATE POLICY "om_update_admin" ON "public"."organization_members" FOR UPDATE TO "authenticated" USING ((EXISTS ( SELECT 1
   FROM "public"."organization_members" "admin_om"
  WHERE (("admin_om"."organization_id" = "organization_members"."organization_id") AND ("admin_om"."user_id" = "auth"."uid"()) AND (("admin_om"."role")::"text" = ANY ((ARRAY['owner'::character varying, 'admin'::character varying])::"text"[])) AND COALESCE("admin_om"."is_active", true))))) WITH CHECK ((("role")::"text" = ANY ((ARRAY['owner'::character varying, 'admin'::character varying, 'member'::character varying, 'viewer'::character varying])::"text"[])));



CREATE POLICY "om_update_self" ON "public"."organization_members" FOR UPDATE TO "authenticated" USING (("user_id" = "auth"."uid"())) WITH CHECK (("user_id" = "auth"."uid"()));



CREATE POLICY "organization_files_tenant_delete" ON "public"."organization_files" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "organization_files_tenant_insert" ON "public"."organization_files" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "organization_files_tenant_select" ON "public"."organization_files" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "organization_files_tenant_update" ON "public"."organization_files" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "organization_metadata_tenant_delete" ON "public"."organization_metadata" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "organization_metadata_tenant_insert" ON "public"."organization_metadata" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "organization_metadata_tenant_select" ON "public"."organization_metadata" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "organization_metadata_tenant_update" ON "public"."organization_metadata" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "organizations_org_select" ON "public"."organizations" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("id") OR "public"."is_org_consultant"("id")));



CREATE POLICY "organizations_org_update" ON "public"."organizations" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("id")) WITH CHECK ("public"."is_org_member"("id"));



CREATE POLICY "pending_invites_tenant_delete" ON "public"."pending_invites" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "pending_invites_tenant_insert" ON "public"."pending_invites" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "pending_invites_tenant_select" ON "public"."pending_invites" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "pending_invites_tenant_update" ON "public"."pending_invites" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



ALTER TABLE "public"."processing_entities" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "processing_logs_tenant_delete" ON "public"."processing_logs" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "processing_logs_tenant_insert" ON "public"."processing_logs" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "processing_logs_tenant_select" ON "public"."processing_logs" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "processing_logs_tenant_update" ON "public"."processing_logs" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "processing_queue_tenant_delete" ON "public"."processing_queue" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "processing_queue_tenant_insert" ON "public"."processing_queue" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "processing_queue_tenant_select" ON "public"."processing_queue" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "processing_queue_tenant_update" ON "public"."processing_queue" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "product_categories_tenant_delete" ON "public"."product_categories" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "product_categories_tenant_insert" ON "public"."product_categories" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "product_categories_tenant_select" ON "public"."product_categories" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "product_categories_tenant_update" ON "public"."product_categories" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "report_generation_queue_tenant_delete" ON "public"."report_generation_queue" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "report_generation_queue_tenant_insert" ON "public"."report_generation_queue" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "report_generation_queue_tenant_select" ON "public"."report_generation_queue" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "report_generation_queue_tenant_update" ON "public"."report_generation_queue" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "report_templates_tenant_delete" ON "public"."report_templates" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "report_templates_tenant_insert" ON "public"."report_templates" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "report_templates_tenant_select" ON "public"."report_templates" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "report_templates_tenant_update" ON "public"."report_templates" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "roles_authenticated_read" ON "public"."roles" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "supplier_categories_authenticated_read" ON "public"."supplier_categories" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "suppliers_tenant_delete" ON "public"."suppliers" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "suppliers_tenant_insert" ON "public"."suppliers" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "suppliers_tenant_select" ON "public"."suppliers" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "suppliers_tenant_update" ON "public"."suppliers" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "units_authenticated_read" ON "public"."units" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "upload_batches_tenant_delete" ON "public"."upload_batches" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "upload_batches_tenant_insert" ON "public"."upload_batches" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "upload_batches_tenant_select" ON "public"."upload_batches" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "upload_batches_tenant_update" ON "public"."upload_batches" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "usage_tracking_tenant_delete" ON "public"."usage_tracking" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "usage_tracking_tenant_insert" ON "public"."usage_tracking" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "usage_tracking_tenant_select" ON "public"."usage_tracking" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "usage_tracking_tenant_update" ON "public"."usage_tracking" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "user_feedback_tenant_delete" ON "public"."user_feedback" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "user_feedback_tenant_insert" ON "public"."user_feedback" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "user_feedback_tenant_select" ON "public"."user_feedback" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "user_feedback_tenant_update" ON "public"."user_feedback" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "user_invitations_tenant_delete" ON "public"."user_invitations" FOR DELETE TO "authenticated" USING ("public"."is_org_member"("organization_id"));



CREATE POLICY "user_invitations_tenant_insert" ON "public"."user_invitations" FOR INSERT TO "authenticated" WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "user_invitations_tenant_select" ON "public"."user_invitations" FOR SELECT TO "authenticated" USING (("public"."is_org_member"("organization_id") OR "public"."is_org_consultant"("organization_id")));



CREATE POLICY "user_invitations_tenant_update" ON "public"."user_invitations" FOR UPDATE TO "authenticated" USING ("public"."is_org_member"("organization_id")) WITH CHECK ("public"."is_org_member"("organization_id"));



CREATE POLICY "users_select_self" ON "public"."users" FOR SELECT TO "authenticated" USING (("id" = "auth"."uid"()));



CREATE POLICY "users_update_self" ON "public"."users" FOR UPDATE TO "authenticated" USING (("id" = "auth"."uid"())) WITH CHECK (("id" = "auth"."uid"()));





ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";





GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_in"("cstring") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_out"("public"."gtrgm") TO "service_role";




























































































































































REVOKE ALL ON FUNCTION "public"."anonymise_user"("p_user_id" "uuid", "p_actor_id" "uuid", "p_reason" "text") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."anonymise_user"("p_user_id" "uuid", "p_actor_id" "uuid", "p_reason" "text") TO "service_role";
GRANT ALL ON FUNCTION "public"."anonymise_user"("p_user_id" "uuid", "p_actor_id" "uuid", "p_reason" "text") TO "authenticated";



GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_extract_query_trgm"("text", "internal", smallint, "internal", "internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_extract_value_trgm"("text", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_trgm_consistent"("internal", smallint, "text", integer, "internal", "internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gin_trgm_triconsistent"("internal", smallint, "text", integer, "internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_compress"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_consistent"("internal", "text", smallint, "oid", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_decompress"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_distance"("internal", "text", smallint, "oid", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_options"("internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_penalty"("internal", "internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_picksplit"("internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_same"("public"."gtrgm", "public"."gtrgm", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "postgres";
GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "anon";
GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "authenticated";
GRANT ALL ON FUNCTION "public"."gtrgm_union"("internal", "internal") TO "service_role";



GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "postgres";
GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "anon";
GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "authenticated";
GRANT ALL ON FUNCTION "public"."set_limit"(real) TO "service_role";



GRANT ALL ON FUNCTION "public"."show_limit"() TO "postgres";
GRANT ALL ON FUNCTION "public"."show_limit"() TO "anon";
GRANT ALL ON FUNCTION "public"."show_limit"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."show_limit"() TO "service_role";



GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "postgres";
GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "anon";
GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."show_trgm"("text") TO "service_role";



GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."similarity"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."similarity_dist"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."similarity_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_dist_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."strict_word_similarity_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_commutator_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_dist_op"("text", "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "postgres";
GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "anon";
GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."word_similarity_op"("text", "text") TO "service_role";


















GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."activity_categories" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."activity_categories" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."activity_categories" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."activity_feed" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."activity_feed" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."activity_feed" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."activity_logs" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."activity_logs" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."activity_logs" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."ai_content_history" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."ai_content_history" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."ai_content_history" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."approval_decisions" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."approval_decisions" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."approval_decisions" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."approval_requests" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."approval_requests" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."approval_requests" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."assets" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."assets" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."assets" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."audit_logs" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."audit_logs" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."audit_logs" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."audit_trail" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."audit_trail" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."audit_trail" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."beta_access_codes" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."beta_access_codes" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."beta_access_codes" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."beta_users" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."beta_users" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."beta_users" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."business_hours" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."business_hours" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."business_hours" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."calculation_snapshots" TO "anon";
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "public"."calculation_snapshots" TO "authenticated";
GRANT ALL ON TABLE "public"."calculation_snapshots" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_billing" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_billing" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_billing" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_clients" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_clients" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_clients" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_firm_members" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_firm_members" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_firm_members" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_profiles" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_profiles" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_profiles" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_tasks" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_tasks" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."consultant_tasks" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."conversation_activity_log" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."conversation_activity_log" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."conversation_activity_log" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."conversation_participants" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."conversation_participants" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."conversation_participants" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."conversations" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."conversations" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."conversations" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_communication" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_communication" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_communication" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_documents" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_documents" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_documents" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_review_log" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_review_log" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_review_log" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_subscriptions" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_subscriptions" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_subscriptions" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_verifications" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_verifications" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."customer_verifications" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."dashboard_metrics" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."dashboard_metrics" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."dashboard_metrics" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_activity_log" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_activity_log" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_activity_log" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_processing_queue" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_processing_queue" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_processing_queue" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_type_categories" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_type_categories" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_type_categories" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_types" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_types" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."document_types" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."domain_events" TO "anon";
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "public"."domain_events" TO "authenticated";
GRANT ALL ON TABLE "public"."domain_events" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."draft_entries" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."draft_entries" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."draft_entries" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."email_logs" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."email_logs" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."email_logs" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."email_templates" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."email_templates" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."email_templates" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."emission_factors" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."emission_factors" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."emission_factors" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."emissions_logs" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."emissions_logs" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."emissions_logs" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."export_history" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."export_history" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."export_history" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."facilities" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."facilities" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."facilities" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."factor_aliases" TO "anon";
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "public"."factor_aliases" TO "authenticated";
GRANT ALL ON TABLE "public"."factor_aliases" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."file_attachments" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."file_attachments" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."file_attachments" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."glossary" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."glossary" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."glossary" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."import_batches" TO "anon";
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "public"."import_batches" TO "authenticated";
GRANT ALL ON TABLE "public"."import_batches" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."login_history" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."login_history" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."login_history" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."manual_extraction_batches" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."manual_extraction_batches" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."manual_extraction_batches" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."manual_extraction_items" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."manual_extraction_items" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."manual_extraction_items" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."manual_review_queue" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."manual_review_queue" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."manual_review_queue" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."message_activity_log" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."message_activity_log" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."message_activity_log" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."messages" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."messages" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."messages" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."notification_delivery" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."notification_delivery" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."notification_delivery" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."notification_templates" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."notification_templates" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."notification_templates" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."notifications" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."notifications" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."notifications" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organization_files" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organization_files" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organization_files" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organization_members" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organization_members" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organization_members" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organization_metadata" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organization_metadata" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organization_metadata" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organizations" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organizations" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."organizations" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."password_reset_tokens" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."password_reset_tokens" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."password_reset_tokens" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."pending_invites" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."pending_invites" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."pending_invites" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_assignments" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_assignments" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_assignments" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_audit_trail" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_audit_trail" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_audit_trail" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_entities" TO "anon";
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "public"."processing_entities" TO "authenticated";
GRANT ALL ON TABLE "public"."processing_entities" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_logs" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_logs" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_logs" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_queue" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_queue" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_queue" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_steps" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_steps" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_steps" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_time_log" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_time_log" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."processing_time_log" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."product_categories" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."product_categories" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."product_categories" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."qc_checklists" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."qc_checklists" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."qc_checklists" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."qc_checks" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."qc_checks" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."qc_checks" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."qc_errors" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."qc_errors" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."qc_errors" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."queue_settings" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."queue_settings" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."queue_settings" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."reassignment_history" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."reassignment_history" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."reassignment_history" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_comments" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_comments" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_comments" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_generation_queue" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_generation_queue" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_generation_queue" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_templates" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_templates" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_templates" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_versions" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_versions" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."report_versions" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."review_assignment_history" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."review_assignment_history" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."review_assignment_history" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."review_audit_trail" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."review_audit_trail" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."review_audit_trail" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."roles" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."roles" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."roles" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."sla_compliance" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."sla_compliance" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."sla_compliance" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."sla_definitions" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."sla_definitions" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."sla_definitions" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_activity_log" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_activity_log" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_activity_log" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_daily_performance" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_daily_performance" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_daily_performance" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_performance" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_performance" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_performance" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_profiles" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_profiles" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_profiles" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_roles" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_roles" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_roles" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_workload" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_workload" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."staff_workload" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."supplier_categories" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."supplier_categories" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."supplier_categories" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."suppliers" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."suppliers" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."suppliers" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."system_settings" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."system_settings" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."system_settings" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."team_performance" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."team_performance" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."team_performance" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."typing_status" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."typing_status" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."typing_status" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."units" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."units" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."units" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."upload_batches" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."upload_batches" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."upload_batches" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."usage_tracking" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."usage_tracking" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."usage_tracking" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_activity_log" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_activity_log" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_activity_log" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_feedback" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_feedback" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_feedback" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_invitations" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_invitations" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_invitations" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_presence" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_presence" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."user_presence" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."users" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."users" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."users" TO "service_role";



GRANT UPDATE("first_name") ON TABLE "public"."users" TO "authenticated";



GRANT UPDATE("last_name") ON TABLE "public"."users" TO "authenticated";



GRANT UPDATE("updated_at") ON TABLE "public"."users" TO "authenticated";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."verification_activity_log" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."verification_activity_log" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."verification_activity_log" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."verification_logs" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."verification_logs" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."verification_logs" TO "service_role";



GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."waitlist" TO "anon";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."waitlist" TO "authenticated";
GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLE "public"."waitlist" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT UPDATE ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT UPDATE ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT UPDATE ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT REFERENCES,TRIGGER,TRUNCATE,MAINTAIN ON TABLES TO "service_role";































