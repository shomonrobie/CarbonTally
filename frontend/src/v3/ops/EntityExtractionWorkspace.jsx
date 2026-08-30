// frontend/src/v3/ops/EntityExtractionWorkspace.jsx
// D22+D23 — Processing Entity extraction workspace. Entity staff land here from
// the ops hub; they see ONLY the work assigned to their Processing Entity (the
// server enforces it — this page never navigates a customer org surface).
// D23: uses the shared ExtractionPanel (document viewer, multi-line extraction,
// factor picker, save/resume, next/previous item).
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getEntityDashboard,
  getEntityExtractionBatchItems,
  getEntityExtractionBatches,
  getEntityPerformance,
} from '../api';
import './ops.css';

export default function EntityExtractionWorkspace({ entityId }) {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [batches, setBatches] = useState([]);
  const [selectedBatchId, setSelectedBatchId] = useState('');
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');
  const [performance, setPerformance] = useState(null);

  const loadBatches = useCallback(() => {
    setError('');
    getEntityExtractionBatches(entityId)
      .then((body) => setBatches(body.batches || []))
      .catch((e) => setError(e.message || 'Failed to load batches'));
  }, [entityId]);

  useEffect(() => {
    setError('');
    getEntityDashboard(entityId)
      .then((body) => setDashboard(body))
      .catch(() => setDashboard(null));
    loadBatches();
  }, [entityId, loadBatches]);

  // D30 — entity performance (own entity only; internal staff any).
  useEffect(() => {
    getEntityPerformance(entityId)
      .then(setPerformance)
      .catch(() => setPerformance(null));
  }, [entityId]);

  const selectBatch = (batchId) => {
    setSelectedBatchId(batchId);
    setItems([]);
    getEntityExtractionBatchItems(entityId, batchId)
      .then((body) => setItems(body.items || []))
      .catch((e) => setError(e.message || 'Failed to load items'));
  };

  const selectItem = (itemId) => {
    // Phase G (G5) — the item workspace is a dedicated route, never an inline
    // panel under the entity batch list. Back-to-entity is a real route with
    // browser-history behaviour.
    navigate(`/pe/items/${encodeURIComponent(entityId)}/${encodeURIComponent(itemId)}`);
  };

  const summary = (dashboard?.extraction || {});
  const statusLabel = (s) => s || 'pending';

  return (
    <div className="v3-entity-extraction">
      <div className="v3-ops-header">
        <div>
          <h1>Extraction workspace</h1>
          <div className="subtitle">
            Assigned work only — batches: {summary?.batches?.total ?? 0} · items:{' '}
            {summary?.items?.total ?? 0} · {((summary?.items?.pct_complete) ?? 0).toFixed(1)}% complete
          </div>
        </div>
      </div>
      {error && <div className="v3-ops-error">{error}</div>}

      {performance && (
        <div className="workspace-pane" style={{ marginBottom: 16 }}>
          <h3>Entity performance</h3>
          <div className="v3-ops-strip">
            <span className="v3-ops-card"><span className="label">Batches</span><span className="value">{performance.batches?.total ?? 0}</span></span>
            <span className="v3-ops-card"><span className="label">Items</span><span className="value">{performance.items?.total ?? 0}</span></span>
            <span className="v3-ops-card"><span className="label">Complete</span><span className="value">{performance.items?.complete_pct ?? 0}%</span></span>
            <span className="v3-ops-card"><span className="label">SLA breached</span><span className="value">{performance.batches?.sla_breached ?? 0}</span></span>
            <span className="v3-ops-card"><span className="label">Overdue</span><span className="value">{performance.batches?.overdue ?? 0}</span></span>
            <span className="v3-ops-card"><span className="label">Avg quality</span><span className="value">{performance.quality?.avg_quality ?? 0}</span></span>
            <span className="v3-ops-card"><span className="label">Rejections</span><span className="value">{performance.quality?.rejected ?? 0}</span></span>
          </div>
          {performance.staff?.length > 0 && (
            <table className="v3-ops-table" style={{ marginTop: 8 }}>
              <thead><tr><th>Staff</th><th>Assigned</th><th>Completed</th></tr></thead>
              <tbody>
                {performance.staff.map((s) => (
                  <tr key={s.id}><td>{s.name}</td><td>{s.assigned}</td><td>{s.completed}</td></tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <div className="entity-grid">
        <div className="entity-pane">
          <h3>Assigned batches</h3>
          {batches.length === 0 && <p className="muted">No work assigned to this Processing Entity.</p>}
          {batches.map((batch) => (
            <button
              key={batch.id}
              className={`entity-row${selectedBatchId === batch.id ? ' active' : ''}`}
              onClick={() => selectBatch(batch.id)}
            >
              <strong>{batch.batch_name}</strong>
              <span className="muted">{statusLabel(batch.status)}</span>
            </button>
          ))}
        </div>

        {selectedBatchId && (
          <div className="entity-pane">
            <h3>Items</h3>
            {items.length === 0 && <p className="muted">No items in this batch.</p>}
            {items.map((it) => (
              <button
                key={it.id}
                className="entity-row"
                onClick={() => selectItem(it.id)}
              >
                <strong>{it.file_name}</strong>
                <span className="muted">{statusLabel(it.status)}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
