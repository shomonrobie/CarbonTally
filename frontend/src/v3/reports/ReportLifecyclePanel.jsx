// frontend/src/v3/reports/ReportLifecyclePanel.jsx
//
// S6 (visibility-first) — customer-facing report lifecycle panel.
//
// Scope discipline:
//   * states, transitions and permissions are NOT defined here; they are read
//     from the persisted version rows and their server-provided
//     `allowed_actions` (see backend/api/v3_reports.py list_report_versions);
//   * no review-comment capability is implemented (deliberately out of S6);
//   * the UI never derives an "almost complete" state — what the database says
//     is what the customer sees.
import React, { useState } from 'react';
import { REPORT_LIFECYCLE_ACTION_CALLS } from '../api';

// Human labels for the existing lifecycle vocabulary
// (backend/domain/report_lifecycle.py: DRAFT, REVIEWED, CHANGES_REQUESTED,
//  REJECTED, APPROVED, FINAL). Unknown values fall through verbatim rather than
// being guessed.
const STATUS_LABELS = {
  DRAFT: 'Draft',
  REVIEWED: 'In review',
  CHANGES_REQUESTED: 'Changes requested',
  REJECTED: 'Rejected',
  APPROVED: 'Approved',
  FINAL: 'Final',
};

// Plain-English meaning of each persisted state, so the customer understands
// what is happening and what comes next.
const STATUS_HELP = {
  DRAFT: 'This version is still being prepared and has not been sent for review.',
  REVIEWED: 'This version is with your reviewer. It is not yet approved.',
  CHANGES_REQUESTED: 'Changes were requested. A revised version is needed.',
  REJECTED: 'This version was rejected and will not be approved as it stands.',
  APPROVED: 'Approved. It can now be finalised.',
  FINAL: 'Final and locked. Finalised reports are immutable.',
};

const ACTION_LABELS = {
  submit_review: 'Submit for review',
  approve: 'Approve',
  request_changes: 'Request changes',
  reject: 'Reject',
  finalize: 'Finalize',
};

// Immutable states are locked by the backend (IMMUTABLE_STATUSES).
const IMMUTABLE_STATUSES = ['APPROVED', 'FINAL'];

export const lifecycleStatusLabel = (status) =>
  STATUS_LABELS[status] || status || 'Unknown';

const formatTimestamp = (iso) => {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? String(iso) : d.toLocaleString();
};

export default function ReportLifecyclePanel({ reportId, versions = [], onChanged }) {
  const [busyAction, setBusyAction] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const current =
    versions.find((v) => v.is_current) || versions[versions.length - 1] || null;
  // The server sends this list with each version row; when it is absent we
  // offer nothing rather than inventing the rules in the browser.
  const allowedActions =
    current && Array.isArray(current.allowed_actions) ? current.allowed_actions : [];
  // Only transitions that this release performs are rendered, so a legitimate
  // server action is never shown as a dead button. `new_version` (supersede by
  // a revised draft version) is outside this S6 release's approved action list
  // and is surfaced as guidance instead.
  const performableActions = allowedActions.filter(
    (action) => REPORT_LIFECYCLE_ACTION_CALLS[action]
  );
  const needsNewVersion = allowedActions.includes('new_version');

  const runAction = async (action) => {
    const call = REPORT_LIFECYCLE_ACTION_CALLS[action];
    if (!call || !current) return;
    setBusyAction(action);
    setError('');
    setNotice('');
    try {
      await call(reportId, current.version_number);
      setNotice(
        `Version ${current.version_number}: ${ACTION_LABELS[action] || action} recorded.`
      );
      if (onChanged) await onChanged();
    } catch (err) {
      // 403 = not permitted for this user; 409 = the state moved underneath us.
      // Both are expected outcomes of a guarded lifecycle, not crashes.
      const status = err && err.status;
      if (status === 403) {
        setError('You do not have permission to perform this action on this report.');
      } else if (status === 409) {
        setError('The report state changed while you were working on it. The current state has been reloaded.');
        if (onChanged) await onChanged();
      } else {
        setError(
          (err && err.message) || 'The action could not be completed. Please try again.'
        );
      }
    } finally {
      setBusyAction('');
    }
  };

  if (!current) {
    return (
      <div className="v3-card">
        <h2>Report status</h2>
        <div className="v3-empty" style={{ padding: 24 }}>
          No report versions yet. Lifecycle states appear once a version exists.
        </div>
      </div>
    );
  }

  const status = current.status;
  const immutable = IMMUTABLE_STATUSES.includes(status);

  return (
    <div className="v3-card">
      <div className="v3-lifecycle-head">
        <h2>Report status</h2>
        <span
          className={`v3-lifecycle-state ${String(status).toLowerCase()}`}
          aria-label={`Report state: ${lifecycleStatusLabel(status)}`}
        >
          {lifecycleStatusLabel(status)}
        </span>
      </div>

      <p className="v3-lifecycle-help" data-testid="lifecycle-help">
        Version {current.version_number} (current). {STATUS_HELP[status] || ''}
      </p>

      {immutable ? (
        <p className="v3-lifecycle-locked" data-testid="lifecycle-locked">
          This version is locked. Finalised and approved reports cannot be edited.
        </p>
      ) : null}

      {performableActions.length > 0 ? (
        <div className="v3-lifecycle-actions">
          {performableActions.map((action) => (
            <button
              key={action}
              type="button"
              className={`v3-btn ${
                action === 'finalize' || action === 'approve' ? 'primary' : ''
              }`}
              disabled={Boolean(busyAction)}
              onClick={() => runAction(action)}
            >
              {busyAction === action
                ? 'Working…'
                : ACTION_LABELS[action] || action.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      ) : (
        <p className="v3-lifecycle-noactions" data-testid="lifecycle-noactions">
          {needsNewVersion
            ? 'Further changes require a revised version of this report. Creating a version is not available from this screen yet.'
            : 'No action is available to you on this version.'}
        </p>
      )}

      {error ? (
        <div className="v3-alert error" role="alert" data-testid="lifecycle-error">
          {error}
        </div>
      ) : null}
      {notice ? (
        <div className="v3-alert success" role="status" data-testid="lifecycle-notice">
          {notice}
        </div>
      ) : null}

      <h3 className="v3-lifecycle-subhead">Version history</h3>
      <table className="v3-lifecycle-table">
        <thead>
          <tr>
            <th scope="col">Version</th>
            <th scope="col">State</th>
            <th scope="col">Recorded</th>
            <th scope="col">Current</th>
          </tr>
        </thead>
        <tbody>
          {versions.map((v) => (
            <tr key={v.id || v.version_number}>
              <td>Version {v.version_number}</td>
              <td>
                <span
                  className={`v3-lifecycle-state small ${String(v.status).toLowerCase()}`}
                >
                  {lifecycleStatusLabel(v.status)}
                </span>
              </td>
              <td>{formatTimestamp(v.created_at)}</td>
              <td>{v.is_current ? 'Current' : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
