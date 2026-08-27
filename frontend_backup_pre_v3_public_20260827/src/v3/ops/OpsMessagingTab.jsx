// frontend/src/v3/ops/OpsMessagingTab.jsx
// N1 — CarbonTally Support / Authorised Admin messaging surface. Scoped to an
// organisation the staff member is authorised for (staff-admin permission is
// enforced server-side by /api/v3/messaging — this UI never bypasses it).
// General employees and Processing Entity staff are denied server-side.
import React, { useCallback, useEffect, useState } from 'react';
import {
  createMessagingConversation,
  getOpsDashboard,
  listMessagingConversations,
  listMessagingMessages,
  sendMessagingMessage,
} from '../api';
import { LoadingState, Alert, Button, SelectInput, TextInput } from '../components/ui';

export default function OpsMessagingTab({ canManage }) {
  const [orgs, setOrgs] = useState([]);
  const [orgId, setOrgId] = useState('');
  const [conversations, setConversations] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [subject, setSubject] = useState('');
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const loadOrgs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getOpsDashboard();
      setOrgs(result.organizations || []);
      if ((result.organizations || []).length > 0) {
        setOrgId((current) => current || result.organizations[0].id);
      }
    } catch (e) {
      setError(e.message || 'Failed to load organisations');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadOrgs(); }, [loadOrgs, retryCount]);

  const loadConversations = useCallback(async (selectedOrgId) => {
    if (!selectedOrgId) return;
    try {
      const result = await listMessagingConversations(selectedOrgId);
      setConversations(result.conversations || []);
    } catch (e) {
      setError(e.message || 'Failed to load conversations');
    }
  }, []);

  useEffect(() => {
    if (!orgId) return;
    loadConversations(orgId);
  }, [orgId, loadConversations, retryCount]);

  const openConversation = async (conversationId) => {
    setError('');
    setActive(conversationId);
    try {
      const result = await listMessagingMessages(conversationId);
      setMessages(result.messages || []);
    } catch (e) {
      setError(e.message || 'Failed to load messages');
    }
  };

  const onCreateConversation = async () => {
    if (!orgId || !subject.trim()) return;
    setSending(true);
    setError('');
    try {
      await createMessagingConversation(orgId, subject.trim());
      setSubject('');
      setNotice('Conversation created.');
      setTimeout(() => setNotice(''), 4000);
      await loadConversations(orgId);
    } catch (e) {
      setError(e.message || 'Failed to create conversation');
    } finally {
      setSending(false);
    }
  };

  const onSend = async () => {
    if (!active || !draft.trim()) return;
    setSending(true);
    setError('');
    try {
      await sendMessagingMessage(active, draft.trim());
      setDraft('');
      const result = await listMessagingMessages(active);
      setMessages(result.messages || []);
    } catch (e) {
      setError(e.message || 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  if (loading) return <LoadingState label="Loading messaging…" />;

  if (!canManage) {
    return (
      <Alert tone="info" title="Messaging is admin-managed">
        The CarbonTally support messaging surface is reserved for staff with staff-admin permissions (N1).
      </Alert>
    );
  }

  return (
    <div>
      {notice && <Alert tone="success" title="Done">{notice}</Alert>}
      {error && <Alert tone="error" title="Action failed">{error}</Alert>}

      <div className="v3-form-grid" style={{ marginBottom: 12 }}>
        <SelectInput
          label="Organisation context"
          value={orgId}
          onChange={(e) => { setOrgId(e.target.value); setActive(null); setMessages([]); }}
        >
          {orgs.map((o) => <option key={o.id} value={o.id}>{o.name || o.id}</option>)}
        </SelectInput>
      </div>

      <div className="workspace-grid">
        <div className="workspace-pane">
          <h3>Conversations</h3>
          {conversations.length === 0 && <p className="v3-muted">No conversations for this organisation.</p>}
          {conversations.map((conv) => (
            <button
              key={conv.id}
              type="button"
              className={`entity-row${active === conv.id ? ' active' : ''}`}
              onClick={() => openConversation(conv.id)}
            >
              <strong>{conv.subject}</strong>
              <span className="muted">{conv.message_count || 0} messages</span>
            </button>
          ))}
          <div style={{ marginTop: 12 }}>
            <TextInput
              label="New conversation subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Subject"
            />
            <Button variant="primary" icon="plus" loading={sending} onClick={onCreateConversation} disabled={!subject.trim()}>
              Start conversation
            </Button>
          </div>
        </div>

        <div className="workspace-pane">
          <h3>Thread</h3>
          {!active ? (
            <p className="v3-muted">Select a conversation to read and reply.</p>
          ) : messages.length === 0 ? (
            <p className="v3-muted">No messages yet.</p>
          ) : (
            messages.map((m) => (
              <div key={m.id} className="v3-message-thread" style={{ marginBottom: 8 }}>
                <div className="v3-muted" style={{ fontSize: 12 }}>
                  {(m.sender_id || '')?.slice(0, 12)} · {m.created_at ? new Date(m.created_at).toLocaleString() : ''}
                </div>
                <div style={{ marginTop: 2 }}>{m.content}</div>
              </div>
            ))
          )}
          {active && (
            <div style={{ marginTop: 12 }}>
              <TextInput
                label="Reply"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Write a reply…"
              />
              <Button variant="primary" icon="send" loading={sending} onClick={onSend} disabled={!draft.trim()}>
                Send
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

