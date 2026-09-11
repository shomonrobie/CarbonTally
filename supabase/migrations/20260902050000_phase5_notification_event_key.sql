-- ============================================================
-- CarbonTally Phase 5 — WS3 / D40: notification event producers
-- support. Additive + idempotent.
--  * event_key: deterministic dedupe key per (recipient, business event) so
--    retried producers can never create duplicate notifications.
--  * actor_domain / source link support already exists via existing columns.
-- Existing notifications (0 today) and semantics preserved.
-- ============================================================

ALTER TABLE public.notifications
    ADD COLUMN IF NOT EXISTS event_key text;

ALTER TABLE public.notifications
    ADD COLUMN IF NOT EXISTS actor_domain text;

CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_event_key
    ON public.notifications (recipient_id, event_key)
    WHERE event_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_notifications_recipient_inbox
    ON public.notifications (recipient_type, recipient_id, is_read, created_at DESC);
