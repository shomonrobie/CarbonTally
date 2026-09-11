// frontend/src/v3/reports/ReportsPage.jsx
// CarbonTally V3 — Reports dashboard. Real V3 backend data only: no fake
// statistics, no fabricated reports/statuses.
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ErrorState } from '../components/StateViews';
import DataTable from '../components/ui/DataTable';
import {
  downloadExport,
  downloadReport,
  exportDocumentsUrl,
  exportEmissionsUrl,
  generateReport,
  getReportTypes,
  listReports,
  resolveV3Organization,
} from '../api';
import './reports.css';

const STATUS_LABELS = { pending: 'Queued', generating: 'Generating', completed: 'Ready', failed: 'Failed' };

const CURRENT_YEAR = new Date().getFullYear();

function StatusBadge({ status }) {
  return (
    <span className={`v3-status ${status || 'pending'}`}>
      <span className="dot" />
      {STATUS_LABELS[status] || status}
    </span>
  );
}

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function GenerateReportModal({ organization, types, onClose, onGenerated }) {
  const [reportType, setReportType] = useState('annual');
  const [year, setYear] = useState(CURRENT_YEAR);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    setSubmitting(true);
    setError('');
    try {
      const result = await generateReport({
        organization_id: organization.id,
        report_type: reportType,
        reporting_year: year,
      });
      onGenerated(result);
    } catch (e) {
      setError(e.message || 'Report generation failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="v3-modal-backdrop" onClick={onClose}>
      <div className="v3-modal" onClick={(e) => e.stopPropagation()}>
        <h2>Generate report</h2>
        {error && <div className="v3-error" style={{ padding: 12, marginBottom: 12 }}>{error}</div>}
        <div className="v3-form-group">
          <label htmlFor="v3-report-type">Report type</label>
          <select id="v3-report-type" value={reportType} onChange={(e) => setReportType(e.target.value)}>
            {types.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>
        <div className="v3-form-group">
          <label htmlFor="v3-report-year">Reporting period (year)</label>
          <select id="v3-report-year" value={year} onChange={(e) => setYear(Number(e.target.value))}>
            {[CURRENT_YEAR, CURRENT_YEAR - 1, CURRENT_YEAR - 2, CURRENT_YEAR - 3].map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <p className="v3-form-hint">
            Generates the annual emissions report for the selected year from the
            authoritative V3 calculation data.
          </p>
        </div>
        <div className="v3-modal-actions">
          <button className="v3-btn" onClick={onClose} disabled={submitting}>Cancel</button>
          <button className="v3-btn v3-btn-primary" onClick={submit} disabled={submitting}>
            {submitting ? 'Generating…' : 'Generate report'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  const [organization, setOrganization] = useState(null);
  const [reports, setReports] = useState([]);
  const [counts, setCounts] = useState({});
  const [types, setTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showGenerate, setShowGenerate] = useState(false);
  const [notice, setNotice] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  const [filters, setFilters] = useState({ status: '', report_type: '', reporting_year: '' });

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const org = await resolveV3Organization();
      if (!org) {
        setError('No organization is linked to this account. Ask an administrator to add you to an organization.');
        setLoading(false);
        return;
      }
      setOrganization(org);
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.report_type) params.report_type = filters.report_type;
      if (filters.reporting_year) params.reporting_year = filters.reporting_year;
      const [list, typeList] = await Promise.all([
        listReports(org.id, { ...params, limit: 500 }),
        getReportTypes().catch(() => ({ report_types: [{ id: 'annual', name: 'Annual emissions report' }] })),
      ]);
      setReports(list.reports || []);
      setCounts(list.count_by_status || {});
      setTypes(typeList.report_types || []);
    } catch (e) {
      setError(e.message || 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  }, [filters.status, filters.report_type, filters.reporting_year]);

  useEffect(() => { load(); }, [load, retryCount]);

  const onGenerated = async (result) => {
    setShowGenerate(false);
    setNotice(`Report ready: ${result?.report?.report_name || 'annual report'}.`);
    await load();
    setTimeout(() => setNotice(''), 6000);
  };

  const onDownload = async (report) => {
    try {
      await downloadReport(report.id, `${report.report_name || 'report'}.json`);
    } catch (e) {
      setError(e.message || 'Download failed');
    }
  };

  const onExport = async (format) => {
    try {
      const url = format === 'csv'
        ? exportEmissionsUrl(organization.id, 'csv')
        : exportEmissionsUrl(organization.id, 'json');
      await downloadExport(url);
    } catch (e) {
      setError(e.message || 'Export failed');
    }
  };

  const onExportDocuments = async () => {
    try {
      await downloadExport(exportDocumentsUrl(organization.id));
    } catch (e) {
      setError(e.message || 'Document export failed');
    }
  };

  const summary = useMemo(() => [
    { key: 'completed', label: 'Ready', value: counts.completed || 0 },
    { key: 'pending', label: 'Queued', value: counts.pending || 0 },
    { key: 'generating', label: 'Generating', value: counts.generating || 0 },
    { key: 'failed', label: 'Failed', value: counts.failed || 0 },
  ], [counts]);

  const reportColumns = [
    {
      key: 'report_name',
      header: 'Report',
      accessor: 'report_name',
      sortable: true,
      sortValue: (r) => (r.report_name || `${r.report_type} ${r.reporting_year}`).toLowerCase(),
      render: (r) => (
        <>
          <Link className="v3-report-name" to={`/reports/${r.id}`}>
            {r.report_name || `${r.report_type} ${r.reporting_year}`}
          </Link>
          {r.error_log && <div className="v3-muted" title={r.error_log}>Failed: {r.error_log.slice(0, 80)}</div>}
        </>
      ),
      isHeader: true,
    },
    {
      key: 'report_type',
      header: 'Type',
      accessor: 'report_type',
      sortable: true,
      sortValue: (r) => (r.report_type || '').toLowerCase(),
      render: (r) => <span className="v3-muted">{r.report_type}</span>,
    },
    {
      key: 'reporting_year',
      header: 'Period',
      accessor: 'reporting_year',
      sortable: true,
      sortValue: (r) => (r.reporting_year != null ? r.reporting_year : -1),
      render: (r) => r.reporting_year,
    },
    {
      key: 'status',
      header: 'Status',
      accessor: 'status',
      sortable: true,
      sortValue: (r) => (r.status || '').toLowerCase(),
      render: (r) => <StatusBadge status={r.status} />,
    },
    {
      key: 'created_at',
      header: 'Created',
      accessor: 'created_at',
      sortable: true,
      sortValue: (r) => (r.created_at ? new Date(r.created_at).getTime() : -1),
      render: (r) => formatDate(r.created_at),
    },
    {
      key: 'completed_at',
      header: 'Generated',
      accessor: 'completed_at',
      sortable: true,
      sortValue: (r) => (r.completed_at ? new Date(r.completed_at).getTime() : -1),
      render: (r) => formatDate(r.completed_at),
    },
    {
      key: 'version',
      header: 'Version',
      accessor: 'current_version',
      sortable: true,
      sortValue: (r) => r.current_version?.version_number || 0,
      render: (r) => r.current_version?.version_number || (r.status === 'completed' ? 'v1' : '—'),
    },
    {
      key: 'created_by',
      header: 'Created by',
      accessor: 'created_by',
      sortable: true,
      sortValue: (r) => (r.created_by || '').toLowerCase(),
      render: (r) => <span className="v3-muted">{r.created_by ? r.created_by.slice(0, 8) : '—'}</span>,
    },
    {
      key: 'actions',
      header: '',
      accessor: 'id',
      render: (r) => (
        <>
          <Link className="v3-btn v3-btn-sm" to={`/reports/${r.id}`}>View</Link>{' '}
          {r.status === 'completed' && r.ready && (
            <button className="v3-btn v3-btn-sm" onClick={() => onDownload(r)}>Download</button>
          )}
        </>
      ),
    },
  ];

  return (
    <div className="v3-report-page">
      <div className="v3-report-header">
        <div>
          <h1>Reports</h1>
          <p className="subtitle">
            {organization ? `${organization.name} · ` : ''}V3 reporting workflow (authoritative data)
          </p>
        </div>
        <div className="v3-report-actions">
          <button className="v3-btn" onClick={() => onExport('csv')} disabled={!organization}>
            Export emissions CSV
          </button>
          <button className="v3-btn" onClick={() => onExport('json')} disabled={!organization}>
            Export emissions JSON
          </button>
          <button className="v3-btn" onClick={onExportDocuments} disabled={!organization}>
            Export documents CSV
          </button>
          <button className="v3-btn v3-btn-primary" onClick={() => setShowGenerate(true)} disabled={!organization}>
            + Generate report
          </button>
        </div>
      </div>

      {notice && <div className="v3-card" style={{ padding: 12, marginBottom: 16, color: '#22543d', background: '#f0fff4' }}>{notice}</div>}
      {error && <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />}

      <div className="v3-summary-strip">
        {summary.map((s) => (
          <div className="v3-summary-card" key={s.key}>
            <div className="label">{s.label}</div>
            <div className={`value ${s.key}`}>{s.value}</div>
          </div>
        ))}
      </div>


      <div className="v3-filters">
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
        >
          <option value="">All statuses</option>
          <option value="pending">Queued</option>
          <option value="generating">Generating</option>
          <option value="completed">Ready</option>
          <option value="failed">Failed</option>
        </select>
        <select
          value={filters.report_type}
          onChange={(e) => setFilters({ ...filters, report_type: e.target.value })}
        >
          <option value="">All types</option>
          {types.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <select
          value={filters.reporting_year}
          onChange={(e) => setFilters({ ...filters, reporting_year: e.target.value })}
        >
          <option value="">All years</option>
          {[CURRENT_YEAR, CURRENT_YEAR - 1, CURRENT_YEAR - 2, CURRENT_YEAR - 3].map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="v3-loading"><div className="spinner" />Loading reports…</div>
      ) : reports.length === 0 ? (
        <div className="v3-card"><div className="v3-empty">
          No reports found. Use “Generate report” to create one from the authoritative V3 data.
        </div></div>
      ) : (
        <div className="v3-card">
          <DataTable
            caption="Organisation reports"
            columns={reportColumns}
            rows={reports}
            clientPaginate
            defaultPageSize={10}
            resetKey={JSON.stringify(filters)}
            emptyLabel="No reports match the current filters."
          />
        </div>
      )}

      {showGenerate && (
        <GenerateReportModal
          organization={organization}
          types={types}
          onClose={() => setShowGenerate(false)}
          onGenerated={onGenerated}
        />
      )}
    </div>
  );
}

