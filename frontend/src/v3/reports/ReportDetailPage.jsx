// frontend/src/v3/reports/ReportDetailPage.jsx
// CarbonTally V3 — Report detail: status, metadata, content preview, versions,
// download. All data is real V3 backend data (persisted rows → API).
import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  downloadExport,
  downloadReport,
  exportEmissionsUrl,
  getReport,
  getReportContent,
  getReportVersions,
  resolveV3Organization,
} from '../api';
import { ErrorState } from '../components/StateViews';
import './reports.css';

const STATUS_LABELS = { pending: 'Queued', generating: 'Generating', completed: 'Ready', failed: 'Failed' };

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function SectionView({ sectionId, title, value }) {
  const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  return (
    <details className="v3-section-card" open={sectionId === 'totals'}>
      <summary>{title}</summary>
      <div className="v3-section-body"><pre>{text}</pre></div>
    </details>
  );
}

function SectionList({ content }) {
  const titles = {
    metadata: 'Report metadata',
    organization: 'Organization',
    period: 'Reporting period',
    totals: 'Emissions totals',
    scopes: 'Scope summaries',
    activities: 'Category / activity summaries',
    validation: 'Validation',
    benchmarking: 'Benchmarking',
    provenance: 'Factor provenance',
    calculation: 'Calculation information',
    lineage: 'Source lineage',
    generation: 'Generation metadata',
  };
  return (
    <div>
      {Object.entries(content || {}).map(([key, value]) => (
        <SectionView key={key} sectionId={key} title={titles[key] || key} value={value} />
      ))}
    </div>
  );
}

export default function ReportDetailPage() {
  const { id } = useParams();
  const [organization, setOrganization] = useState(null);
  const [report, setReport] = useState(null);
  const [content, setContent] = useState(null);
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const org = await resolveV3Organization();
      setOrganization(org);
      const detail = await getReport(id);
      setReport(detail.report);
      const [contentResult, versionsResult] = await Promise.all([
        getReportContent(id).catch((e) => (e.status === 409 ? { content: null } : Promise.reject(e))),
        getReportVersions(id),
      ]);
      setContent(contentResult.content || null);
      setVersions(versionsResult.versions || []);
    } catch (e) {
      setError(e.message || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load, retryCount]);

  const onDownload = async () => {
    setBusy(true);
    try {
      await downloadReport(id, `${report.report_name || 'report'}.json`);
    } catch (e) {
      setError(e.message || 'Download failed');
    } finally {
      setBusy(false);
    }
  };

  const onExport = async (format) => {
    if (!organization) return;
    setBusy(true);
    try {
      const period = report.reporting_period || {};
      const url = format === 'csv'
        ? exportEmissionsUrl(organization.id, 'csv', { start_date: period.start_date, end_date: period.end_date })
        : exportEmissionsUrl(organization.id, 'json', { start_date: period.start_date, end_date: period.end_date });
      await downloadExport(url);
    } catch (e) {
      setError(e.message || 'Export failed');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <div className="v3-report-page"><div className="v3-loading"><div className="spinner" />Loading report…</div></div>;
  }

  if (error) {
    return (
      <div className="v3-report-page">
        <div className="v3-report-nav"><Link to="/reports">← Back to reports</Link></div>
        <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />
      </div>
    );
  }

  const status = report.status || 'pending';
  const ready = report.ready === true && status === 'completed';

  return (
    <div className="v3-report-page">
      <div className="v3-report-nav">
        <Link to="/reports">← Back to reports</Link>
      </div>
      <div className="v3-report-header">
        <div>
          <h1>{report.report_name || `${report.report_type} ${report.reporting_year}`}</h1>
          <p className="subtitle">
            <span className={`v3-status ${status}`}><span className="dot" />{STATUS_LABELS[status] || status}</span>
            {' '}· {report.report_type} · {report.reporting_year}
          </p>
        </div>
        <div className="v3-report-actions">
          {ready && (
            <>
              <button className="v3-btn" onClick={onDownload} disabled={busy}>Download (JSON)</button>
              <button className="v3-btn" onClick={() => onExport('csv')} disabled={busy || !organization}>Export emissions CSV</button>
              <button className="v3-btn" onClick={() => onExport('json')} disabled={busy || !organization}>Export emissions JSON</button>
            </>
          )}
        </div>
      </div>

      {!ready && (
        <div className="v3-card" style={{ padding: 16, marginBottom: 16, color: '#4a5568' }}>
          {status === 'failed'
            ? `This report failed to generate: ${report.error_log || 'unknown error'}`
            : 'This report has not finished generating yet. The preview and download will unlock once the backend confirms the report is ready.'}
        </div>
      )}

      <div className="v3-detail-grid">
        <div className="v3-detail-section">
          <h2>Report preview</h2>
          {ready && content ? (
            <SectionList content={content} />
          ) : (
            <div className="v3-card"><div className="v3-empty">
              {status === 'failed'
                ? 'No preview available — generation failed.'
                : 'Preview will appear once the report is ready.'}
            </div></div>
          )}
        </div>
        <div>
          <div className="v3-detail-section">
            <h2>Details</h2>
            <div className="v3-meta-list">
              <div className="v3-meta-item"><div className="k">Organization</div><div className="v">{organization ? organization.name : report.organization_id}</div></div>
              <div className="v3-meta-item"><div className="k">Report type</div><div className="v">{report.report_type}</div></div>
              <div className="v3-meta-item"><div className="k">Reporting period</div><div className="v">
                {report.reporting_period ? `${report.reporting_period.start_date} → ${report.reporting_period.end_date}` : report.reporting_year}
              </div></div>
              <div className="v3-meta-item"><div className="k">Status</div><div className="v">{STATUS_LABELS[status] || status}</div></div>
              <div className="v3-meta-item"><div className="k">Created</div><div className="v">{formatDate(report.created_at)}</div></div>
              <div className="v3-meta-item"><div className="k">Generated</div><div className="v">{formatDate(report.completed_at)}</div></div>
              <div className="v3-meta-item"><div className="k">Created by</div><div className="v">{report.created_by || '—'}</div></div>
              <div className="v3-meta-item"><div className="k">Pages</div><div className="v">{report.page_count || '—'}</div></div>
              <div className="v3-meta-item"><div className="k">File size</div><div className="v">{report.final_report_size_bytes ? `${report.final_report_size_bytes} bytes` : '—'}</div></div>
            </div>
          </div>

          <div className="v3-detail-section">
            <h2>Versions</h2>
            {versions.length === 0 ? (
              <div className="v3-card"><div className="v3-empty" style={{ padding: 24 }}>No versions recorded yet.</div></div>
            ) : (
              <div className="v3-card">
                <ul className="v3-versions-list">
                  {versions.map((v) => (
                    <li key={v.id}>
                      <span>Version {v.version_number}</span>
                      <span className="v3-muted">{formatDate(v.created_at)}</span>
                      {v.is_current && <span className="v3-tag">Current</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="v3-detail-section">
            <h2>Export</h2>
            <div className="v3-muted" style={{ marginBottom: 8 }}>
              Org-scoped exports from the V3 exports surface (CSV / JSON). Excel is not a supported backend format.
            </div>
            <button className="v3-btn v3-btn-sm" onClick={() => onExport('csv')} disabled={busy || !organization}>Emissions CSV</button>{' '}
            <button className="v3-btn v3-btn-sm" onClick={() => onExport('json')} disabled={busy || !organization}>Emissions JSON</button>
          </div>
        </div>
      </div>
    </div>
  );
}


