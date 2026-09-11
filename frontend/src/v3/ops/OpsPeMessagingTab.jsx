// frontend/src/v3/ops/OpsPeMessagingTab.jsx
// WS4 — D39 Operations side: authorised CarbonTally Operations (internal
// staff with can_manage_staff) can list PE operational conversations, open a
// thread and reply. Read/RSent through the same canonical entity messaging
// endpoints as the PE surface. Customers/consultants/PEs never appear here.
import React, { useCallback, useEffect, useState } from 'react';
import {
  listEntityConversations,
  listEntityMessages,
  sendEntityMessage,
} from '../api';
import { Alert, Button, LoadingState, TextInput } from '../components/ui';

export default function OpsPeMessagingTab() {
  const [convs, setConvs] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
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
      }
    } catch (e) {
      setError(e.message || 'Unable to load PE operational conversations.');
    } finally {
      setLoading(false);
    }
  }, [active]);

  useEffect(() => { load(); }, [load, refresh]);

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

  if (loading) return <LoadingState label="Loading PE operational conversations…" />;

  return (
    <div className="v3-ops-page">
      {error && <Alert tone="error" title="Failed">{error}</Alert>}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(240px, 340px) 1fr', gap: 12, alignItems: 'start' }}>
        <div className="v12-panel">
          <h3 style={{ marginTop: 0 }}>PE operational conversations</h3>
          {convs.length === 0 ? (
            <div className="v12-muted">No PE operational conversations.</div>
          ) : (
            convs.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => { setActive(c.id); setRefresh((k) => k + 1); }}
                style={{ display: 'block', width: '100%', textAlign: 'left', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 8, marginBottom: 6, cursor: 'pointer', background: active === c.id ? '#f0fdfa' : '#fff' }}
              >
                <strong>{c.subject}</strong>
                <div className="v12-muted">Entity {c.processing_entity_id ? String(c.processing_entity_id).slice(0, 8) : '—'} · {c.message_count} messages</div>
              </button>
            ))
          )}
        </div>
        <div className="v12-panel">
          <h3 style={{ marginTop: 0 }}>{active ? 'Thread' : 'Select a conversation'}</h3>
          {!active ? (
            <div className="v12-muted">Open a PE operational conversation to respond.</div>
          ) : (
            <>
              <div style={{ maxHeight: '45vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 10 }}>
                {messages.map((m) => (
                  <div key={m.id} className="v12-msg" style={{ background: '#f8fafc', borderRadius: 8, padding: '6px 10px' }}>
                    <div className="v12-muted">{m.sender_id} · {m.created_at}</div>
                    <div>{m.content}</div>
                  </div>
                ))}
                {messages.length === 0 && <div className="v12-muted">No messages yet.</div>}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <TextInput label="Reply" value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Reply to the Processing Entity…" />
                <Button disabled={busy || !draft.trim()} onClick={send}>Send</Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
