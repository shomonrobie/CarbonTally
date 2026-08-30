// frontend/src/v3/ops/QcQueue.jsx
// QC queue: QC queue + shared workspace with validation/calculation visibility
// and the pass/fail decision + notes (the CarbonTally-staff QC gate).
// CL-59 — opening an item navigates to the dedicated routed workspace
// (/ops/qc/:itemId).
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getOpsQcReporting, getQcQueue } from '../api';

export default function QcQueue() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState(25);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [report, setReport] = useState(null);

  const load = async (nextLimit = limit, nextOffset = offset) => {
    try {
      const result = await getQcQueue(nextLimit, nextOffset);
      setItems(result.items || []);
      setTotal(result.total ?? result.queued ?? 0);
      setLimit(nextLimit);
      setOffset(nextOffset);
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
        <h3>QC queue ({total})</h3>
        <table className="v3-ops-table">
          <thead><tr><th>Item</th><th>Organisation</th><th>Client of</th><th>Entity</th><th>Batch</th><th>Status</th><th>Quality score</th><th>Received</th><th>Open</th></tr></thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td>{r.file_name}</td>
                <td>{r.organization_name || '—'}</td>
                <td>{r.consultant ? r.consultant.firm_name || r.consultant.client_name || '—' : '—'}</td>
                <td>{r.entity?.name || '—'}</td>
                <td>{r.batch_name || '—'}</td>
                <td>{r.status}</td>
                <td>{r.quality_score ?? '—'}</td>
                <td>{r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}</td>
                <td>
                  {/* CL-59 — open the item in a dedicated routed workspace */}
                  <button className="v3-btn primary" onClick={() => navigate(`/ops/qc/${encodeURIComponent(r.id)}`)}>Open workspace</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {total > limit && (
          <div className="ct-table-pagination">
            <span className="ct-table-pagination-count">
              {offset + 1}–{Math.min(total, offset + items.length)} of {total}
            </span>
            <button type="button" className="v3-btn v3-btn-sm" disabled={offset <= 0} onClick={() => load(limit, Math.max(0, offset - limit))}>← Prev</button>
            <span className="ct-table-pagination-count">Page {Math.floor(offset / limit) + 1} of {Math.max(1, Math.ceil(total / limit))}</span>
            <button type="button" className="v3-btn v3-btn-sm" disabled={offset + limit >= total} onClick={() => load(limit, offset + limit)}>Next →</button>
            <select className="ct-table-pagination-select" aria-label="Rows per page" value={limit} onChange={(e) => load(Number(e.target.value), 0)}>
              {[10, 25, 50, 100].map((s) => <option key={s} value={s}>{s} / page</option>)}
            </select>
          </div>
        )}
      </div>
    </div>
  );
}
