// frontend/src/v3/ops/QcQueue.jsx
// QC queue: QC queue + shared workspace with validation/calculation visibility
// and the pass/fail decision + notes (the CarbonTally-staff QC gate).
import React, { useEffect, useState } from 'react';
import { getOpsQcReporting, getQcQueue, qcReviewItem } from '../api';
import WorkItemWorkspace from './WorkItemWorkspace';

export default function QcQueue() {
  const [items, setItems] = useState([]);
  const [activeItemId, setActiveItemId] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [score, setScore] = useState(80);
  const [notes, setNotes] = useState('');
  const [report, setReport] = useState(null);

  const load = async () => {
    try {
      const result = await getQcQueue();
      setItems(result.items || []);
    } catch (e) {
      setError(e.message || 'Failed to load QC queue');
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  // D30 — QC reporting (outcomes, quality, internal vs entity).
  useEffect(() => {
    getOpsQcReporting()
      .then(setReport)
      .catch(() => setReport(null));
  }, []);

  const onQc = async (approved) => {
    try {
      await qcReviewItem(activeItemId, { quality_score: Number(score), approved, qc_notes: notes });
      setNotice(approved ? 'QC passed.' : 'QC rejected — item returned for correction.');
      setActiveItemId(null);
      await load();
    } catch (e) { setError(e.message); }
  };

  return (
    <div>
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      {report && (
        <div className="workspace-pane" style={{ marginBottom: 16 }}>
          <h3>QC reporting</h3>
          <div className="v3-ops-strip">
            <span className="v3-ops-card"><span className="label">QC approved</span><span className="value">{report.outcomes?.qc_approved ?? 0}</span></span>
            <span className="v3-ops-card"><span className="label">QC rejected</span><span className="value">{report.outcomes?.qc_rejected ?? 0}</span></span>
            <span className="v3-ops-card"><span className="label">Approved</span><span className="value">{report.outcomes?.approved ?? 0}</span></span>
            <span className="v3-ops-card"><span className="label">Avg quality</span><span className="value">{report.avg_quality_score ?? 0}</span></span>
          </div>
          <p className="v3-muted" style={{ marginTop: 8 }}>
            Outcomes by scope: {report.by_scope?.map((s) => `${s.scope} ${s.status}: ${s.n}`).join(' · ') || 'none'}
          </p>
          {report.processor_performance?.length > 0 && (
            <>
              <h4 style={{ marginTop: 10 }}>Processor performance (internal vs entity)</h4>
              <table className="v3-ops-table" style={{ marginTop: 6 }}>
                <thead><tr><th>Processor</th><th>Completed</th><th>Rejected</th><th>Rejection rate</th><th>Avg quality</th><th>Sample</th></tr></thead>
                <tbody>
                  {report.processor_performance.map((p) => (
                    <tr key={p.scope}>
                      <td>{p.scope === 'internal' ? 'CarbonTally internal' : 'Processing Entity'}</td>
                      <td>{p.completed}</td>
                      <td>{p.rejected}</td>
                      <td>{p.rejection_rate_pct}%</td>
                      <td>{p.avg_quality}</td>
                      <td>{p.sample_size}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
          {report.recurring_quality && !report.recurring_quality.supported && (
            <p className="v3-muted" style={{ marginTop: 8 }}>{report.recurring_quality.note}</p>
          )}
        </div>
      )}

      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>QC queue ({items.length})</h3>
        <table className="v3-ops-table">
          <thead><tr><th>Item</th><th>Status</th><th>Quality score</th><th>Open</th></tr></thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td>{r.file_name}</td>
                <td>{r.status}</td>
                <td>{r.quality_score ?? '—'}</td>
                <td>
                  <button className="v3-btn primary" onClick={() => setActiveItemId(r.id)}>Open workspace</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {activeItemId && (
        <WorkItemWorkspace
          itemId={activeItemId}
          renderActions={({ item }) => (
            <div>
              <div className="workspace-grid">
                <div className="workspace-field">
                  <label>Quality score (0–100)</label>
                  <input type="number" min={0} max={100} value={score} onChange={(e) => setScore(e.target.value)} />
                </div>
                <div className="workspace-field">
                  <label>QC notes</label>
                  <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
                </div>
              </div>
              <div className="workspace-actions">
                <button className="v3-btn primary" onClick={() => onQc(true)}>Pass</button>
                <button className="v3-btn danger" onClick={() => onQc(false)}>Fail — return for correction</button>
              </div>
            </div>
          )}
        />
      )}
    </div>
  );
}
