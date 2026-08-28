// frontend/src/v3/ops/ReviewQueue.jsx
// Reviewer queue: review queue + shared workspace with validation and
// review (assign/complete) actions.
import React, { useEffect, useState } from 'react';
import { assignReview, completeReview, getOpsReviewReporting, getReviewQueue, validateItem } from '../api';
import WorkItemWorkspace from './WorkItemWorkspace';

export default function ReviewQueue() {
  const [items, setItems] = useState([]);
  const [activeItemId, setActiveItemId] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [report, setReport] = useState(null);

  const load = async () => {
    try {
      const result = await getReviewQueue();
      setItems(result.items || []);
    } catch (e) {
      setError(e.message || 'Failed to load review queue');
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  // D30 — reviewer reporting (aging, SLA).
  useEffect(() => {
    getOpsReviewReporting()
      .then(setReport)
      .catch(() => setReport(null));
  }, []);

  const onValidate = async () => {
    try {
      const result = await validateItem(activeItemId);
      setNotice(result.blocking ? 'Blocking findings — routed back to mapping.' : 'Validated.');
    } catch (e) { setError(e.message); }
  };

  const onAssign = async () => {
    try {
      await assignReview(activeItemId, ''); // assigned_to resolved server-side for internal reviewers
      setNotice('Review assigned.');
      await load();
    } catch (e) { setError(e.message); }
  };

  const onComplete = async () => {
    try {
      await completeReview(activeItemId, { manual_extraction_result: { reviewed: true }, review_time_seconds: 60 });
      setNotice('Review completed.');
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
          <h3>Review reporting</h3>
          <div className="v3-ops-strip">
            <span className="v3-ops-card"><span className="label">Pending</span><span className="value">{report.by_status?.pending ?? 0}</span></span>
            <span className="v3-ops-card"><span className="label">In review</span><span className="value">{report.by_status?.in_review ?? 0}</span></span>
            <span className="v3-ops-card"><span className="label">Completed</span><span className="value">{report.by_status?.completed ?? 0}</span></span>
            <span className="v3-ops-card"><span className="label">SLA breached</span><span className="value">{report.sla_breached ?? 0}</span></span>
          </div>
          <p className="v3-muted" style={{ marginTop: 8 }}>
            Aging: {Object.entries(report.aging || {}).map(([b, n]) => `${b}: ${n}`).join(' · ') || 'none'}
          </p>
          {report.workload?.length > 0 && (
            <>
              <h4 style={{ marginTop: 10 }}>Reviewer workload</h4>
              <table className="v3-ops-table" style={{ marginTop: 6 }}>
                <thead><tr><th>Reviewer</th><th>Assigned</th><th>Pending</th><th>Completed</th><th>Overdue</th></tr></thead>
                <tbody>
                  {report.workload.map((w) => (
                    <tr key={w.reviewer_id}><td>{w.name}</td><td>{w.assigned}</td><td>{w.pending}</td><td>{w.completed}</td><td>{w.overdue}</td></tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
          <h4 style={{ marginTop: 10 }}>Issues</h4>
          <p className="v3-muted">
            Types: {Object.entries(report.issues?.by_type || {}).map(([t, n]) => `${t}: ${n}`).join(' · ') || 'none'}
            {' · '}Status: {Object.entries(report.issues?.by_status || {}).map(([s, n]) => `${s}: ${n}`).join(' · ') || 'none'}
          </p>
        </div>
      )}

      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Review queue ({items.length})</h3>
        <table className="v3-ops-table">
          <thead><tr><th>Item</th><th>Status</th><th>Assigned</th><th>Priority</th><th>Open</th></tr></thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td>{r.file_name}</td>
                <td>{r.status}</td>
                {/* UH-7 — reviewer display name instead of a raw UUID */}
                <td>{r.assigned_to_name || '—'}</td>
                <td>{r.priority}</td>
                <td>
                  {/* UH-7 — open the REAL extraction item the row resolves to */}
                  <button className="v3-btn primary" onClick={() => setActiveItemId(r.item_id || r.id)}>Open workspace</button>
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
            <div className="workspace-actions">
              <button className="v3-btn primary" onClick={onValidate} disabled={item.status !== 'mapped' && item.status !== 'validated'}>
                Validate
              </button>
              <button className="v3-btn" onClick={onAssign}>Assign to me</button>
              <button className="v3-btn primary" onClick={onComplete}>Complete review</button>
            </div>
          )}
        />
      )}
    </div>
  );
}
