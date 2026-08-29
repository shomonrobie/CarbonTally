// frontend/src/v3/messaging/useConversationRealtime.js
// CL-64 — conversation-specific Supabase Realtime subscription for V3 messaging.
//
// Security model: the subscription uses a `postgres_changes` filter scoped to
// one conversation id. Supabase Realtime only delivers rows the authenticated
// client is ALLOWED to SELECT via RLS — the `messages`/`conversations` RLS is
// org-member / active-consultant-grant / staff-admin only, so this never opens
// a global or cross-tenant stream (Processing Entity staff remain denied).
//
// Reconnect/backoff is handled by the Supabase client's channel lifecycle
// (subscription status is surfaced through `onStatus`). Consumers deduplicate
// INSERT payloads by message id and always have the API refetch as the
// deterministic fallback.
import { useEffect, useRef } from 'react';
import { supabase } from '../../supabaseClient';

export function useConversationRealtime(conversationId, { onInsert, onUpdate, onStatus } = {}) {
  const cbRef = useRef({ onInsert, onUpdate, onStatus });
  cbRef.current = { onInsert, onUpdate, onStatus };

  useEffect(() => {
    if (!conversationId) return undefined;

    const channelName = `ct-msg-${conversationId}-${Date.now()}`;
    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'messages',
          filter: `conversation_id=eq.${conversationId}`,
        },
        (payload) => cbRef.current.onInsert?.(payload.new)
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'messages',
          filter: `conversation_id=eq.${conversationId}`,
        },
        (payload) => cbRef.current.onUpdate?.(payload.new)
      )
      .subscribe((status) => cbRef.current.onStatus?.(status));

    return () => {
      try {
        supabase.removeChannel(channel);
      } catch (e) {
        /* channel teardown must never throw */
      }
    };
  }, [conversationId]);

  return null;
}
