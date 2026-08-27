// frontend/src/v3/admin/ActivityTab.jsx
// D18/R2 — Organisation activity surface. Renders member activity derived from
// authoritative author columns (documents uploaded, issues created/resolved,
// extraction batches, emissions rows) via /api/v3/reporting/member-activity.
// Never fabricates activity — only real persisted rows are shown.
import React, { useCallback, useEffect, useState } from 'react';
import { getMemberActivity } from '../api';
import { LoadingState, ErrorState, Alert } from '../components/ui';
import DataTable from '../components/ui/DataTable';

export default function ActivityTab({ organization }) {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getMemberActivity(organization.id);
      setMembers(result.members || []);
    } catch (e) {
      setError(e.message || 'Failed to load activity');
    } finally {
      setLoading(false);
    }
  }, [organization.id]);

  useEffect(() => { load(); }, [load, retryCount]);

  if (loading) return <LoadingState label="Loading activity…" />;
  if (error) return <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  const columns = [
    { key: 'name', header: 'Member', accessor: 'name', render: (row) => <strong>{row.name}</strong>, isHeader: true },
    { key: 'documents_uploaded', header: 'Documents', accessor: 'documents_uploaded' },
    { key: 'issues_created', header: 'Issues created', accessor: 'issues_created' },
    { key: 'issues_resolved', header: 'Issues resolved', accessor: 'issues_resolved' },
    { key: 'extraction_batches', header: 'Batches', accessor: 'extraction_batches' },
    { key: 'emissions_rows', header: 'Emissions rows', accessor: 'emissions_rows' },
  ];

  const total = members.reduce(
    (acc, m) => ({
      docs: acc.docs + (m.documents_uploaded || 0),
      issues: acc.issues + (m.issues_created || 0),
      batches: acc.batches + (m.extraction_batches || 0),
      emissions: acc.emissions + (m.emissions_rows || 0),
    }),
    { docs: 0, issues: 0, batches: 0, emissions: 0 },
  );

  return (
    <div>
      <Alert tone="info" title="Activity">
        Activity is derived from the organisation's persisted rows (uploads, batches, issues, emissions). It is
        per-member and org-scoped.
      </Alert>

      {members.length === 0 ? (
        <p className="v3-muted" style={{ marginTop: 16 }}>
          No member activity recorded yet — activity appears as documents are uploaded and processed.
        </p>
      ) : (
        <>
          <div className="v3-stat-grid" style={{ marginTop: 12 }}>
            <div className="v3-stat-card"><div className="v3-stat-label">Documents</div><div className="v3-stat-value">{total.docs}</div></div>
            <div className="v3-stat-card"><div className="v3-stat-label">Issues</div><div className="v3-stat-value">{total.issues}</div></div>
            <div className="v3-stat-card"><div className="v3-stat-label">Batches</div><div className="v3-stat-value">{total.batches}</div></div>
            <div className="v3-stat-card"><div className="v3-stat-label">Emissions rows</div><div className="v3-stat-value">{total.emissions}</div></div>
          </div>
          <DataTable caption="Member activity" columns={columns} rows={members} rowKey="user_id" />
        </>
      )}
    </div>
  );
}
