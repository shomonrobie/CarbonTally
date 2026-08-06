-- ============================================================================
-- CarbonTally v1.0 RC2 — Production Hardening Migration (REPAIR RELEASE)
-- File 003 of 008: Indexes & lookup-path repair
-- Source of truth:
--   * Baseline: supabase/migrations/00000000000000_init_schema.sql
--   * CarbonTally RC1 — Independent Database Audit.md
--   * CarbonTally_v1.0_Structural_Change_Review.md (APPROVE items only)
-- Database: PostgreSQL 16 (Supabase). Schema: public.
--
-- BASELINE REALITY (verified against the actual init file): the RC1 I1–I5
-- performance family and the four FK-supporting indexes are ALREADY CREATED in
-- the baseline init. RC2 003 therefore:
--   1. RECONCILES that family with IF NOT EXISTS so the suite self-heals on any
--      scheme that started without a given index (and re-runs cleanly); and
--   2. ADDS the two indexes the audit/RI policy still required and that the
--      baseline omitted:
--        * L3 — password_reset_tokens.user_id  → non-unique lookup index
--        * FK-support on document_processing_queue.emission_factor_used (the
--          F1 FK to emission_factors(id) gains a proper leading-column index,
--          matching the emissions_logs_emission_factor_id_idx pattern).
--
-- WHY NOT CONCURRENTLY: the Supabase migration runner (`supabase db reset`)
-- applies migrations inside a single pipeline, where CREATE INDEX CONCURRENTLY
-- is illegal (SQLSTATE 25001). A db reset rebuilds an empty database, so there
-- are no concurrent writers to guard against; plain CREATE INDEX IF NOT EXISTS
-- is safe and idempotent. Each statement is self-contained; a failure is
-- non-destructive (only the offending index is skipped) and can be re-run.
-- A NOTE: after dropping/rebuilding the factor UNIQUE index in 002, this file
-- never re-creates it here — 002 owns the factor natural key.
-- ============================================================================

-- ============================================================================

-- The trigram indexes below need pg_trgm. The baseline init only enables
-- uuid-ossp and pgcrypto, so enable it here (idempotent).
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- SECTION 1 — RECONCILE THE RC1 PERFORMANCE + FK-SUPPORT FAMILY (I1–I5, FK)
-- ============================================================================
-- All IF NOT EXISTS: absent on this scheme → created; present → no-op. Plain
-- (non-CONCURRENTLY) creation because the Supabase migration runner pipelines
-- statements and CONCURRENTLY is illegal there; db reset builds an empty DB.

-- I1 — tenant composites
CREATE INDEX IF NOT EXISTS customer_documents_org_created_idx
    ON public.customer_documents (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS emissions_logs_org_start_date_idx
    ON public.emissions_logs (organization_id, start_date);
CREATE INDEX IF NOT EXISTS suppliers_org_idx
    ON public.suppliers (organization_id);
CREATE INDEX IF NOT EXISTS facilities_org_idx
    ON public.facilities (organization_id);

-- I2 — queue-claim partials
CREATE INDEX IF NOT EXISTS dpq_claim_idx
    ON public.document_processing_queue (status, created_at)
    WHERE status IN ('pending','processing','manual_review','manual_extraction','qc','customer_review');
CREATE INDEX IF NOT EXISTS processing_queue_claim_idx
    ON public.processing_queue (queue_status, created_at)
    WHERE queue_status IN ('pending','assigned','in_progress');
CREATE INDEX IF NOT EXISTS report_generation_queue_claim_idx
    ON public.report_generation_queue (status, created_at)
    WHERE status IN ('pending','queued','processing');

-- I3 — messaging / notifications
CREATE INDEX IF NOT EXISTS messages_conversation_created_idx
    ON public.messages (conversation_id, created_at);
CREATE INDEX IF NOT EXISTS conversation_participants_conv_user_idx
    ON public.conversation_participants (conversation_id, user_id);
CREATE INDEX IF NOT EXISTS notifications_unread_recipient_idx
    ON public.notifications (recipient_id, created_at)
    WHERE is_read = false;

-- I4 — consultant access GIN
CREATE INDEX IF NOT EXISTS consultant_firm_members_client_access_gin
    ON public.consultant_firm_members USING gin (client_access);

-- I5 — trigram (pg_trgm enabled by baseline init)
CREATE INDEX IF NOT EXISTS suppliers_name_trgm_idx
    ON public.suppliers USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS suppliers_vat_number_trgm_idx
    ON public.suppliers USING gin (vat_number gin_trgm_ops);
CREATE INDEX IF NOT EXISTS organizations_name_trgm_idx
    ON public.organizations USING gin (name gin_trgm_ops);

-- FK-support pair on emissions_logs
CREATE INDEX IF NOT EXISTS emissions_logs_emission_factor_id_idx
    ON public.emissions_logs (emission_factor_id);
CREATE INDEX IF NOT EXISTS emissions_logs_asset_id_idx
    ON public.emissions_logs (asset_id);

-- FK-support on customer_documents
CREATE INDEX IF NOT EXISTS customer_documents_supplier_id_idx
    ON public.customer_documents (supplier_id);
CREATE INDEX IF NOT EXISTS customer_documents_document_type_id_idx
    ON public.customer_documents (document_type_id);

-- FK-support on document_processing_queue (customer_document_id)
CREATE INDEX IF NOT EXISTS dpq_customer_document_id_idx
    ON public.document_processing_queue (customer_document_id);

-- ============================================================================
-- SECTION 2 — RC2 ADDITIONS: indexes the baseline omitted
-- ============================================================================

-- ---------------------------------------------------------------------------
-- L3 — password_reset_tokens.user_id lookup index
-- ---------------------------------------------------------------------------
-- Audit L3: password_reset_tokens.user_id is queried when validating a reset
-- request (and, after ER1-a, when a user is erased). The baseline declares
-- the column as plain (non-unique — correct: multiple outstanding tokens are
-- legitimate) but adds NO index, so every user_id lookup is a seq scan. This
-- pays for itself on the small reset-token table and is a cheap, safe add.
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS password_reset_tokens_user_id_idx
    ON public.password_reset_tokens (user_id);

-- ---------------------------------------------------------------------------
-- FK-support on document_processing_queue.emission_factor_used
-- ---------------------------------------------------------------------------
-- The F1 foreign key document_processing_queue.emission_factor_used →
-- emission_factors(id) exists in the baseline, but the baseline only indexes
-- the (customer_document_id) column. A leading column for the factor join/
-- update path gives us the same protection as emissions_logs_emission_factor_id_idx.
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS dpq_emission_factor_used_idx
    ON public.document_processing_queue (emission_factor_used);

-- ============================================================================
-- EXPLICITLY NOT IMPLEMENTED HERE (register verification):
--   * pg_trgm extension — already created by the baseline init (safe to
--     assume; 007 re-checks it). Re-check in 007 Section 4e.
--   * Full-text search GIN on organisation notes/description — out of scope.
--   * Partial indexes on notification unread beyond I3 — not required.
--   * Index on messages.sender_id / receiver_id — not an audited hot path.
--   * Any index on anonymise/erasure fields — covered by L3 + PKs.
--
-- ROLLBACK: drop only the two Section-2 additions if reverting to the RC1
-- index set; the Section-1 quotes are all baseline-owned and left intact:
--   DROP INDEX CONCURRENTLY IF EXISTS public.password_reset_tokens_user_id_idx;
--   DROP INDEX CONCURRENTLY IF EXISTS public.dpq_emission_factor_used_idx;
-- ============================================================================

-- End of 003_rc2_indexes.sql
