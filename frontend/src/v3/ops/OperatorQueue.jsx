// frontend/src/v3/ops/OperatorQueue.jsx
// Data-entry operator queue: operator queue + batch items + the shared D23
// extraction panel (document viewer, multi-line extraction, factor picker,
// save/resume, next/previous item).
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  assignBatch,
  calculateItem,
  extractItem,
  getMappingOptions,
  getOperatorQueue,
  getOpsBatchItems,
  getOpsMe,
  listProcessingEntities,
  listOpsStaff,
  mapItem,
  startItem,
} from '../api';
import ExtractionPanel from './ExtractionPanel';

const INTERNAL_API = {
  startItem,
  extractItem,
  mapItem,
  calculateItem,
  getMappingOptions,
};

const EMPTY_ASSIGN = { type: 'operator', target: '', reason: '' };

export default function OperatorQueue() {
  const navigate = useNavigate();
  const [batches, setBatches] = useState([]);
  const [queueTotal, setQueueTotal] = useState(0);
  const [queueLimit, setQueueLimit] = useState(25);
  const [queueOffset, setQueueOffset] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [activeBatchId, setActiveBatchId] = useState(null);
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [me, setMe] = useState(null);
  const [operators, setOperators] = useState([]);
  const [entities, setEntities] = useState([]);
  const [assignFor, setAssignFor] = useState(null);
  const [assignForm, setAssignForm] = useState({ ...EMPTY_ASSIGN });
  const [assigning, setAssigning] = useState(false);

  const canAssign = !!(
    me?.permissions?.can_manage_staff && me?.permissions?.can_process
  );

  const loadBatches = useCallback(async (limit = queueLimit, offset = queueOffset, status = statusFilter) => {
    try {
      // CL-58 — server-side pagination window over the operator queue.
      const result = await getOperatorQueue(status, limit, offset);
      setBatches(result.batches || []);
      setQueueTotal(result.total ?? result.queued ?? 0);
      setQueueLimit(limit);
      setQueueOffset(offset);
      if ((result.batches || []).length) {
        const first = result.batches[0].batch;
        setActiveBatchId(first.id);
      }
    } catch (e) {
      setError(e.message || 'Failed to load operator queue');
    }
  }, [queueLimit, queueOffset, statusFilter]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadBatches(); }, []);

  useEffect(() => {
    getOpsMe().then(setMe).catch(() => setMe(null));
    listOpsStaff()
      .then((result) =>
        setOperators((result.staff || []).filter((p) => p.is_active && !p.entity_id))
      )
      .catch(() => setOperators([]));
    listProcessingEntities()
      .then((result) =>
        setEntities((result.entities || []).filter((e) => e.status !== 'inactive'))
      )
      .catch(() => setEntities([]));
  }, []);

  const loadBatchItems = useCallback(async (batchId) => {
    try {
      const result = await getOpsBatchItems(batchId);
      const list = result.items || [];
      setItems(list);
      const pending = list.find((i) => i.status === 'pending') || list[0];
      return list;
    } catch (e) {
      setError(e.message || 'Failed to load batch items');
      return [];
    }
  }, []);

  const openBatch = async (batchId) => {
    setActiveBatchId(batchId);
    await loadBatchItems(batchId);
  };

  const openItem = async (itemId) => {
    // CL-59 — the workspace is a dedicated route, never an inline panel below
    // the queue. Queue position/filters live on the queue page; the item route
    // is deep-linkable, refresh-safe and history-aware.
    navigate(`/ops/items/${encodeURIComponent(itemId)}`);
  };

  useEffect(() => {
    if (activeBatchId && !items.length) loadBatchItems(activeBatchId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeBatchId]);

  const startAssign = (batch) => {
    setAssignFor(batch);
    setAssignForm({ ...EMPTY_ASSIGN });
    setError('');
    setNotice('');
  };

  const onAssign = async () => {
    if (!assignFor || !assignForm.target) return;
    setAssigning(true);
    setError('');
    setNotice('');
    try {
      if (assignForm.type === 'entity') {
        await assignBatch(assignFor.id, null, {
          entity_id: assignForm.target,
          reason: assignForm.reason.trim() || null,
        });
      } else {
        await assignBatch(assignFor.id, assignForm.target, { reason: assignForm.reason.trim() || null });
      }
      setNotice(`Batch assigned to ${assignForm.type === 'entity' ? 'processing entity' : 'operator'}.`);
      setAssignFor(null);
      setAssignForm({ ...EMPTY_ASSIGN });
      await loadBatches();
    } catch (e) {
      setError(e.message || 'Assignment failed');
    } finally {
      setAssigning(false);
    }
  };

  return (
    <div>
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
          <h3 style={{ margin: 0 }}>Assigned / self-serve batches ({queueTotal})</h3>
          <select
            className="ct-table-pagination-select"
            aria-label="Filter by status"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              loadBatches(queueLimit, 0, e.target.value);
            }}
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        <table className="v3-ops-table">
          <thead><tr><th>Batch</th><th>Organisation</th><th>Client of</th><th>Entity</th><th>Status</th><th>Progress</th><th>Items</th><th>Assigned</th><th>Received</th><th>Source</th><th /></tr></thead>
          <tbody>
            {batches.map((entry) => (
              <React.Fragment key={entry.batch.id}>
                <tr>
                  <td>{entry.batch.batch_name || entry.batch.id}</td>
                  <td>{entry.organization?.name || '—'}</td>
                  <td>{entry.consultant ? entry.consultant.firm_name || entry.consultant.client_name || '—' : '—'}</td>
                  <td>{entry.entity?.name || '—'}</td>
                  <td>{entry.batch.status}</td>
                  <td>{entry.progress ? `${entry.progress.pct_complete}%` : '—'}</td>
                  <td>{entry.progress?.total_items ?? '—'}</td>
                  <td>{entry.assigned_to_name || 'Unassigned'}</td>
                  <td>{entry.batch.created_at ? new Date(entry.batch.created_at).toLocaleDateString() : '—'}</td>
                  <td className="v3-muted" style={{ fontSize: 12 }}>
                    {(entry.source_items || []).join(', ') || (entry.sla?.breached ? '⚠ SLA breached' : '—')}
                  </td>
                  <td>
                    <button
                      className="v3-btn v3-btn-sm"
                      onClick={() => openBatch(entry.batch.id)}
                      disabled={activeBatchId === entry.batch.id}
                    >
                      Open
                    </button>
                    {' '}
                    {canAssign && (
                      <button
                        className="v3-btn v3-btn-sm"
                        onClick={() => startAssign(entry.batch)}
                        disabled={assignFor?.id === entry.batch.id}
                      >
                        Assign
                      </button>
                    )}
                  </td>
                </tr>
                {assignFor?.id === entry.batch.id && (
                  <tr>
                    <td colSpan={11}>
                      <div className="workspace-field" style={{ marginBottom: 8 }}>
                        <label>Assign batch to</label>
                        <div>
                          <label className="v3-checkbox" style={{ display: 'inline-block', marginRight: 16 }}>
                            <input
                              type="radio"
                              name="assign-type"
                              checked={assignForm.type === 'operator'}
                              onChange={() => setAssignForm({ ...assignForm, type: 'operator', target: '' })}
                            />
                            Internal operator
                          </label>
                          <label className="v3-checkbox" style={{ display: 'inline-block' }}>
                            <input
                              type="radio"
                              name="assign-type"
                              checked={assignForm.type === 'entity'}
                              onChange={() => setAssignForm({ ...assignForm, type: 'entity', target: '' })}
                            />
                            Processing entity
                          </label>
                        </div>
                      </div>
                      {assignForm.type === 'operator' ? (
                        <div className="workspace-field" style={{ marginBottom: 8 }}>
                          <label>Operator</label>
                          <select
                            value={assignForm.target}
                            onChange={(e) => setAssignForm({ ...assignForm, target: e.target.value })}
                          >
                            <option value="">Select operator…</option>
                            {operators.map((p) => (
                              <option key={p.user_id || p.id} value={p.user_id || p.id}>
                                {p.first_name} {p.last_name} ({p.role_name || 'operator'})
                              </option>
                            ))}
                          </select>
                        </div>
                      ) : (
                        <div className="workspace-field" style={{ marginBottom: 8 }}>
                          <label>Processing entity</label>
                          <select
                            value={assignForm.target}
                            onChange={(e) => setAssignForm({ ...assignForm, target: e.target.value })}
                          >
                            <option value="">Select entity…</option>
                            {entities.map((entity) => (
                              <option key={entity.id} value={entity.id}>{entity.name}</option>
                            ))}
                          </select>
                        </div>
                      )}
                      <div className="workspace-field" style={{ marginBottom: 8 }}>
                        <label>Reason (optional)</label>
                        <input
                          value={assignForm.reason}
                          onChange={(e) => setAssignForm({ ...assignForm, reason: e.target.value })}
                          placeholder="e.g. entity owns this client's extraction"
                        />
                      </div>
                      <div className="workspace-actions">
                        <button className="v3-btn" onClick={() => setAssignFor(null)}>Cancel</button>
                        <button
                          className="v3-btn primary"
                          onClick={onAssign}
                          disabled={assigning || !assignForm.target}
                        >
                          {assigning ? 'Assigning…' : 'Assign batch'}
                        </button>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
        {queueTotal > queueLimit && (
          <div className="ct-table-pagination">
            <span className="ct-table-pagination-count">
              {queueTotal === 0 ? '0 rows' : `${queueOffset + 1}–${Math.min(queueTotal, queueOffset + batches.length)} of ${queueTotal}`}
            </span>
            <button
              type="button"
              className="v3-btn v3-btn-sm"
              disabled={queueOffset <= 0}
              onClick={() => loadBatches(queueLimit, Math.max(0, queueOffset - queueLimit))}
            >
              ← Prev
            </button>
            <span className="ct-table-pagination-count">
              Page {Math.floor(queueOffset / queueLimit) + 1} of {Math.max(1, Math.ceil(queueTotal / queueLimit))}
            </span>
            <button
              type="button"
              className="v3-btn v3-btn-sm"
              disabled={queueOffset + queueLimit >= queueTotal}
              onClick={() => loadBatches(queueLimit, queueOffset + queueLimit)}
            >
              Next →
            </button>
            <select
              className="ct-table-pagination-select"
              aria-label="Rows per page"
              value={queueLimit}
              onChange={(e) => loadBatches(Number(e.target.value), 0)}
            >
              {[10, 25, 50, 100].map((s) => (
                <option key={s} value={s}>{s} / page</option>
              ))}
            </select>
          </div>
        )}
        {canAssign && entities.length === 0 && (
          <div className="v3-ops-notice" style={{ marginTop: 8 }}>
            No processing entities provisioned — create one in the Entities tab before assigning work to an entity.
          </div>
        )}
      </div>

      <div className="workspace-pane">
        <h3>Batch items ({items.length})</h3>
        {items.length === 0 ? (
          <div className="v3-ops-notice">No items in this batch yet.</div>
        ) : (
          <table className="v3-ops-table">
            <thead><tr><th>Item</th><th>Status</th><th /></tr></thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id}>
                  <td>{i.file_name}</td>
                  <td>{i.status}</td>
                  <td>
                    <button className="v3-btn v3-btn-sm" onClick={() => openItem(i.id)}>
                      Open
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
