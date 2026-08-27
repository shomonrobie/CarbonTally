// frontend/src/v3/ops/AuditConsoleTab.jsx
// Admin audit console — read-side audit trail over /api/v3/ops/reporting/audit
// (staff admin, can_manage_staff only). Filters on action / entity_type /
// actor with bounded pagination. Before/after payloads are deliberately not
// exposed by the backend; only actor/action/resource/timestamp/field names.
import React, { useCallback, useEffect, useState } from 'react';
import { getOpsAudit } from '../api';
import { LoadingState, ErrorState, Alert, Button, SelectInput } from '../components/ui';
import DataTable from '../components/ui/DataTable';

const PAGE_SIZE = 50;

export default function AuditConsoleTab({ canManage }) {
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [filters, setFilters] = useState({ action: '', entity_type: '', actor: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    const params = { limit: PAGE_SIZE, offset };
    if (filters.action) params.action = filters.action;
    if (filters.entity_type) params.entity_type = filters.entity_type;
    if (filters.actor) params.actor = filters.actor;
    try {
      const result = await getOpsAudit(params);
      setEntries(result.entries || []);
      setTotal(result.total || 0);
    } catch (e) {
      setError(e.message || 'Failed to load audit trail');
    } finally {
      setLoading(false);
    }
  }, [offset, filters]);

  useEffect(() => { load(); }, [load, retryCount]);

  if (loading) return <LoadingState label="Loading audit trail…" />;

  if (!canManage) {
    return (
      <Alert tone="info" title="Audit is admin-only">
        The audit console is reserved for staff with staff-admin permissions.
      </Alert>
    );
  }

  const columns = [
    {
      key: 'occurred_at',
      header: 'When',
      accessor: 'occurred_at',
      render: (row) => (row.occurred_at ? new Date(row.occurred_at).toLocaleString() : '—'),
    },
    { key: 'actor', header: 'Actor', accessor: 'actor' },
    { key: 'action', header: 'Action', accessor: 'action' },
    { key: 'entity_type', header: 'Resource', accessor: 'entity_type' },
    {
      key: 'entity_id',
      header: 'Entity',
      accessor: 'entity_id',
      render: (row) => <span className="v3-mono">{row.entity_id || '—'}</span>,
    },
    {
      key: 'changed',
      header: 'Changed fields',
      accessor: 'changed_fields',
      render: (row) => (row.changed_fields || []).join(', ') || '—',
    },
  ];

  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      {error && <Alert tone="error" title="Failed to load">{error}</Alert>}

      <div className="v3-form-grid" style={{ marginBottom: 12 }}>
        <SelectInput
          label="Action"
          value={filters.action}
          onChange={(e) => { setFilters({ ...filters, action: e.target.value }); setOffset(0); }}
        >
          <option value="">All actions</option>
          <option value="issue:created">issue:created</option>
          <option value="issue:updated">issue:updated</option>
          <option value="batch:assigned">batch:assigned</option>
          <option value="item:started">item:started</option>
          <option value="item:calculated">item:calculated</option>
          <option value="item:customer_reviewed">item:customer_reviewed</option>
          <option value="subscription">subscription</option>
          <option value="credit">credit</option>
        </SelectInput>
        <SelectInput
          label="Resource type"
          value={filters.entity_type}
          onChange={(e) => { setFilters({ ...filters, entity_type: e.target.value }); setOffset(0); }}
        >
          <option value="">All resources</option>
          <option value="issue">issue</option>
          <option value="manual_extraction_item">manual_extraction_item</option>
          <option value="manual_extraction_batch">manual_extraction_batch</option>
          <option value="organization">organization</option>
          <option value="processing_entity">processing_entity</option>
          <option value="subscription">subscription</option>
        </SelectInput>
        <SelectInput
          label="Actor"
          value={filters.actor}
          onChange={(e) => { setFilters({ ...filters, actor: e.target.value }); setOffset(0); }}
        >
          <option value="">All actors</option>
          {[...new Set(entries.map((e) => e.actor).filter(Boolean))].map((a) => (
            <option key={a} value={a}>{a.slice(0, 12)}…</option>
          ))}
        </SelectInput>
      </div>

      <DataTable caption={`Audit trail — ${total} entries`} columns={columns} rows={entries} rowKey="id" />

      <div className="v3-actions" style={{ alignItems: 'center' }}>
        <Button variant="secondary" icon="arrowLeft" disabled={offset === 0} onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}>
          Previous
        </Button>
        <span className="v3-muted">Page {page} of {pages}</span>
        <Button variant="secondary" icon="arrowRight" disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset((o) => o + PAGE_SIZE)}>
          Next
        </Button>
      </div>
    </div>
  );
}
