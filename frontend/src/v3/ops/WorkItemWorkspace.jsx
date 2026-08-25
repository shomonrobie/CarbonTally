// frontend/src/v3/ops/WorkItemWorkspace.jsx
// Shared split-screen processing workspace — the SAME workspace contract as the
// Phase 3 surface (`source` + `data` + `status` + `issues` + `workflow`).
// Role-specific controls are layered on top via the `renderActions` render prop:
//   Data Entry -> extraction + mapping
//   Reviewer   -> extraction + mapping + validation + review
//   QC         -> extraction + mapping + factor + calculation + validation + QC
import React, { useEffect, useState } from 'react';
import { getItemWorkspace } from '../api';

export default function WorkItemWorkspace({ itemId, renderActions }) {
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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

  return (
    <div>
      <div className="workspace-grid">
        <div className="workspace-pane">
          <h3>Source document</h3>
          <div className="workspace-field">
            <strong>{item.file_name || 'Document'}</strong>
          </div>
          <pre>{JSON.stringify(workspace.source || {}, null, 2)}</pre>
        </div>
        <div className="workspace-pane">
          <h3>Data ({item.status || 'pending'})</h3>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      </div>

      <div className="workspace-pane" style={{ marginTop: 16 }}>
        <h3>Workflow</h3>
        <div className="workspace-field">
          Stage: <strong>{workflow.stage || '—'}</strong> · Status: <strong>{item.status}</strong>
        </div>
        {issues.length > 0 && (
          <div className="workspace-field">
            <div className="v3-ops-badge failed">Issues: {issues.length}</div>
            <pre>{JSON.stringify(issues, null, 2)}</pre>
          </div>
        )}
        {renderActions && renderActions({ workspace, item, data, workflow, issues })}
      </div>
    </div>
  );
}
