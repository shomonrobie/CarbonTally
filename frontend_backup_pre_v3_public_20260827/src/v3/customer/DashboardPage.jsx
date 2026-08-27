// frontend/src/v3/customer/DashboardPage.jsx
// CarbonTally V3 customer dashboard — real org-scoped data from the V3 backend.
// Statistics are composed from verified V3 surfaces (reports, documents,
// members, persisted emissions rows); nothing is fabricated.
import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  getCustomerDashboardReport,
  getEmissionsTrend,
  getMemberActivity,
  listMembers,
  listReports,
  resolveV3Organization,
  v3ListDocuments,
  v3ListEmissions,
} from '../api';
import { ErrorState } from '../components/StateViews';

function StatCard({ label, value, to }) {
  return (
    <Link to={to} className="v3-stat-card">
      <div className="v3-stat-label">{label}</div>
      <div className="v3-stat-value">{value}</div>
    </Link>
  );
}

export default function DashboardPage() {
  const [org, setOrg] = useState(null);
  const [reports, setReports] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [members, setMembers] = useState([]);
  const [emissions, setEmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  const [report, setReport] = useState(null);
  const [reportError, setReportError] = useState('');
  const [trend, setTrend] = useState(null);
  const [activity, setActivity] = useState(null);
  const [activityError, setActivityError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const organization = await resolveV3Organization();
      if (!organization) {
        setError('No organization is linked to this account.');
        setLoading(false);
        return;
      }
      setOrg(organization);
      const [rep, docs, mems, emis] = await Promise.all([
        listReports(organization.id).catch(() => ({ reports: [] })),
        v3ListDocuments(organization.id).catch(() => ({ documents: [] })),
        listMembers(organization.id).catch(() => ({ members: [] })),
        v3ListEmissions(organization.id).catch(() => ({ emissions: [] })),
      ]);
      setReports(rep.reports || []);
      setDocuments(docs.documents || []);
      setMembers(mems.members || []);
      setEmissions(emis.emissions || []);
    } catch (e) {
      setError(e.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load, retryCount]);

  // D30 — reporting overview (emissions / documents / processing / attention).
  useEffect(() => {
    if (!org) return;
    let active = true;
    getCustomerDashboardReport(org.id)
      .then((r) => { if (active) { setReport(r); setReportError(''); } })
      .catch((e) => { if (active) setReportError(e.message || 'Reporting unavailable'); });
    // D31 — monthly emissions trend + member activity.
    getEmissionsTrend(org.id, 12)
      .then((r) => { if (active) setTrend(r); })
      .catch(() => undefined);
    getMemberActivity(org.id)
      .then((r) => { if (active) { setActivity(r); setActivityError(''); } })
      .catch((e) => { if (active) setActivityError(e.message || 'Activity unavailable'); });
    return () => { active = false; };
  }, [org]);

  const readyReports = reports.filter((r) => r.status === 'completed').length;
  const pendingReports = reports.filter((r) => r.status === 'pending' || r.status === 'generating').length;
  const totalCo2e = emissions.reduce((sum, row) => sum + (Number(row.calculated_kg_co2e) || Number(row.co2e_kg) || 0), 0);

  if (loading) return <div className="v3-loading"><div className="spinner" />Loading dashboard…</div>;
  if (error) return <ErrorState message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  return (
    <div className="v3-page">
      <div className="v3-page-header">
        <h1>Dashboard</h1>
        <p className="v3-subtitle">{org.name} · V3 customer workspace</p>
      </div>

      <div className="v3-stat-grid">
        <StatCard label="Ready reports" value={readyReports} to="/reports" />
        <StatCard label="Queued reports" value={pendingReports} to="/reports" />
        <StatCard label="Documents" value={documents.length} to="/documents" />
        <StatCard label="Members" value={members.length} to="/organization" />
        <StatCard label="Emissions rows" value={emissions.length} to="/emissions" />
        <StatCard label="Total tCO₂e" value={(totalCo2e / 1000).toFixed(2)} to="/emissions" />
      </div>

      {reportError ? (
        <div className="v3-card"><div className="v3-muted">{reportError}</div></div>
      ) : report ? (
        <div className="v3-card" style={{ marginBottom: 16 }}>
          <h2>Reporting overview</h2>
          <div className="v3-grid-2">
            <div>
              <h3 className="v3-muted">Emissions</h3>
              <p><strong>{(report.emissions.total_kg / 1000).toFixed(2)} tCO₂e</strong> ({report.emissions.row_count} rows)</p>
              {report.emissions.by_scope.map((s) => (
                <p key={s.scope} className="v3-muted">{s.scope}: {(s.kg / 1000).toFixed(2)} tCO₂e</p>
              ))}
              {report.emissions.by_month.length > 0 && (
                <p className="v3-muted">Latest month: {report.emissions.by_month[report.emissions.by_month.length - 1].month}</p>
              )}
            </div>
            <div>
              <h3 className="v3-muted">Documents</h3>
              <p>Total <strong>{report.documents.total_documents}</strong> · Processed {report.documents.processed} · Pending {report.documents.pending}</p>
              <p className={report.documents.requiring_attention ? 'v3-error' : 'v3-muted'}>
                Requiring attention: {report.documents.requiring_attention}
              </p>
            </div>
            <div>
              <h3 className="v3-muted">Processing</h3>
              <p>{report.processing.items.total} items · <strong>{report.processing.items.complete_pct}%</strong> complete</p>
              <p className="v3-muted">Mapped {report.processing.items.mapped} · Unmapped {report.processing.items.unmapped}</p>
              <p className="v3-muted">
                {Object.entries(report.processing.items.by_stage)
                  .filter(([, n]) => n > 0)
                  .map(([stage, n]) => `${stage}: ${n}`).join(' · ') || 'No items'}
              </p>
            </div>
            <div>
              <h3 className="v3-muted">Needs your attention</h3>
              <p>Open issues: <strong>{report.attention.open_issues}</strong></p>
              <p className="v3-muted">Unmapped items: {report.attention.unmapped_items}</p>
              <p className="v3-muted">Pending customer review: {report.attention.pending_customer_review}</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="v3-loading"><div className="spinner" />Loading reporting…</div>
      )}

      <div className="v3-card" style={{ marginBottom: 16 }}>
        <h2>Monthly emissions trend</h2>
        {trend ? (
          trend.months.some((m) => m.kg > 0) ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={trend.months.map((m) => ({ month: m.month, tCO2e: Number((m.kg / 1000).toFixed(2)), rows: m.rows }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(value, _name, item) => [`${value} tCO₂e (${item.payload.rows} rows)`, 'Emissions']}
                  labelFormatter={(label) => `Period ${label}`}
                />
                <Bar dataKey="tCO2e" fill="#2f6f4f" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="v3-empty">No emissions recorded in the last 12 months yet.</p>
          )
        ) : (
          <div className="v3-loading"><div className="spinner" />Loading trend…</div>
        )}
      </div>

      <div className="v3-card" style={{ marginBottom: 16 }}>
        <h2>Activity by member</h2>
        {activityError ? (
          <div className="v3-muted">{activityError}</div>
        ) : activity ? (
          activity.members.length === 0 ? (
            <p className="v3-empty">No organisation members yet.</p>
          ) : (
            <table className="v3-table">
              <thead>
                <tr><th>Member</th><th>Documents uploaded</th><th>Extraction batches</th><th>Issues created</th><th>Issues resolved</th><th>Emissions rows</th></tr>
              </thead>
              <tbody>
                {activity.members.map((m) => (
                  <tr key={m.user_id}>
                    <td>{m.name}</td>
                    <td>{m.documents_uploaded}</td>
                    <td>{m.extraction_batches}</td>
                    <td>{m.issues_created}</td>
                    <td>{m.issues_resolved}</td>
                    <td>{m.emissions_rows}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        ) : (
          <div className="v3-loading"><div className="spinner" />Loading activity…</div>
        )}
      </div>

      <div className="v3-grid-2">
        <div className="v3-card">
          <h2>Quick actions</h2>
          <div className="v3-quick-links">
            <Link className="v3-btn" to="/emissions">Record / calculate emissions</Link>
            <Link className="v3-btn" to="/documents">Upload a document</Link>
            <Link className="v3-btn" to="/processing">View processing batches</Link>
            <Link className="v3-btn" to="/reports">Generate a report</Link>
          </div>
        </div>

        <div className="v3-card">
          <h2>Latest reports</h2>
          {reports.length === 0 ? (
            <div className="v3-empty">No reports yet.</div>
          ) : (
            <table className="v3-table">
              <thead>
                <tr><th>Report</th><th>Period</th><th>Status</th></tr>
              </thead>
              <tbody>
                {reports.slice(0, 5).map((r) => (
                  <tr key={r.id}>
                    <td>
                      <Link className="v3-link" to={`/reports/${r.id}`}>
                        {r.report_name || `${r.report_type} ${r.reporting_year}`}
                      </Link>
                    </td>
                    <td>{r.reporting_year}</td>
                    <td>{r.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
