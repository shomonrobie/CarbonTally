// frontend/src/v3/ops/PEManagerDashboard.jsx
// Phase F close-out (F1) — a genuinely distinct PE Manager experience.
// Managers see entity-wide oversight: assigned work, team workload, SLA/quality
// and the assigned-batch list, all own-entity and server-enforced. Staff get
// the item-level extraction workspace (separate surface) — this is not a
// rename of the staff screen.
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getEntityDashboard,
  getEntityExtractionBatches,
  getEntityPerformance,
} from '../api';
import './ops.css';

export default function PEManagerDashboard({ entityId }) {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [batches, setBatches] = useState([]);
  const [performance, setPerformance] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getEntityDashboard(entityId)
      .then(setDashboard)
      .catch((e) => setError(e.message || 'Failed to load entity dashboard'));
    getEntityExtractionBatches(entityId)
      .then((body) => setBatches(body.batches || []))
      .catch((e) => setError(e.message || 'Failed to load batches'));
    getEntityPerformance(entityId)
      .then(setPerformance)
      .catch(() => setPerformance(null));
  }, [entityId]);

  const summary = (dashboard?.extraction || {});
  const batchStats = { open: 0, in_progress: 0, completed: 0, other: 0 };
  batches.forEach((b) => {
    const s = b.status || 'other';
    if (batchStats[s] !== undefined) batchStats[s] += 1;
    else batchStats.other += 1;
  });

  const statusLabel = (s) => s || 'pending';

  return (
    <div className="v3-entity-extraction">
      <div className="v3-ops-header">
        <div>
          <h1>Processing Entity — Manager dashboard</h1>
          <div className="subtitle">
            Entity-wide oversight · batches: {summary?.batches?.total ?? 0} · items:{' '}
            {summary?.items?.total ?? 0} · {((summary?.items?.pct_complete) ?? 0).toFixed(1)}% complete
          </div>
        </div>
        <button className="v3-btn v3-btn-sm" onClick={() => navigate('/ops?tab=entity-work')}>
          Open item work →
        </button>
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
        </div>
      )}

      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Team workload</h3>
        {performance?.staff?.length > 0 ? (
          <table className="v3-ops-table">
            <thead><tr><th>Team member</th><th>Assigned</th><th>Completed</th></tr></thead>
            <tbody>
              {performance.staff.map((s) => (
                <tr key={s.id}><td>{s.name}</td><td>{s.assigned}</td><td>{s.completed}</td></tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="muted">No team workload data for this entity yet.</p>
        )}
      </div>

      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Assigned batches ({batches.length})</h3>
        <div className="v3-ops-strip">
          <span className="v3-ops-card"><span className="label">Open</span><span className="value">{batchStats.open}</span></span>
          <span className="v3-ops-card"><span className="label">In progress</span><span className="value">{batchStats.in_progress}</span></span>
          <span className="v3-ops-card"><span className="label">Completed</span><span className="value">{batchStats.completed}</span></span>
          <span className="v3-ops-card"><span className="label">Other</span><span className="value">{batchStats.other}</span></span>
        </div>
        {batches.length === 0 ? (
          <p className="muted" style={{ marginTop: 8 }}>No work assigned to this Processing Entity.</p>
        ) : (
          <table className="v3-ops-table" style={{ marginTop: 8 }}>
            <thead><tr><th>Batch</th><th>Status</th><th /></tr></thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.id}>
                  <td>{b.batch_name || b.id}</td>
                  <td>{statusLabel(b.status)}</td>
                  <td><button className="v3-btn v3-btn-sm" onClick={() => navigate('/ops?tab=entity-work')}>Open items</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
