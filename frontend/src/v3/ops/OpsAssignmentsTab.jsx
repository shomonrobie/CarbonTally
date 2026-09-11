// frontend/src/v3/ops/OpsAssignmentsTab.jsx
// WS4 Gate 3 — Operations item-level processing assignment surface. Consumes the
// approved 4C D38 endpoints (/api/v3/ops/items/{id}/work/*) for BOTH target
// kinds (Processing Entity OR CarbonTally internal staff). An authorised
// CarbonTally Operations user can assign an individual work item to a PE or an
// internal staff member and reassign between them (PE->PE, PE->Internal,
// Internal->PE). The row shows the canonical assignment context:
//   * batch default    (batch-level fallback, read from the batch object)
//   * item assignment  (current open D38 ledger row from the API)
//   * effective processor (the API's canonical `effective` summary — the
//     frontend never re-derives the effective rule itself).
// Every mutation goes through the V3 HTTP API; the UI is not a security
// boundary and never touches Supabase assignment tables directly.
//
// The batch directory intentionally includes BOTH internal/unassigned batches
// (operator queue) and batches defaulted to an active Processing Entity, so a
// mixed batch (A->Alpha, B->Beta, D->Internal …) is visible and each row can
// carry its own item-level processor.
import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getEntityExtractionBatches,
  getOperatorQueue,
  getOpsBatchItems,
  listOpsStaff,
  listProcessingEntities,
  opsWorkAssignTarget,
  opsWorkClaim,
  opsWorkComplete,
  opsWorkInfo,
  opsWorkReassignTarget,
  opsWorkRelease,
} from '../api';
import DataTable from '../components/ui/DataTable';
import { Alert, Button, LoadingState } from '../components/ui';

const shortId = (value) => (value ? `…${String(value).replace(/-/g, '').slice(-6)}` : '—');

const nameOf = (person) => {
  if (!person) return '—';
  const full = `${person.first_name || ''} ${person.last_name || ''}`.trim();
  return full || person.email || shortId(person.user_id);
};

const partyLabel = (kind, assignee, staffById, entityById) => {
  if (!assignee) return '—';
  if (kind === 'processing_entity') return entityById[assignee] || `PE ${shortId(assignee)}`;
  if (kind === 'internal_staff') return staffById[assignee] || `Internal staff ${shortId(assignee)}`;
  return shortId(assignee);
};

const batchDefaultLabel = (batch, staffById, entityById) => {
  if (!batch) return '—';
  if (batch.entity_id) return entityById[batch.entity_id] || `PE ${shortId(batch.entity_id)}`;
  if (batch.assigned_to) return staffById[batch.assigned_to] || `Internal staff ${shortId(batch.assigned_to)}`;
  return 'None (CarbonTally queue)';
};

const sameEntity = (current, entityId) =>
  !!current && current.assignee_kind === 'processing_entity'
  && String(current.processing_entity_id) === String(entityId);
const sameStaff = (current, userId) =>
  !!current && current.assignee_kind === 'internal_staff'
  && String(current.assigned_to) === String(userId);

