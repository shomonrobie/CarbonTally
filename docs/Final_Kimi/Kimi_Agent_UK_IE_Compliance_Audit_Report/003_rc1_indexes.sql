-- ============================================================================
-- CarbonTally v1.0 RC1 — Production Hardening Migration
-- File 003 of 008: Approved targeted index families (I1–I5 + FK-supporting)
-- Source of truth: CarbonTally_v1.0_Structural_Change_Review.md §4.
--   APPROVED: I1 tenant composites, I2 queue-claim partials, I3 messaging/
--   notifications, I4 client_access GIN, I5 pg_trgm trigram family.
--   REJECTED and intentionally absent: I6 blanket "index every FK" programme
--   (~60 indexes). FK-supporting indexes below are limited to the F1
--   remediation columns on hot pipeline tables (real query entry points).
--
-- *** WHY THIS FILE IS NON-TRANSACTIONAL ***
-- Every index below is built with CREATE INDEX CONCURRENTLY so that builds
-- never take an ACCESS EXCLUSIVE lock on live tables (Supabase production).
-- CONCURRENTLY CANNOT run inside a transaction block, so this file must:
--   * contain NO BEGIN/COMMIT wrapping,
--   * be run OUTSIDE a transaction (e.g. applied statement-by-statement via
--     `psql -f` against the Supabase connection, NOT wrapped by a migration
--     runner that auto-transactions; on Supabase, run it in the SQL editor or
--     via a migration with transactions disabled),
--   * tolerate failure of any single statement: each statement is independent
--     and idempotent (IF NOT EXISTS), so re-running the file after a failure
--     is safe. Note: a failed CONCURRENTLY build can leave an INVALID index;
--     drop it (DROP INDEX CONCURRENTLY IF EXISTS <name>;) and re-run.
-- One statement per index, as required.
--
-- Caveat carried from the review: the dump shows no indexes; per the
-- hardening plan's "action zero", inspect existing Supabase migration files
-- first — each family below then collapses from "build" to "verify".
-- ============================================================================

-- Pre-requisite for the I5 trigram family (idempotent; CREATE EXTENSION is
-- permitted outside a transaction and in its own implicit transaction).
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Pre-requisite for anonymise_user() in 005: sha256() lives in pgcrypto
-- (GDPR erasure email hash). Idempotent; also permitted outside a transaction.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- I1 — Tenant composite family (APPROVE)
-- RLS-join paths on the four hot tenant tables; ordering column matches the
-- dominant list/rollup query on the two pipeline tables.
-- ============================================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS customer_documents_org_created_idx
    ON public.customer_documents (organization_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS emissions_logs_org_start_date_idx
    ON public.emissions_logs (organization_id, start_date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS suppliers_org_idx
    ON public.suppliers (organization_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS facilities_org_idx
    ON public.facilities (organization_id);

-- ============================================================================
-- I2 — Queue-claim partial family (APPROVE)
-- Restricted to unclaimed/active statuses so each index stays small and hot.
-- The partial predicates MUST match the worker claim queries exactly or the
-- indexes are silently unused (Gate 7 query-plan check). If the claim query
-- uses a different status vocabulary, align the predicate here to it — after
-- the K4 value-list audit in 002.
-- ============================================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS dpq_claim_idx
    ON public.document_processing_queue (status, created_at)
    WHERE status IN ('pending','processing','manual_review','manual_extraction','qc','customer_review');

CREATE INDEX CONCURRENTLY IF NOT EXISTS processing_queue_claim_idx
    ON public.processing_queue (queue_status, created_at)
    WHERE queue_status IN ('pending','assigned','in_progress');

CREATE INDEX CONCURRENTLY IF NOT EXISTS report_generation_queue_claim_idx
    ON public.report_generation_queue (status, created_at)
    WHERE status IN ('pending','queued','processing');

-- ============================================================================
-- I3 — Messaging/notifications family (APPROVE)
-- Thread timeline, participant lookup, unread-notification badge count.
-- ============================================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS messages_conversation_created_idx
    ON public.messages (conversation_id, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS conversation_participants_conv_user_idx
    ON public.conversation_participants (conversation_id, user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS notifications_unread_recipient_idx
    ON public.notifications (recipient_id, created_at)
    WHERE is_read = false;

-- ============================================================================
-- I4 — consultant_firm_members.client_access array GIN (APPROVE)
-- The sole justified GIN in v1.0: the ADR-locked uuid[] access-grant column
-- evaluated in consultant RLS predicates.
-- ============================================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS consultant_firm_members_client_access_gin
    ON public.consultant_firm_members USING gin (client_access);

-- ============================================================================
-- I5 — pg_trgm trigram family (APPROVE; v1.0.x window acceptable)
-- Fuzzy supplier/org matching for autocomplete and "did you mean?" duplicate
-- prompts — the soft control complementing K5's hard identifier uniqueness.
-- Scoped to exactly the three approved columns (no wider trigram programme).
-- ============================================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS suppliers_name_trgm_idx
    ON public.suppliers USING gin (name gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS suppliers_vat_number_trgm_idx
    ON public.suppliers USING gin (vat_number gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS organizations_name_trgm_idx
    ON public.organizations USING gin (name gin_trgm_ops);

-- ============================================================================
-- FK-supporting indexes (F1 companions — hot pipeline entry points only;
-- NOT the rejected I6 blanket programme)
-- Supporting the F1 remediation FKs that are genuine query entry points:
-- factor/asset/supplier joins on the emissions and pipeline tables. Each is
-- individually justified by the join paths in F1; non-entry-point FKs are
-- revisited evidence-gated in v1.1 against query logs (review §4 I6).
-- ============================================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS emissions_logs_emission_factor_id_idx
    ON public.emissions_logs (emission_factor_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS emissions_logs_asset_id_idx
    ON public.emissions_logs (asset_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS customer_documents_supplier_id_idx
    ON public.customer_documents (supplier_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS dpq_customer_document_id_idx
    ON public.document_processing_queue (customer_document_id);

-- ============================================================================
-- End of 003_rc1_indexes.sql — 18 indexes total:
--   I1 ×4, I2 ×3, I3 ×3, I4 ×1, I5 ×3, FK-supporting ×4.
-- (K5's six UNIQUE-backed indexes were built in 002 and are counted there,
-- per the review; I6 rejected programme intentionally absent.)
-- ============================================================================
