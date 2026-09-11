// frontend/src/v3/ops/AuditConsoleTab.jsx
// Admin audit console — read-side audit trail over /api/v3/ops/reporting/audit
// (staff admin, can_manage_staff only). Filters on action / entity_type /
// actor with bounded pagination. Before/after payloads are deliberately not
// exposed by the backend; only actor/action/resource/timestamp/field names.
import React, { useCallback, useEffect, useState } from 'react';
import { getOpsAudit } from '../api';
import { LoadingState, ErrorState, Alert, Button, SelectInput, TextInput } from '../components/ui';
import DataTable from '../components/ui/DataTable';

const PAGE_SIZE = 50;

export default function AuditConsoleTab({ canManage }) {
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [filters, setFilters] = useState({
    action: '', entity_type: '', actor: '', q: '',
    // Phase 7 — taxonomy investigation filters.
    category: '', origin: '', outcome: '',
  });
  const [qDraft, setQDraft] = useState('');
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('desc');
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
    if (filters.q) params.q = filters.q;
    if (filters.category) params.category = filters.category;
    if (filters.origin) params.origin = filters.origin;
    if (filters.outcome) params.outcome = filters.outcome;
    if (sortKey) {
      params.sort = sortKey;
      params.order = sortDir;
    }
    try {
      const result = await getOpsAudit(params);
      setEntries(result.entries || []);
      setTotal(result.total || 0);
    } catch (e) {
      setError(e.message || 'Failed to load audit trail');
    } finally {
      setLoading(false);
    }
  }, [offset, filters, sortKey, sortDir]);

  useEffect(() => {
    if (!canManage) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load, retryCount, canManage]);

  // Debounce the free-text search: only hit the API once the operator pauses.
  useEffect(() => {
    const timer = setTimeout(() => {
      const q = qDraft.trim();
      if (q !== filters.q) {
        setFilters((f) => ({ ...f, q }));
        setOffset(0);
      }
    }, 350);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qDraft]);

  // The audit trail is staff-admin-only: gate BEFORE loading/fetching so a
  // non-manager never triggers a read of the trail (BL-4, authorization).
  if (!canManage) {
    return (
      <Alert tone="info" title="Audit is admin-only">
        The audit console is reserved for staff with staff-admin permissions.
      </Alert>
    );
  }

  if (loading) return <LoadingState label="Loading audit trail…" />;

  const columns = [
    {
      key: 'occurred_at',
      header: 'When',
      accessor: 'occurred_at',
      sortable: true,
      sortValue: (row) => (row.occurred_at ? new Date(row.occurred_at).getTime() : -1),
      render: (row) => (row.occurred_at ? new Date(row.occurred_at).toLocaleString() : '—'),
    },
    { key: 'actor', header: 'Actor', accessor: 'actor', sortable: true, sortValue: (row) => (row.actor || '').toLowerCase() },
    { key: 'action', header: 'Action', accessor: 'action', sortable: true, sortValue: (row) => (row.action || '').toLowerCase() },
    // Phase 7 — canonical taxonomy columns.
    { key: 'category', header: 'Category', accessor: 'category', render: (row) => row.category || '—' },
    { key: 'origin', header: 'Origin', accessor: 'origin', render: (row) => row.origin || '—' },
    { key: 'outcome', header: 'Outcome', accessor: 'outcome', render: (row) => row.outcome || '—' },
    { key: 'entity_type', header: 'Resource', accessor: 'entity_type', sortable: true, sortValue: (row) => (row.entity_type || '').toLowerCase() },
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

  const onSortChange = ({ key, direction }) => {
    setSortKey(key);
    setSortDir(direction);
    setOffset(0);
  };

  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      {error && <Alert tone="error" title="Failed to load">{error}</Alert>}

      <div className="v3-form-grid" style={{ marginBottom: 12 }}>
        <TextInput
          label="Search"
          placeholder="action, resource, actor, entity id…"
          value={qDraft}
          onChange={(e) => setQDraft(e.target.value)}
        />
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
        <SelectInput
          label="Category"
          value={filters.category}
          onChange={(e) => { setFilters({ ...filters, category: e.target.value }); setOffset(0); }}
        >
          <option value="">All categories</option>
          <option value="authentication">authentication</option>
          <option value="authorization">authorization</option>
          <option value="document">document</option>
          <option value="extraction">extraction</option>
          <option value="mapping">mapping</option>
          <option value="validation">validation</option>
          <option value="calculation">calculation</option>
          <option value="evidence">evidence</option>
          <option value="workflow">workflow</option>
          <option value="report">report</option>
          <option value="administration">administration</option>
          <option value="system">system</option>
        </SelectInput>
        <SelectInput
          label="Origin"
          value={filters.origin}
          onChange={(e) => { setFilters({ ...filters, origin: e.target.value }); setOffset(0); }}
        >
          <option value="">Human + system</option>
          <option value="human">Human</option>
          <option value="system">System / automated</option>
        </SelectInput>
        <SelectInput
          label="Outcome"
          value={filters.outcome}
          onChange={(e) => { setFilters({ ...filters, outcome: e.target.value }); setOffset(0); }}
        >
          <option value="">Any outcome</option>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
        </SelectInput>
      </div>

      <DataTable
        caption={`Audit trail — ${total} entries`}
        columns={columns}
        rows={entries}
        rowKey="id"
        onSortChange={onSortChange}
        sortKey={sortKey}
        sortDir={sortDir}
      />

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
