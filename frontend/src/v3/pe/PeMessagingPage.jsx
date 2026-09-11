// frontend/src/v3/pe/PeMessagingPage.jsx
// WS4 — D39 PE ↔ CarbonTally Operations operational messaging in the PEShell.
// Lists THIS entity's operational conversations (entity-scoped), opens a
// thread and sends/replies. Customers, consultants and other PEs are never
// participants here (server-authoritative).
import React, { useCallback, useEffect, useState } from 'react';
import {
  createEntityConversation,
  listEntityConversations,
  listEntityMessages,
  markEntityConversationRead,
  sendEntityMessage,
} from '../api';
import { Alert, Button, LoadingState, TextInput } from '../components/ui';
import '../ops/ops.css';
import '../ops/v12.css';

export default function PeMessagingPage() {
  const [convs, setConvs] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [subject, setSubject] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const body = await listEntityConversations();
      setConvs(body.conversations || []);
      if (active) {
        const m = await listEntityMessages(active);
        setMessages(m.messages || []);
        await markEntityConversationRead(active);
      }
    } catch (e) {
      setError(e.message || 'Unable to load PE operational conversations.');
    } finally {
      setLoading(false);
    }
  }, [active]);

  useEffect(() => { load(); }, [load, refresh]);

  const open = async (id) => {
    setActive(id);
    setRefresh((k) => k + 1);
  };

  const create = async () => {
    if (!subject.trim()) return;
    setBusy(true);
    setError('');
    try {
      await createEntityConversation({ subject: subject.trim() });
      setSubject('');
      setNotice('Operational conversation created — CarbonTally Operations can now respond.');
      setRefresh((k) => k + 1);
    } catch (e) {
      setError(e.message || 'Could not create conversation.');
    } finally {
      setBusy(false);
    }
  };

  const send = async () => {
    if (!active || !draft.trim()) return;
    setBusy(true);
    setError('');
    try {
      await sendEntityMessage(active, draft.trim());
      setDraft('');
      setRefresh((k) => k + 1);
    } catch (e) {
      setError(e.message || 'Could not send message.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <LoadingState label="Loading PE operational messages…" />;

  return (
    <div className="v3-ops-page">
      <div className="v3-ops-header">
        <div>
          <h1>Operations messages</h1>
          <div className="subtitle">PE ↔ CarbonTally Operations (your entity only)</div>
        </div>
      </div>
      {error && <Alert tone="error" title="Failed">{error}</Alert>}
      {notice && <Alert tone="success" title="Done">{notice}</Alert>}

      <div className="v12-panel" style={{ marginBottom: 12 }}>
        <h3 style={{ marginTop: 0 }}>Open an operational conversation with CarbonTally</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <TextInput
            label="Subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="e.g. Clarification on assigned batch"
          />
          <Button disabled={busy || !subject.trim()} onClick={create}>Start conversation</Button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(240px, 320px) 1fr', gap: 12, alignItems: 'start' }}>
        <div className="v12-panel">
          <h3 style={{ marginTop: 0 }}>Conversations</h3>
          {convs.length === 0 ? (
            <div className="v12-muted">No operational conversations yet.</div>
          ) : (
            convs.map((c) => (
              <button
                key={c.id}
                type="button"
                className="v12-conv-row"
                onClick={() => open(c.id)}
                style={{ display: 'block', width: '100%', textAlign: 'left', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 8, marginBottom: 6, cursor: 'pointer', background: active === c.id ? '#f0fdfa' : '#fff' }}
              >
                <strong>{c.subject}</strong>
                <div className="v12-muted">{c.message_count} messages</div>
              </button>
            ))
          )}
        </div>

        <div className="v12-panel">
          <h3 style={{ marginTop: 0 }}>{active ? 'Conversation' : 'Select a conversation'}</h3>
          {!active ? (
            <div className="v12-muted">Open a conversation to view the thread.</div>
          ) : (
            <>
              <div style={{ maxHeight: '45vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 10 }}>
                {messages.map((m) => (
                  <div key={m.id} className="v12-msg" style={{ background: '#f8fafc', borderRadius: 8, padding: '6px 10px' }}>
                    <div className="v12-muted">{m.sender_id === 'you' ? 'You' : 'Participant'} · {m.created_at}</div>
                    <div>{m.content}</div>
                  </div>
                ))}
                {messages.length === 0 && <div className="v12-muted">No messages yet — send the first one.</div>}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <TextInput label="Reply" value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Reply to CarbonTally Operations…" />
                <Button disabled={busy || !draft.trim()} onClick={send}>Send</Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
