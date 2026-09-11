// frontend/src/v3/admin/AuditTab.jsx
// Phase 7 — Auditor / Assurance: customer audit & evidence surface.
//
// Shows the organisation its OWN audit-readiness indicator, recent material
// activity and a downloadable audit/evidence package. CarbonTally provides
// traceable evidence and audit-ready records; it does NOT provide an assurance
// opinion. The readiness indicator is explicitly labelled "audit evidence
// readiness" and the UI never claims verification/assurance/certification.
//
// Authorization is server-side (organisation owner/admin only); this tab is a
// UX convenience and is never the security boundary.
import React, { useCallback, useEffect, useState } from 'react';
import {
  auditPackageUrl,
  downloadExport,
  getAuditActivity,
  getAuditReadiness,
} from '../api';
import { Alert, Button, ErrorState, LoadingState, SelectInput } from '../components/ui';
import DataTable from '../components/ui/DataTable';
import './admin.css';

const STATUS_LABEL = {
  no_evidence_yet: 'No evidence recorded yet',
  gaps_to_review: 'Some evidence gaps to review',
  evidence_present: 'Evidence present for the current records',
};

export default function AuditTab({ organization }) {
  const [readiness, setReadiness] = useState(null);
  const [activity, setActivity] = useState(null);
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState('');

  const load = useCallback(async () => {
    if (!organization?.id) return;
    setLoading(true);
    setError('');
    try {
      const [r, a] = await Promise.all([
        getAuditReadiness(organization.id),
        getAuditActivity(organization.id, { category, limit: 100 }),
      ]);
      setReadiness(r);
      setActivity(a);
    } catch (e) {
      setError(e.message || 'Failed to load audit information');
    } finally {
      setLoading(false);
    }
  }, [organization, category]);

  useEffect(() => { load(); }, [load]);

  const onDownload = async () => {
    setDownloading(true);
    setDownloadError('');
    try {
      await downloadExport(auditPackageUrl(organization.id));
    } catch (e) {
      setDownloadError(e.message || 'Failed to download the evidence package');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) return <LoadingState label="Loading audit information…" />;
  if (error) return <ErrorState inline message={error} onRetry={load} />;

  const components = readiness?.components || {};
  const columns = [
    {
      key: 'occurred_at',
      header: 'When',
      accessor: 'occurred_at',
      render: (row) => (row.occurred_at ? new Date(row.occurred_at).toLocaleString() : '—'),
    },
    { key: 'action', header: 'Action', accessor: 'action' },
    { key: 'category', header: 'Category', accessor: 'category', render: (row) => row.category || '—' },
    { key: 'actor', header: 'Actor', accessor: 'actor', render: (row) => (row.actor ? row.actor.slice(0, 12) : '—') },
    { key: 'origin', header: 'Origin', accessor: 'origin', render: (row) => row.origin || '—' },
  ];

  return (
    <div>
      <Alert tone="info" title="Evidence & audit readiness">
        CarbonTally provides traceable calculations, evidence, provenance and
        audit-ready records that can support internal review and independent
        assurance processes. This is not an assurance opinion, verification or
        certification.
      </Alert>

      {downloadError && <Alert tone="error" title="Download failed">{downloadError}</Alert>}

      <div className="v3-admin-card">
        <h3>Audit evidence readiness</h3>
        <p className="v3-muted">
          {STATUS_LABEL[readiness?.status] || '—'}
          {typeof readiness?.evidence_coverage_pct === 'number'
            ? ` · ${readiness.evidence_coverage_pct}% of calculations have a complete evidence chain`
            : ''}
        </p>
        <div className="v3-actions">
          <Button variant="secondary" onClick={onDownload} disabled={downloading}>
            {downloading ? 'Preparing…' : 'Download evidence package (JSON)'}
          </Button>
        </div>
        {Array.isArray(readiness?.gaps) && readiness.gaps.length > 0 && (
          <ul className="v3-muted">
            {readiness.gaps.map((g) => <li key={g}>{g}</li>)}
          </ul>
        )}
        <p className="v3-muted">
          Calculations: {components.calculations_total ?? 0} ·
          {' '}Evidence complete: {components.evidence_complete ?? 0} ·
          {' '}Documents: {components.documents ?? 0} ·
          {' '}Open issues: {components.open_issues ?? 0}
        </p>
      </div>

      <div className="v3-admin-card">
        <div className="v3-form-grid" style={{ marginBottom: 12 }}>
          <SelectInput label="Category" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            <option value="document">document</option>
            <option value="calculation">calculation</option>
            <option value="workflow">workflow</option>
            <option value="report">report</option>
            <option value="administration">administration</option>
          </SelectInput>
        </div>
        <DataTable
          caption={`Recent activity — ${activity?.total ?? 0} events`}
          columns={columns}
          rows={activity?.events || []}
          rowKey="resource_id"
        />
      </div>
    </div>
  );
}
