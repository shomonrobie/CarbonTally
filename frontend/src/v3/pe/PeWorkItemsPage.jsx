// frontend/src/v3/pe/PeWorkItemsPage.jsx
// WS4 — D38 work-item surface inside the dedicated PE application. Lists the
// items effectively assigned to THIS entity (item-level open assignment else
// batch default — resolved server-side by /api/v3/pe/*), shows current
// assignment state + history, and exposes Claim / Release / Complete.
// Item-level assignment changes are governed by CarbonTally Operations only;
// PE-initiated reassignment controls are intentionally absent. Every control
// calls the canonical /api/v3/pe/items/{id}/work/* endpoints; the UI never
// authorizes locally.
import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getPeBatchItems,
  getPeMe,
  getPeWork,
  peWorkClaim,
  peWorkComplete,
  peWorkInfo,
  peWorkRelease,
} from '../api';
import DataTable from '../components/ui/DataTable';
import { Alert, Button, LoadingState } from '../components/ui';
import '../ops/ops.css';
import '../ops/v12.css';

function AssignmentCell({ itemId }) {
  const [info, setInfo] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    peWorkInfo(itemId)
      .then((d) => { if (active) setInfo(d); })
      .catch((e) => { if (active) setError(e.message || 'Failed'); });
    return () => { active = false; };
  }, [itemId]);
  if (error) return <span className="v12-muted">{error}</span>;
  if (!info) return <span className="v12-muted">…</span>;
  const current = info.current;
  const label = current
    ? `Claimed (${current.processing_entity_id ? 'this entity' : '—'})`
    : 'Unclaimed';
  return (
    <div>
      <span className="v12-stage">{label}</span>
      <details style={{ marginTop: 4 }}>
        <summary className="v12-muted" style={{ cursor: 'pointer' }}>History ({info.history?.length || 0})</summary>
        <ul style={{ paddingLeft: 14, margin: '6px 0', fontSize: '0.8rem', color: '#334155' }}>
          {(info.history || []).map((h) => (
            <li key={h.id}>
              {h.action}{h.close_action ? ` → ${h.close_action}` : ''} · by {h.actor_domain} · {h.created_at}
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}

export default function PeWorkItemsPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [actionError, setActionError] = useState('');
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const me = await getPeMe();
      const work = await getPeWork();
      const out = [];
      for (const batch of work.batches || []) {
        const body = await getPeBatchItems(batch.id);
        for (const item of body.items || []) {
          out.push({ ...item, batch_name: batch.batch_name, entity_id: me.entity.id });
        }
      }
      setRows(out);
    } catch (e) {
      setError(e.message || 'Unable to load assigned work.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load, refresh]);

  const act = async (itemId, fn, okLabel) => {
    setBusy(true);
    setActionError('');
    setNotice('');
    try {
      await fn();
      setNotice(okLabel);
      setRefresh((k) => k + 1);
    } catch (e) {
      setActionError(e.message || 'Action failed.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <LoadingState label="Loading assigned work…" />;
  if (error && rows.length === 0) return <Alert tone="error" title="Failed to load">{error}</Alert>;

  return (
    <div className="v3-ops-page">
      <div className="v3-ops-header">
        <div>
          <h1>Assigned work</h1>
          <div className="subtitle">{rows.length} item{rows.length === 1 ? '' : 's'} for your Processing Entity</div>
        </div>
        <Link to="/pe" className="v3-btn v3-btn-secondary">← Back</Link>
      </div>
      {notice && <Alert tone="success" title="Action recorded">{notice}</Alert>}
      {actionError && <Alert tone="error" title="Action not applied">{actionError}</Alert>}

      {rows.length === 0 ? (
        <Alert tone="info" title="No assigned work">
          CarbonTally has not assigned any items to your Processing Entity yet.
        </Alert>
      ) : (
        <DataTable
          caption="PE assigned work — current assignment, attribution and D38 actions"
          rowKey="id"
          rows={rows}
          columns={[
            { key: 'file', header: 'Item', accessor: 'file_name', render: (r) => r.file_name || r.id },
            { key: 'batch', header: 'Batch', accessor: 'batch_name' },
            { key: 'status', header: 'State', accessor: 'status', sortable: true },
            { key: 'assignment', header: 'Assignment', accessor: 'id', render: (r) => <AssignmentCell itemId={r.id} /> },
            {
              key: 'actions',
              header: 'D38 actions',
              accessor: 'id',
              render: (r) => (
                <div className="v12-actions">
                  <Button size="sm" variant="primary" disabled={busy} onClick={() => act(r.id, () => peWorkClaim(r.id), 'Item claimed.')}>
                    Claim
                  </Button>
                  <Button size="sm" disabled={busy} onClick={() => act(r.id, () => peWorkRelease(r.id), 'Item released.')}>
                    Release
                  </Button>
                  <Button size="sm" disabled={busy} onClick={() => act(r.id, () => peWorkComplete(r.id), 'Item completed.')}>
                    Complete
                  </Button>
                </div>
              ),
            },
          ]}
        />
      )}
    </div>
  );
}