export default function OpsAssignmentsTab() {
  const [batches, setBatches] = useState([]);          // directory rows {id,batch,kind,context}
  const [staffById, setStaffById] = useState({});
  const [entityById, setEntityById] = useState({});
  const [staffOptions, setStaffOptions] = useState([]);
  const [entityOptions, setEntityOptions] = useState([]);
  const [activeRow, setActiveRow] = useState(null);    // open directory row
  const [items, setItems] = useState([]);
  const [work, setWork] = useState({});                 // itemId -> {info|error}
  const [targets, setTargets] = useState({});           // `${itemId}:entity|staff` -> id
  const [loading, setLoading] = useState(true);
  const [itemsLoading, setItemsLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [actionError, setActionError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const q = await getOperatorQueue('', 100, 0);
      const internalRows = (q.batches || []).filter((r) => r.batch && r.batch.entity_id == null);

      let staffRows = [];
      let entities = [];
      try {
        staffRows = (await listOpsStaff()).staff || [];
      } catch (_e) { staffRows = []; }
      try {
        entities = (await listProcessingEntities(100, 0, 'active')).entities || [];
      } catch (_e) { entities = []; }

      const sById = {};
      staffRows.forEach((m) => { if (m && m.user_id) sById[m.user_id] = nameOf(m); });
      const eById = {};
      entities.forEach((en) => { if (en && en.id) eById[en.id] = en.name || shortId(en.id); });
      setStaffById(sById);
      setEntityById(eById);
      setStaffOptions(staffRows.filter((m) => m && m.is_active !== false && !m.entity_id));
      setEntityOptions(entities.filter((en) => en && en.status === 'active'));

      const rows = internalRows.map((r) => ({
        id: r.batch.id,
        batch: r.batch,
        kind: 'internal',
        context: (r.organization && r.organization.name) || 'CarbonTally internal batch',
      }));
      const seen = {};
      rows.forEach((r) => { seen[r.id] = true; });
      // Batches defaulted to each ACTIVE processing entity. Load failures for
      // one entity must not block the whole tab.
      for (const en of entities) {
        if (!en || en.status !== 'active') continue;
        try {
          const body = await getEntityExtractionBatches(en.id);
          for (const b of body.batches || []) {
            if (seen[b.id]) continue;
            seen[b.id] = true;
            rows.push({ id: b.id, batch: b, kind: 'pe', context: `Processing Entity: ${en.name || shortId(en.id)}` });
          }
        } catch (_e) { /* per-entity batch listing is best effort for context */ }
      }
      setBatches(rows);
    } catch (e) {
      setError(e.message || 'Unable to load work assignment batches.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const refreshItemWork = useCallback(async (itemId) => {
    try {
      const info = await opsWorkInfo(itemId);
      setWork((prev) => ({ ...prev, [itemId]: { info } }));
    } catch (e) {
      setWork((prev) => ({ ...prev, [itemId]: { error: e.message || 'Failed' } }));
    }
  }, []);

  const openBatch = async (row) => {
    setActiveRow(row);
    setActionError('');
    setNotice('');
    setItemsLoading(true);
    setItems([]);
    setWork({});
    try {
      const result = await getOpsBatchItems(row.batch.id);
      const batchItems = result.items || [];
      setItems(batchItems);
      await Promise.all(batchItems.map((it) => refreshItemWork(it.id)));
    } catch (e) {
      setActionError(e.message || 'Failed to load batch items.');
    } finally {
      setItemsLoading(false);
    }
  };

  const runAction = async (itemId, fn, okLabel) => {
    setBusy(true);
    setActionError('');
    setNotice('');
    try {
      await fn();
      setNotice(okLabel);
      setTargets((t) => {
        const next = { ...t };
        delete next[`${itemId}:entity`];
        delete next[`${itemId}:staff`];
        return next;
      });
      await refreshItemWork(itemId);
    } catch (e) {
      // Server validation/authorization detail is surfaced for 4xx responses
      // (friendlyError keeps raw detail available on error.raw for developers).
      setActionError(e.message || 'Action could not be applied.');
    } finally {
      setBusy(false);
    }
  };

  const applyTarget = (item, kind) => {
    const current = work[item.id]?.info?.current || null;
    const target = kind === 'entity'
      ? { entity_id: targets[`${item.id}:entity`] }
      : { assigned_to: targets[`${item.id}:staff`] };
    const value = kind === 'entity' ? target.entity_id : target.assigned_to;
    if (!value) return;
    const unchanged = kind === 'entity'
      ? sameEntity(current, value)
      : sameStaff(current, value);
    if (unchanged) {
      setNotice('Item is already assigned to that party.');
      return;
    }
    const isReassign = !!current;
    const label = kind === 'entity'
      ? (isReassign ? 'Item reassigned to the processing entity.' : 'Item assigned to the processing entity.')
      : (isReassign ? 'Item reassigned to the internal staff member.' : 'Item assigned to the internal staff member.');
    const fn = isReassign
      ? () => opsWorkReassignTarget(item.id, target)
      : () => opsWorkAssignTarget(item.id, target);
    runAction(item.id, fn, label);
  };

  if (loading) return <LoadingState label="Loading work assignment batches…" />;

  const openItems = items.length > 0 || itemsLoading || activeRow;
  const workRow = (item) => work[item.id] || {};


  return (
    <div className="v3-ops-page">
      {error && <Alert tone="error" title="Failed to load">{error}</Alert>}
      {notice && <Alert tone="success" title="Action recorded">{notice}</Alert>}
      {actionError && <Alert tone="error" title="Action not applied">{actionError}</Alert>}

      {batches.length === 0 ? (
        <Alert tone="info" title="Nothing awaiting assignment">
          No work batches are currently visible to item-level assignment. New
          internal batches appear here when they are open/unassigned, and
          Processing Entity default batches appear under their entity.
        </Alert>
      ) : (
        <DataTable
          caption={`Work batches for item-level processing assignment — ${batches.length} batch(es)`}
          rowKey="id"
          rows={batches}
          columns={[
            { key: 'name', header: 'Batch', render: (r) => r.batch.batch_name || shortId(r.batch.id) },
            { key: 'context', header: 'Context', render: (r) => <span className="v12-muted">{r.context}</span> },
            {
              key: 'default',
              header: 'Batch default party',
              render: (r) => (
                <span className="v12-stage">{batchDefaultLabel(r.batch, staffById, entityById)}</span>
              ),
            },
            { key: 'status', header: 'State', accessor: 'batch.status' },
            {
              key: 'open', header: '',
              render: (r) => <Button size="sm" disabled={busy} onClick={() => openBatch(r)}>Open items</Button>,
            },
          ]}
        />
      )}

      {openItems && (
        <section style={{ marginTop: 24 }}>
          <h3>
            {activeRow
              ? `Items — ${activeRow.batch.batch_name || shortId(activeRow.batch.id)}`
              : 'Batch items — D38 item assignment'}
          </h3>
          {itemsLoading ? (
            <LoadingState label="Loading batch items…" />
          ) : items.length === 0 ? (
            <div className="v3-ops-notice">No items in this batch yet.</div>
          ) : (
            <DataTable
              rowKey="id"
              rows={items}
              columns={[
                { key: 'file', header: 'Item', accessor: 'file_name', render: (r) => r.file_name || r.id },
                { key: 'status', header: 'State', accessor: 'status', sortable: true },

                {
                  key: 'assignment',
                  header: 'Assignment (batch default · item · effective)',
                  render: (r) => {
                    const info = workRow(r).info;
                    const err = workRow(r).error;
                    if (err) return <span className="v12-muted">{err}</span>;
                    if (!info) return <span className="v12-muted">…</span>;
                    const current = info.current || null;
                    const eff = info.effective || null;
                    const effectiveParty = eff
                      ? (eff.kind === 'processing_entity'
                        ? partyLabel('processing_entity', eff.assignee, staffById, entityById)
                        : eff.kind === 'internal_staff'
                          ? partyLabel('internal_staff', eff.assignee, staffById, entityById)
                          : 'Unassigned')
                      : 'Unassigned';
                    const sourceWord = eff && eff.source === 'item'
                      ? 'item assignment'
                      : eff && eff.source === 'batch'
                        ? 'batch default'
                        : 'no assignment';
                    return (
                      <div>
                        <div className="v12-muted" style={{ fontSize: '0.78rem', lineHeight: 1.5 }}>
                          <div>Batch default: {batchDefaultLabel(activeRow.batch, staffById, entityById)}</div>
                          {current && (
                            <div>
                              Item assignment:{' '}
                              {partyLabel(
                                current.assignee_kind,
                                current.assignee_kind === 'processing_entity'
                                  ? current.processing_entity_id
                                  : current.assigned_to,
                                staffById,
                                entityById,
                              )}
                              {current.action === 'reassign' ? ' (reassigned)' : ''}
                            </div>
                          )}
                          {current && (current.previous_assigned_to || current.previous_processing_entity_id) && (
                            <div>
                              Previous:{' '}
                              {current.previous_processing_entity_id
                                ? partyLabel('processing_entity', current.previous_processing_entity_id, staffById, entityById)
                                : partyLabel('internal_staff', current.previous_assigned_to, staffById, entityById)}
                            </div>
                          )}
                        </div>
                        <div style={{ marginTop: 4 }}>
                          <span className="v12-stage active">Effective: {effectiveParty}</span>{' '}
                          <span className="v12-muted" style={{ fontSize: '0.72rem' }}>({sourceWord})</span>
                        </div>
                        <details style={{ marginTop: 4 }}>
                          <summary className="v12-muted" style={{ cursor: 'pointer', fontSize: '0.75rem' }}>
                            History ({info.history?.length || 0})
                          </summary>
                          <ul style={{ paddingLeft: 14, margin: '6px 0', fontSize: '0.75rem', color: '#334155' }}>
                            {(info.history || []).map((h) => (
                              <li key={h.id}>
                                {h.action}{h.close_action ? ` → ${h.close_action}` : ''} · {h.actor_domain}
                                {h.reason ? ` · “${h.reason}”` : ''} · {h.created_at}
                              </li>
                            ))}
                          </ul>
                        </details>
                      </div>
                    );
                  },
                },

                {
                  key: 'actions',
                  header: 'Assign / reassign',
                  render: (r) => {
                    const entry = workRow(r);
                    const info = entry.info;
                    const current = info?.current || null;
                    const eff = info?.effective || null;
                    const canClose = !!current && !(eff && eff.kind === 'processing_entity');
                    const itemLabel = r.file_name || r.id;
                    return (
                      <div className="v12-actions" style={{ alignItems: 'center', flexWrap: 'wrap' }}>
                        <Button size="sm" variant="primary" disabled={busy} onClick={() => runAction(r.id, () => opsWorkClaim(r.id), 'Assigned to you (claim).')}>
                          Assign to me
                        </Button>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <select
                            aria-label={`Assign ${itemLabel} to processing entity`}
                            value={targets[`${r.id}:entity`] || ''}
                            disabled={busy}
                            onChange={(e) => setTargets((t) => ({ ...t, [`${r.id}:entity`]: e.target.value }))}
                            style={{ padding: '4px 6px', maxWidth: 190 }}
                          >
                            <option value="">Processing entity…</option>
                            {entityOptions.map((en) => (
                              <option key={en.id} value={en.id}>{en.name || shortId(en.id)}</option>
                            ))}
                          </select>
                          <Button
                            size="sm"
                            disabled={busy || !targets[`${r.id}:entity`] || sameEntity(current, targets[`${r.id}:entity`])}
                            onClick={() => applyTarget(r, 'entity')}
                          >
                            {current ? 'Reassign to PE' : 'Assign to PE'}
                          </Button>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <select
                            aria-label={`Assign ${itemLabel} to internal staff`}
                            value={targets[`${r.id}:staff`] || ''}
                            disabled={busy}
                            onChange={(e) => setTargets((t) => ({ ...t, [`${r.id}:staff`]: e.target.value }))}
                            style={{ padding: '4px 6px', maxWidth: 190 }}
                          >
                            <option value="">Internal staff…</option>
                            {staffOptions.map((m) => (
                              <option key={m.user_id} value={m.user_id}>
                                {nameOf(m)} ({m.role_name || 'staff'})
                              </option>
                            ))}
                          </select>
                          <Button
                            size="sm"
                            disabled={busy || !targets[`${r.id}:staff`] || sameStaff(current, targets[`${r.id}:staff`])}
                            onClick={() => applyTarget(r, 'staff')}
                          >
                            {current ? 'Reassign to staff' : 'Assign to staff'}
                          </Button>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <Button size="sm" disabled={busy || !canClose} onClick={() => runAction(r.id, () => opsWorkRelease(r.id), 'Assignment released.')}>
                            Release
                          </Button>
                          <Button size="sm" disabled={busy || !canClose} onClick={() => runAction(r.id, () => opsWorkComplete(r.id), 'Assignment completed.')}>
                            Complete
                          </Button>
                          <Link className="v3-btn v3-btn-sm" to={`/ops/items/${encodeURIComponent(r.id)}?tab=assignments`}>
                            Open item
                          </Link>
                        </div>
                      </div>
                    );
                  },
                },
              ]}
            />
          )}
        </section>
      )}
    </div>
  );
}

