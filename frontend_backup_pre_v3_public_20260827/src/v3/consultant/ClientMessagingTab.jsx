// frontend/src/v3/consultant/ClientMessagingTab.jsx
// D27 / D19 §16 — consultant -> client messaging through CarbonTally (Realtime).
import React, { useEffect, useState } from 'react';
import {
  createMessagingConversation,
  listMessagingConversations,
  listMessagingMessages,
  sendMessagingMessage,
} from '../api';

export default function ClientMessagingTab({ client }) {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [subject, setSubject] = useState('');
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const loadConversations = async () => {
    const result = await listMessagingConversations(client.organization_id);
    setConversations(result.conversations || []);
  };

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        if (!client?.organization_id) return;
        await loadConversations();
      } catch (e) {
        setError(e.message || 'Failed to load conversations');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client?.organization_id]);

  const openConversation = async (conversationId) => {
    setError('');
    setActiveConversation(conversationId);
    try {
      const result = await listMessagingMessages(conversationId);
      setMessages(result.messages || []);
    } catch (e) {
      setError(e.message || 'Failed to load messages');
    }
  };

  const onCreate = async () => {
    if (!subject.trim()) return;
    setError('');
    try {
      const result = await createMessagingConversation(client.organization_id, subject.trim());
      setSubject('');
      await loadConversations();
      setActiveConversation(result.conversation.id);
      setMessages([]);
    } catch (e) {
      setError(e.message || 'Failed to create conversation');
    }
  };

  const onSend = async () => {
    if (!activeConversation || !draft.trim()) return;
    setSending(true);
    setError('');
    try {
      await sendMessagingMessage(activeConversation, draft.trim());
      setDraft('');
      await openConversation(activeConversation);
    } catch (e) {
      setError(e.message || 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  if (loading) return <div className="v3-loading"><div className="spinner" />Loading messages…</div>;

  return (
    <div className="v3-admin-card">
      <h2>Client messaging — {client?.client_name}</h2>
      <p className="v3-muted">
        Messages with this client are exchanged through CarbonTally (Supabase
        Realtime). Processing entities never participate in these conversations.
      </p>
      {error && <div className="v3-error" style={{ marginBottom: 12 }}>{error}</div>}

      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <input
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="New conversation subject"
          maxLength={300}
        />
        <button className="v3-btn v3-btn-primary" onClick={onCreate} disabled={!subject.trim()}>
          Start
        </button>
      </div>

      {conversations.length === 0 ? (
        <div className="v3-empty">No conversations yet.</div>
      ) : (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
          {conversations.map((conversation) => (
            <li key={conversation.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--v3-border, #e5e7eb)' }}>
              <button
                className="v3-link"
                onClick={() => openConversation(conversation.id)}
                style={{ textAlign: 'left', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                {conversation.subject}
                <span className="v3-muted" style={{ marginLeft: 8 }}>
                  ({conversation.message_count || 0} messages)
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {activeConversation && (
        <div style={{ marginTop: 16 }}>
          <div className="v3-message-thread" style={{ maxHeight: 320, overflowY: 'auto', marginBottom: 10 }}>
            {messages.length === 0 ? (
              <div className="v3-empty">No messages yet.</div>
            ) : (
              messages.map((message) => (
                <div key={message.id} style={{ marginBottom: 10 }}>
                  <div className="v3-muted">{new Date(message.created_at).toLocaleString()}</div>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
                </div>
              ))
            )}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Write a message…"
              rows={2}
              maxLength={20000}
            />
            <button className="v3-btn v3-btn-primary" onClick={onSend} disabled={sending || !draft.trim()}>
              {sending ? 'Sending…' : 'Send'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
