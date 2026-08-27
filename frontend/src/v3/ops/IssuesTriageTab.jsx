// frontend/src/v3/ops/IssuesTriageTab.jsx
// G-P0-4 / ADR-V3-009 — CarbonTally-internal issues triage queue. Real data
// over /api/v3/issues/admin/open (staff admin, can_manage_staff). Actions:
// assign, prioritise, escalate, resolve, close, reopen — all via the issue
// update endpoint with the domain transition table enforced server-side.
import React, { useCallback, useEffect, useState } from 'react';
import { listOpsOpenIssues, updateIssue } from '../api';
import { LoadingState, Alert, Button, StatusBadge, ConfirmationDialog } from '../components/ui';
import DataTable from '../components/ui/DataTable';

const STATUS_TRANSITIONS = {
  open: ['in_progress', 'on_hold', 'escalated', 'resolved', 'closed'],
  in_progress: ['on_hold', 'escalated', 'resolved', 'closed'],
  on_hold: ['in_progress', 'escalated', 'resolved', 'closed'],
  escalated: ['in_progress', 'resolved', 'closed'],
  resolved: ['closed', 'open'],
  closed: ['open'],
};

const PRIORITIES = [0, 1, 2, 3, 4, 5];

export default function IssuesTriageTab({ canManage }) {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busyId, setBusyId] = useState(null);
  const [confirm, setConfirm] = useState(null); // {action, issue, payload}
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await listOpsOpenIssues();
      setIssues(result.issues || []);
    } catch (e) {
      setError(e.message || 'Failed to load issues');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load, retryCount]);

  const flash = (message) => {
    setNotice(message);
    setTimeout(() => setNotice(''), 5000);
  };

  const runUpdate = async (issue, payload, message) => {
    setBusyId(issue.id);
    setError('');
    try {
      await updateIssue(issue.id, payload);
      flash(message);
      setConfirm(null);
      await load();
    } catch (e) {
      setError(e.message || 'Failed to update issue');
    } finally {
      setBusyId(null);
    }
  };

  if (loading) return <LoadingState label="Loading issues…" />;

  if (!canManage) {
    return (
      <Alert tone="info" title="Triage is admin-managed">
        The operations issues triage queue is reserved for staff with staff-admin permissions.
      </Alert>
    );
  }

  const columns = [
    { key: 'title', header: 'Issue', accessor: 'title', render: (row) => <strong>{row.title}</strong>, isHeader: true },
    { key: 'status', header: 'Status', accessor: 'status', render: (row) => <StatusBadge status={row.status} /> },
    { key: 'severity', header: 'Severity', accessor: 'severity' },
    { key: 'priority', header: 'Priority', accessor: 'priority' },
    {
      key: 'org',
      header: 'Context',
      accessor: 'organization_id',
      render: (row) => (row.entity_id ? `entity:${row.entity_id.slice(0, 8)}` : row.organization_id ? `org:${row.organization_id.slice(0, 8)}` : '—'),
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (row) => (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <select
            aria-label={`Transition status for ${row.title}`}
            className="v3-input"
            value=""
            style={{ width: 120 }}
            onChange={(e) => {
              const status = e.target.value;
              if (status) setConfirm({ action: 'status', issue: row, payload: { status } });
            }}
          >
            <option value="">Status…</option>
            {(STATUS_TRANSITIONS[row.status] || []).map((s) => (
              <option key={s} value={s}>{s.replace('_', ' ')}</option>
            ))}
          </select>
          <select
            aria-label={`Set priority for ${row.title}`}
            className="v3-input"
            value={String(row.priority ?? 0)}
            style={{ width: 90 }}
            onChange={(e) => runUpdate(row, { priority: Number(e.target.value) }, 'Priority updated.')}
          >
            {PRIORITIES.map((p) => <option key={p} value={p}>P{p}</option>)}
          </select>
          {row.status === 'resolved' || row.status === 'closed' ? (
            <Button variant="secondary" size="sm" icon="refresh" loading={busyId === row.id} onClick={() => runUpdate(row, { status: 'open' }, 'Issue reopened.')}>
              Reopen
            </Button>
          ) : (
            <Button variant="secondary" size="sm" icon="check" loading={busyId === row.id} onClick={() => setConfirm({ action: 'resolve', issue: row, payload: { status: 'resolved' } })}>
              Resolve
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      {notice && <Alert tone="success" title="Updated">{notice}</Alert>}
      {error && <Alert tone="error" title="Action failed">{error}</Alert>}

      <Alert tone="info" title="Issues triage">
        Open, in-progress and escalated issues across the platform. Transition authority is enforced server-side
        against the domain transition table; every change is audited.
      </Alert>

      {issues.length === 0 ? (
        <p className="v3-muted" style={{ marginTop: 16 }}>No open issues to triage.</p>
      ) : (
        <div style={{ marginTop: 16 }}>
          <DataTable caption="Operations issues triage" columns={columns} rows={issues} rowKey="id" />
        </div>
      )}

      {confirm && (
        <ConfirmationDialog
          open
          title={confirm.action === 'resolve' ? 'Resolve this issue?' : `Move to "${confirm.payload.status}"?`}
          message={
            confirm.action === 'resolve'
              ? 'Resolving records the issue as resolved. It can be reopened later.'
              : `The issue will transition from ${confirm.issue.status} to ${confirm.payload.status}.`
          }
          confirmLabel={confirm.action === 'resolve' ? 'Resolve' : 'Update'}
          tone={confirm.action === 'resolve' ? 'approve' : 'primary'}
          busy={busyId === confirm.issue.id}
          onClose={() => setConfirm(null)}
          onConfirm={() => runUpdate(confirm.issue, confirm.payload, 'Issue updated.')}
        />
      )}
    </div>
  );
}
