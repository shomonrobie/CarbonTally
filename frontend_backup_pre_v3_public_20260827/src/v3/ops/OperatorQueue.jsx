// frontend/src/v3/ops/OperatorQueue.jsx
// Data-entry operator queue: operator queue + batch items + the shared D23
// extraction panel (document viewer, multi-line extraction, factor picker,
// save/resume, next/previous item).
import React, { useCallback, useEffect, useState } from 'react';
import {
  assignBatch,
  calculateItem,
  extractItem,
  getItemWorkspace,
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
  const [batches, setBatches] = useState([]);
  const [activeBatchId, setActiveBatchId] = useState(null);
  const [items, setItems] = useState([]);
  const [activeItemId, setActiveItemId] = useState(null);
  const [item, setItem] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [validation, setValidation] = useState([]);
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

  const loadBatches = useCallback(async () => {
    try {
      const result = await getOperatorQueue();
      setBatches(result.batches || []);
      if ((result.batches || []).length) {
        const first = result.batches[0].batch;
        setActiveBatchId(first.id);
      }
    } catch (e) {
      setError(e.message || 'Failed to load operator queue');
    }
  }, []);

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
      setActiveItemId(pending ? pending.id : null);
      return list;
    } catch (e) {
      setError(e.message || 'Failed to load batch items');
      return [];
    }
  }, []);

  const openBatch = async (batchId) => {
    setActiveBatchId(batchId);
    setActiveItemId(null);
    setItem(null);
    await loadBatchItems(batchId);
  };

  const openItem = async (itemId) => {
    setActiveItemId(itemId);
    setItem(null);
    setNotice('');
    try {
      // Load the full signed workspace payload: signed source URL + OCR field
      // suggestions + server validation findings (D19/D32). The list row is
      // used only for selection.
      const ws = await getItemWorkspace(itemId);
      setItem(ws.item || ws);
      setSuggestions(ws.source?.ocr_suggestions || null);
      setValidation(ws.validation?.findings || []);
    } catch (e) {
      setError(e.message || 'Failed to open item workspace');
    }
  };

  useEffect(() => {
    if (activeBatchId && !items.length) loadBatchItems(activeBatchId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeBatchId]);

  useEffect(() => {
    if (activeItemId && !item) openItem(activeItemId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeItemId]);

  const afterChange = async (itemId) => {
    try {
      const ws = await getItemWorkspace(itemId);
      setItem(ws.item || ws);
      setSuggestions(ws.source?.ocr_suggestions || null);
      setValidation(ws.validation?.findings || []);
      // Also refresh the list row so the queue reflects the new status.
      await loadBatchItems(activeBatchId);
    } catch (e) {
      setError(e.message || 'Failed to refresh item');
    }
  };

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
        <h3>Assigned / self-serve batches ({batches.length})</h3>
        <table className="v3-ops-table">
          <thead><tr><th>Batch</th><th>Status</th><th>Progress</th><th /></tr></thead>
          <tbody>
            {batches.map((entry) => (
              <React.Fragment key={entry.batch.id}>
                <tr>
                  <td>{entry.batch.batch_name || entry.batch.id}</td>
                  <td>{entry.batch.status}</td>
                  <td>{entry.progress ? `${entry.progress.pct_complete}%` : '—'}</td>
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
                    <td colSpan={4}>
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
                      {activeItemId === i.id ? 'Open' : 'Open'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {item ? (
        <ExtractionPanel
          item={item}
          items={items}
          api={INTERNAL_API}
          onItemChange={afterChange}
          mode="staff"
          suggestions={suggestions}
          validation={validation}
        />
      ) : (
        <div className="v3-ops-card"><div className="v3-ops-notice">Select an item to begin extraction.</div></div>
      )}
    </div>
  );
}
