// frontend/src/v3/ops/ProcessingEntitiesTab.jsx
// CarbonTally-internal Processing Entity provisioning — list + create over the
// real V3 surfaces (/api/v3/ops/entities for staff reads, /api/v3/processing-entities
// for admin creates). This is the surface that lets internal staff route work to
// a Processing Entity (D22) before assigning batches via the Data entry queue.
import React, { useCallback, useEffect, useState } from 'react';
import { createProcessingEntity, listProcessingEntities } from '../api';

export default function ProcessingEntitiesTab({ canManage }) {
  const [entities, setEntities] = useState([]);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState(25);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({ name: '', description: '' });
  const [creating, setCreating] = useState(false);

  const load = useCallback(async (nextLimit = limit, nextOffset = offset) => {
    try {
      const result = await listProcessingEntities(nextLimit, nextOffset);
      setEntities(result.entities || []);
      setTotal(result.total ?? result.entities?.length ?? 0);
      setLimit(nextLimit);
      setOffset(nextOffset);
    } catch (e) {
      setError(e.message || 'Failed to load processing entities');
    }
  }, [limit, offset]);

  useEffect(() => { load(); }, [load]);

  const onCreate = async () => {
    if (!form.name.trim()) return;
    setError('');
    setNotice('');
    setCreating(true);
    try {
      await createProcessingEntity({
        name: form.name.trim(),
        description: form.description.trim() || null,
        status: 'active',
        metadata: {},
      });
      setForm({ name: '', description: '' });
      setNotice('Processing entity created.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to create processing entity');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Create processing entity</h3>
        {!canManage ? (
          <div className="v3-ops-notice">
            Only internal staff who can manage staff may create processing entities.
          </div>
        ) : (
          <div className="workspace-grid">
            <div className="workspace-field">
              <label>Name</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Acme Processing Ltd"
              />
            </div>
            <div className="workspace-field">
              <label>Description (optional)</label>
              <input
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Back-office extraction partner"
              />
            </div>
            <div className="workspace-actions">
              <button className="v3-btn primary" onClick={onCreate} disabled={creating || !form.name.trim()}>
                {creating ? 'Creating…' : 'Create entity'}
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="workspace-pane">
        <h3>Processing entities ({total})</h3>
        {entities.length === 0 ? (
          <div className="v3-ops-notice">
            No processing entities yet. Create one above, then assign staff and batches.
          </div>
        ) : (
          <table className="v3-ops-table">
            <thead>
              <tr><th>Name</th><th>Description</th><th>Status</th></tr>
            </thead>
            <tbody>
              {entities.map((entity) => (
                <tr key={entity.id}>
                  <td>{entity.name}</td>
                  <td className="v3-muted">{entity.description || '—'}</td>
                  <td>{entity.status || 'active'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {total > limit && (
          <div className="ct-table-pagination">
            <span className="ct-table-pagination-count">
              {offset + 1}–{Math.min(total, offset + entities.length)} of {total}
            </span>
            <button type="button" className="v3-btn v3-btn-sm" disabled={offset <= 0} onClick={() => load(limit, Math.max(0, offset - limit))}>← Prev</button>
            <span className="ct-table-pagination-count">Page {Math.floor(offset / limit) + 1} of {Math.max(1, Math.ceil(total / limit))}</span>
            <button type="button" className="v3-btn v3-btn-sm" disabled={offset + limit >= total} onClick={() => load(limit, offset + limit)}>Next →</button>
            <select className="ct-table-pagination-select" aria-label="Rows per page" value={limit} onChange={(e) => load(Number(e.target.value), 0)}>
              {[10, 25, 50, 100].map((s) => <option key={s} value={s}>{s} / page</option>)}
            </select>
          </div>
        )}
      </div>
    </div>
  );
}
