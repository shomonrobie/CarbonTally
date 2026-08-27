// frontend/src/v3/customer/IssuesPage.jsx
// D25 — Customer Issues. Reads the org-scoped /api/v3/issues surface only.
// The backend NEVER returns entity-scoped (internal) issues to customers, so
// no internal/processing-entity context can appear here. Customer replies on
// issues are not yet supported by the model — documented as future work.
import React, { useCallback, useEffect, useState } from 'react';
import {
  createCustomerIssue,
  getCustomerIssue,
  listCustomerIssues,
  resolveV3Organization,
} from '../api';
import { ErrorState } from '../components/StateViews';

const SEVERITY_LABELS = { low: 'Low', medium: 'Medium', high: 'High', critical: 'Critical' };
const STATUS_LABELS = { open: 'Open', in_progress: 'In progress', resolved: 'Resolved', closed: 'Closed' };
const EMPTY_FORM = { title: '', description: '', severity: 'medium' };

export default function IssuesPage() {
  const [org, setOrg] = useState(null);
  const [issues, setIssues] = useState([]);
  const [selected, setSelected] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async (organizationId) => {
    try {
      const result = await listCustomerIssues(organizationId, statusFilter ? { status: statusFilter } : {});
      setIssues(result.issues || []);
    } catch (e) {
      setError(e.message || 'Failed to load issues');
    }
  }, [statusFilter]);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const organization = await resolveV3Organization();
        if (!organization) {
          setError('No organization is linked to this account.');
          return;
        }
        setOrg(organization);
        await load(organization.id);
      } catch (e) {
        setError(e.message || 'Failed to load issues');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [load, retryCount]);

  const openIssue = async (issueId) => {
    setSelected(null);
    try {
      const result = await getCustomerIssue(issueId);
      setSelected(result);
    } catch (e) {
      setError(e.message || 'Failed to load issue');
    }
  };

  const onCreate = async () => {
    if (!org || !form.title.trim()) return;
    setSubmitting(true);
    setError('');
    setNotice('');
    try {
      await createCustomerIssue({
        organization_id: org.id,
        title: form.title.trim(),
        description: form.description.trim() || null,
        severity: form.severity,
        issue_type: 'exception',
      });
      setForm({ ...EMPTY_FORM });
      setNotice('Issue reported.');
      await load(org.id);
    } catch (e) {
      setError(e.message || 'Failed to report issue');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="v3-loading"><div className="spinner" />Loading issues…</div>;
  if (error && !org) return <ErrorState message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  return (
    <div className="v3-page">
      <div className="v3-page-header">
        <h1>Issues</h1>
        <p className="v3-subtitle">Customer-facing issues for {org?.name || 'your organisation'}</p>
      </div>

      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note">{notice}</div>}

      <div className="v3-card">
        <h2>Report an issue</h2>
        <div className="v3-form-grid">
          <div className="v3-form-group" style={{ gridColumn: '1 / -1' }}>
            <label htmlFor="d25-issue-title">Title</label>
            <input
              id="d25-issue-title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Short summary of the issue"
            />
          </div>
          <div className="v3-form-group" style={{ gridColumn: '1 / -1' }}>
            <label htmlFor="d25-issue-desc">Description (optional)</label>
            <textarea
              id="d25-issue-desc"
              rows={3}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="More detail — keep sensitive personal data out"
            />
          </div>
          <div className="v3-form-group">
            <label htmlFor="d25-issue-sev">Severity</label>
            <select
              id="d25-issue-sev"
              value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value })}
            >
              {Object.entries(SEVERITY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="v3-actions">
          <button
            className="v3-btn v3-btn-primary"
            onClick={onCreate}
            disabled={submitting || !form.title.trim()}
          >
            {submitting ? 'Reporting…' : 'Report issue'}
          </button>
        </div>
      </div>

      <div className="v3-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <h2 style={{ margin: 0 }}>Issues ({issues.length})</h2>
          <select
            aria-label="Filter by status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ width: 180 }}
          >
            <option value="">All statuses</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
        {issues.length === 0 ? (
          <div className="v3-empty">No issues match.</div>
        ) : (
          <table className="v3-table">
            <thead>
              <tr><th>Title</th><th>Status</th><th>Severity</th><th>Created</th><th /></tr>
            </thead>
            <tbody>
              {issues.map((issue) => (
                <tr key={issue.id}>
                  <td>{issue.title}</td>
                  <td><span className={`v3-status ${issue.status || 'open'}`}><span className="dot" />{STATUS_LABELS[issue.status] || issue.status}</span></td>
                  <td>{SEVERITY_LABELS[issue.severity] || issue.severity}</td>
                  <td className="v3-muted">{issue.created_at ? new Date(issue.created_at).toLocaleString() : '—'}</td>
                  <td>
                    <button className="v3-btn v3-btn-sm" onClick={() => openIssue(issue.id)}>View</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selected && (
        <div className="v3-card">
          <h2>{selected.title}</h2>
          <div className="v3-meta-list">
            <div className="v3-meta-item"><div className="k">Status</div><div className="v">{STATUS_LABELS[selected.status] || selected.status}</div></div>
            <div className="v3-meta-item"><div className="k">Severity</div><div className="v">{SEVERITY_LABELS[selected.severity] || selected.severity}</div></div>
            <div className="v3-meta-item"><div className="k">Created</div><div className="v">{selected.created_at ? new Date(selected.created_at).toLocaleString() : '—'}</div></div>
            <div className="v3-meta-item"><div className="k">Updated</div><div className="v">{selected.updated_at ? new Date(selected.updated_at).toLocaleString() : '—'}</div></div>
            {selected.manual_extraction_batch_id && (
              <div className="v3-meta-item"><div className="k">Related batch</div><div className="v">{selected.manual_extraction_batch_id}</div></div>
            )}
          </div>
          {selected.description && (
            <p style={{ whiteSpace: 'pre-wrap' }}>{selected.description}</p>
          )}
          <div className="v3-actions">
            <button className="v3-btn" onClick={() => setSelected(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}

