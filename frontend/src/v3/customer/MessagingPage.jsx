// frontend/src/v3/customer/MessagingPage.jsx
// D27 / D19 §16 — Consultant-client messaging through CarbonTally (Realtime).
import React, { useEffect, useState } from 'react';
import {
  createMessagingConversation,
  listMessagingConversations,
  listMessagingMessages,
  resolveV3Organization,
  sendMessagingMessage,
} from '../api';
import { ErrorState } from '../components/StateViews';

export default function MessagingPage() {
  const [org, setOrg] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [subject, setSubject] = useState('');
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const loadConversations = async (organizationId) => {
    const result = await listMessagingConversations(organizationId);
    setConversations(result.conversations || []);
  };

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const organization = await resolveV3Organization();
        if (!organization) {
          setError('No organization is linked to this account.');
          return;
        }
        setOrg(organization);
        await loadConversations(organization.id);
      } catch (e) {
        setError(e.message || 'Failed to load conversations');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [retryCount]);

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

  const onCreateConversation = async () => {
    if (!org || !subject.trim()) return;
    setError('');
    try {
      const result = await createMessagingConversation(org.id, subject.trim());
      setSubject('');
      setNotice('Conversation created.');
      await loadConversations(org.id);
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
  if (error && !org) return <ErrorState message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  return (
    <div className="v3-page">
      <div className="v3-page-header">
        <h1>Messages</h1>
        <p className="v3-subtitle">Conversations between your organisation and your consultants</p>
      </div>

      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note" style={{ marginBottom: 14 }}>{notice}</div>}

      <div className="v3-card">
        <h2>Start a conversation</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Subject (e.g. Documentation request)"
            maxLength={300}
          />
          <button className="v3-btn v3-btn-primary" onClick={onCreateConversation} disabled={!subject.trim()}>
            Create
          </button>
        </div>
      </div>

      <div className="v3-card">
        <h2>Conversations ({conversations.length})</h2>
        {conversations.length === 0 ? (
          <div className="v3-empty">No conversations yet.</div>
        ) : (
          <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
            {conversations.map((conversation) => (
              <li key={conversation.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--v3-border, #e5e7eb)' }}>
                <button
                  className="v3-link"
                  onClick={() => openConversation(conversation.id)}
                  style={{ textAlign: 'left', background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.95rem' }}
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
      </div>

      {activeConversation && (
        <div className="v3-card">
          <h2>Conversation</h2>
          <div className="v3-message-thread" style={{ maxHeight: 360, overflowY: 'auto', marginBottom: 12 }}>
            {messages.length === 0 ? (
              <div className="v3-empty">No messages yet — say hello.</div>
            ) : (
              messages.map((message) => (
                <div key={message.id} style={{ marginBottom: 10 }}>
                  <div className="v3-muted">
                    {new Date(message.created_at).toLocaleString()}
                  </div>
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
