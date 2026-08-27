// frontend/src/v3/ops/OpsDashboard.jsx
// CarbonTally operations dashboard: workload, processing status, pending
// review/QC and issues — all from the authoritative /api/v3/ops/dashboard.
import React, { useEffect, useState } from 'react';
import { getOpsAudit, getOpsDashboard, getOpsPlatformReporting, getOpsQueueAging } from '../api';

function Stat({ label, value }) {
  return (
    <div className="v3-ops-card">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}

export default function OpsDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [platform, setPlatform] = useState(null);
  const [aging, setAging] = useState(null);
  const [audit, setAudit] = useState(null);

  useEffect(() => {
    getOpsDashboard()
      .then(setData)
      .catch((e) => setError(e.message || 'Failed to load dashboard'));
    // D30 — platform & quality reporting (internal staff, can_view_all).
    getOpsPlatformReporting()
      .then(setPlatform)
      .catch(() => setPlatform(null));
    // D31 — queue aging drill-down (internal staff, can_view_all).
    getOpsQueueAging()
      .then(setAging)
      .catch(() => setAging(null));
    // D31 — read-side audit (staff admin only; hidden for others via 403).
    getOpsAudit({ limit: 25 })
      .then(setAudit)
      .catch(() => setAudit(null));
  }, []);

  if (error) return <div className="v3-ops-error">{error}</div>;
  if (!data) return <div className="v3-loading"><div className="spinner" />Loading dashboard…</div>;

  const pipeline = data.pipeline || {};
  const items = pipeline.items || {};
  const batches = pipeline.batches || {};
  const queues = pipeline.queues || {};
  const staff = data.staff || {};
  const issues = data.issues || {};

  return (
    <div>
      <div className="v3-ops-strip">
        <Stat label="Batches" value={batches.total ?? 0} />
        <Stat label="Items" value={items.total ?? 0} />
        <Stat label="% Complete" value={`${items.pct_complete ?? 0}%`} />
        <Stat label="Pending QC" value={queues.qc_pending ?? 0} />
        <Stat label="Customer review" value={queues.customer_review ?? 0} />
        <Stat label="Issues" value={issues.total ?? 0} />
        <Stat label="Staff" value={staff.total ?? 0} />
      </div>

      <div className="workspace-pane">
        <h3>Pipeline by stage</h3>
        <table className="v3-ops-table">
          <thead>
            <tr><th>Stage</th><th>Items</th></tr>
          </thead>
          <tbody>
            {Object.entries(items.by_stage || {}).map(([stage, count]) => (
              <tr key={stage}><td>{stage}</td><td>{count}</td></tr>
            ))}
          </tbody>
        </table>
      </div>

      {platform && (
        <div className="workspace-pane">
          <h3>Platform &amp; quality</h3>
          <div className="v3-ops-strip">
            <Stat label="Organizations" value={platform.platform?.organizations ?? 0} />
            <Stat label="Entities" value={(platform.platform?.processing_entities?.active ?? 0)} />
            <Stat label="Staff" value={Object.values(platform.platform?.staff || {}).reduce((a, b) => a + b, 0)} />
            <Stat label="Items complete" value={`${platform.processing?.items_complete_pct ?? 0}%`} />
            <Stat label="Failed/rejected" value={platform.processing?.failed_or_rejected ?? 0} />
            <Stat label="Review SLA breached" value={platform.quality?.review_sla_breached ?? 0} />
            <Stat label="Open issues" value={platform.quality?.issues_by_status?.open ?? 0} />
          </div>
        </div>
      )}

      {aging && (
        <div className="workspace-pane">
          <h3>Queue aging</h3>
          <div className="v3-ops-strip">
            <Stat label="Batches open" value={aging.batches?.open ?? 0} />
            <Stat label="Batches completed" value={aging.batches?.completed ?? 0} />
            <Stat label="SLA breached" value={aging.batches?.sla_breached ?? 0} />
            <Stat label="Overdue" value={aging.batches?.overdue ?? 0} />
            <Stat label="Items" value={aging.items?.total ?? 0} />
            <Stat label="Internal items" value={aging.items?.internal ?? 0} />
            <Stat label="Entity items" value={aging.items?.entity ?? 0} />
          </div>
          <div style={{ display: 'flex', gap: 24, marginTop: 8, flexWrap: 'wrap' }}>
            <div>
              <h4>Batch age</h4>
              {Object.entries(aging.batches?.aging || {}).map(([b, n]) => (
                <p key={b} className="v3-muted">{b}: {n}</p>
              ))}
            </div>
            <div>
              <h4>Item age</h4>
              {Object.entries(aging.items?.aging || {}).map(([b, n]) => (
                <p key={b} className="v3-muted">{b}: {n}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      {audit && (
        <div className="workspace-pane">
          <h3>Audit trail (admin)</h3>
          {audit.entries?.length === 0 ? (
            <p className="v3-muted">No audit entries recorded yet.</p>
          ) : (
            <table className="v3-ops-table">
              <thead>
                <tr><th>When</th><th>Actor</th><th>Action</th><th>Resource</th><th>Entity</th></tr>
              </thead>
              <tbody>
                {audit.entries.map((e) => (
                  <tr key={e.id}>
                    <td>{e.occurred_at ? e.occurred_at.slice(0, 19).replace('T', ' ') : ''}</td>
                    <td>{e.actor}</td>
                    <td>{e.action}</td>
                    <td>{e.entity_type}</td>
                    <td>{e.entity_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
