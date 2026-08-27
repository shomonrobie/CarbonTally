// frontend/src/v3/ops/WorkItemWorkspace.jsx
// Shared split-screen processing workspace — the SAME workspace contract as the
// Phase 3 surface (`source` + `data` + `status` + `issues` + `workflow`).
// Rendered inside the D19 WorkbenchShell (top workflow nav + split panes +
// pane presets + secure view-only source). Role-specific controls are layered
// on top via the `renderActions` render prop:
//   Data Entry -> extraction + mapping
//   Reviewer   -> extraction + mapping + validation + review
//   QC         -> extraction + mapping + factor + calculation + validation + QC
import React, { useEffect, useState } from 'react';
import { getItemWorkspace } from '../api';
import WorkbenchShell from '../components/workbench/WorkbenchShell';
import StatusBadge from '../components/ui/StatusBadge';

const WB_STAGES = [
  { id: 'queue', label: 'Queue' },
  { id: 'extract', label: 'Extract' },
  { id: 'map', label: 'Map' },
  { id: 'validate', label: 'Validate' },
  { id: 'review', label: 'Review' },
  { id: 'qc', label: 'QC' },
  { id: 'evidence', label: 'Evidence' },
];

function stageForStatus(status) {
  if (['qc_approved', 'qc_rejected'].includes(status)) return 'qc';
  if (['approved', 'rejected'].includes(status)) return 'review';
  if (['calculated'].includes(status)) return 'evidence';
  if (['validating', 'validated'].includes(status)) return 'validate';
  if (['mapping', 'mapped'].includes(status)) return 'map';
  return 'extract';
}

export default function WorkItemWorkspace({ itemId, renderActions, allowDownload = false }) {
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [preset, setPreset] = useState('50-50');

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    getItemWorkspace(itemId)
      .then((body) => { if (active) setWorkspace(body); })
      .catch((e) => { if (active) setError(e.message || 'Failed to load workspace'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [itemId]);

  if (loading) return <div className="v3-loading"><div className="spinner" />Loading workspace…</div>;
  if (error) return <div className="v3-ops-error">{error}</div>;
  if (!workspace || !workspace.item) return <div className="v3-ops-error">Workspace unavailable.</div>;

  const item = workspace.item || {};
  const data = workspace.data || {};
  const workflow = workspace.workflow || {};
  const issues = workspace.issues || [];
  const source = workspace.source || {};
  const findings = (workspace.validation && workspace.validation.findings) || [];

  // D19 — lock state is server-derived: items past the editable stages are
  // read-only in the workbench.
  const LOCKED_STATUSES = [
    'validating', 'validated', 'calculating', 'calculated', 'customer_review',
    'approved', 'rejected', 'qc_approved', 'qc_rejected', 'completed', 'failed',
  ];
  const locked = LOCKED_STATUSES.includes(item.status);

  const dataPane = (
    <>
      <div className="ct-pane__header">Structured data · {item.status || 'pending'}</div>
      <div className="ct-pane__body">
        {locked && (
          <div className="v3-ops-notice">
            <strong>Locked</strong> — this item is in “{item.status}” and is read-only in the workbench.
          </div>
        )}
        {findings.length > 0 && (
          <div className="v3-inline-card" style={{ marginTop: 10 }}>
            <strong>Validation findings ({findings.length})</strong>
            {findings.map((f, i) => (
              <div key={`${f.code}-${i}`} style={{ marginTop: 4 }}>
                <StatusBadge status={f.severity} />{' '}
                {f.field ? <code>{f.field}:</code> : null} {f.message || f.code}
              </div>
            ))}
          </div>
        )}
        <pre className="v3-mono" style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(data, null, 2)}</pre>
        {issues.length > 0 && (
          <div className="v3-inline-card" style={{ marginTop: 10 }}>
            <strong>Linked issues ({issues.length})</strong>
            {issues.map((issue) => (
              <div key={issue.id} style={{ marginTop: 4 }}>
                <StatusBadge status={issue.status} /> {issue.title || issue.issue_type}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );

  const workflowPane = renderActions ? renderActions({ workspace, item, data, workflow, issues }) : null;

  return (
    <WorkbenchShell
      stages={WB_STAGES}
      currentStage={stageForStatus(item.status)}
      preset={preset}
      onPresetChange={setPreset}
      sourceUrl={source.viewer_url}
      sourceTitle={source.file_name}
      allowDownload={allowDownload}
      status={item.status}
      locked={locked}
      data={dataPane}
      dataLabel="Data"
      actions={workflowPane}
    />
  );
}

