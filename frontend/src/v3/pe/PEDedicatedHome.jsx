// frontend/src/v3/pe/PEDedicatedHome.jsx
// V1.2 — dedicated Processing Entity application home (/pe).
//
// Frozen PE roles (Data Entry Operator, Reviewer, QC Specialist, Admin) —
// the capability set shown here comes from the server (GET /api/v3/pe/me),
// and every action calls the /api/v3/pe/* endpoints, which remain the
// authoritative authorization + workflow boundary. This page:
//   * shows the PE-controlled pipeline (Extraction → Mapping → Validation →
//     Calculation → PE Review → PE QC) and stops at the PE-controlled stages;
//   * never shows CarbonTally QC or Customer Approval controls;
//   * renders Review/QC actions ONLY for capabilities the backend returned
//     (Reviewer → PE Review; QC Specialist → PE QC; Admin → both, never CT QC;
//     Data Entry Operator → neither).
import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getPeBatchItems,
  getPeMe,
  getPeWork,
  peQcDecision,
  peReviewDecision,
} from '../api';
import {
  Alert,
  Button,
  LoadingState,
} from '../components/ui';
import DataTable from '../components/ui/DataTable';
import '../ops/ops.css';
import '../ops/v12.css';

const PE_PIPELINE = ['Extraction', 'Mapping', 'Validation', 'Calculation', 'PE Review', 'PE QC'];

const REVIEW_READY = ['calculated', 'pe_review', 'pe_reviewed'];
const QC_READY = ['pe_reviewed', 'pe_qc', 'pe_qc_approved'];

const can = (caps, key) => (caps || []).includes(key);

export default function PEDedicatedHome() {
  const [me, setMe] = useState(null);
  const [meError, setMeError] = useState('');
  const [batches, setBatches] = useState([]);
  const [batchItems, setBatchItems] = useState({});
  const [loading, setLoading] = useState(true);
  const [openBatch, setOpenBatch] = useState(null);
  const [notice, setNotice] = useState('');
  const [actionError, setActionError] = useState('');
  const [acting, setActing] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setMeError('');
    try {
      const meBody = await getPeMe();
      setMe(meBody);
      const workBody = await getPeWork();
      setBatches(workBody.batches || []);
    } catch (e) {
      setMeError(e.message || 'Unable to load the Processing Entity workspace.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  const loadBatch = async (batchId) => {
    try {
      const body = await getPeBatchItems(batchId);
      setBatchItems((prev) => ({ ...prev, [batchId]: body.items || [] }));
      setOpenBatch(batchId);
    } catch (e) {
      setActionError(e.message || 'Failed to load the batch items.');
    }
  };

  const decide = async (itemId, kind, approved) => {
    setActing(true);
    setActionError('');
    setNotice('');
    try {
      if (kind === 'review') {
        await peReviewDecision(itemId, approved);
      } else {
        await peQcDecision(itemId, approved);
      }
      setNotice(`${kind === 'review' ? 'PE Review' : 'PE QC'} ${approved ? 'approved' : 'rejected'} — decision recorded.`);
      if (openBatch) loadBatch(openBatch);
      setRefreshKey((k) => k + 1);
    } catch (e) {
      setActionError(e.message || 'Decision could not be applied.');
    } finally {
      setActing(false);
    }
  };

  if (loading) return <LoadingState label="Loading Processing Entity workspace…" />;

  if (meError) {
    return (
      <Alert tone="info" title="Processing Entity workspace">
        {meError}. Only active Processing Entity members (Data Entry Operator,
        Reviewer, QC Specialist or Admin) can use this application.
      </Alert>
    );
  }

  const caps = me.capabilities || [];
  const showReview = can(caps, 'review');
  const showQc = can(caps, 'qc');
  const entityId = me.entity.id;

  return (
    <div className="v3-ops-page">
      <div className="v3-ops-header">
        <div>
          <h1>Processing Entity workspace</h1>
          <div className="subtitle">
            {me.entity.name} · {me.role.label || me.role.key}
          </div>
        </div>
      </div>
      <div className="v12-panel">
        <h3 style={{ marginTop: 0 }}>PE-controlled pipeline</h3>
        <div className="v12-stage-rail">
          {PE_PIPELINE.map((s, i) => (
            <React.Fragment key={s}>
              {i > 0 && <span className="v12-stage-arrow">→</span>}
              <span className="v12-stage">{s}</span>
            </React.Fragment>
          ))}
          <span className="v12-stage-arrow">→</span>
          <span className="v12-stage stop">CarbonTally QC · Customer Approval (handed off — not PE actions)</span>
        </div>
        <p className="v12-muted" style={{ marginTop: 6 }}>
          Your role grants:
          {' '}{(caps).join(', ') || 'read_work'}. CarbonTally QC and customer
          approval are performed by CarbonTally and the customer on separate
          surfaces after your entity hands the work over.
        </p>
      </div>

      {actionError && <Alert tone="error" title="Action not applied">{actionError}</Alert>}
      {notice && <Alert tone="success" title="Decision recorded">{notice}</Alert>}

      {batches.length === 0 ? (
        <Alert tone="info" title="No assigned work">
          CarbonTally has not assigned any batches to this Processing Entity yet.
        </Alert>
      ) : (
        <div>
          {batches.map((batch) => (
            <div className="v12-panel" key={batch.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                <div>
                  <h3 style={{ margin: 0 }}>{batch.batch_name || batch.id}</h3>
                  <div className="v12-muted">
                    {batch.item_count} item{batch.item_count === 1 ? '' : 's'} · batch state: {batch.status || 'pending'}
                  </div>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={acting}
                  onClick={() => (openBatch === batch.id ? setOpenBatch(null) : loadBatch(batch.id))}
                >
                  {openBatch === batch.id ? 'Hide items' : 'Show items'}
                </Button>
              </div>

              {openBatch === batch.id && (
                <div style={{ marginTop: 12 }}>
                  {(batchItems[batch.id] || []).length === 0 ? (
                    <Alert tone="info" title="No items in this batch">
                      This batch currently has no extractable items.
                    </Alert>
                  ) : (
                    <DataTable
                      caption={`Assigned work — ${batch.batch_name || batch.id}`}
                      columns={[
                        {
                          key: 'file_name',
                          header: 'File',
                          accessor: 'file_name',
                          render: (row) => (
                            <Link to={`/pe/items/${encodeURIComponent(entityId)}/${encodeURIComponent(row.id)}`}>
                              {(row.file_name || row.id || '—').slice(0, 60)}
                            </Link>
                          ),
                        },
                        {
                          key: 'status',
                          header: 'State',
                          accessor: 'status',
                          sortable: true,
                          render: (row) => <span className="v12-stage active">{row.status || 'pending'}</span>,
                        },
                        {
                          key: 'actions',
                          header: 'Actions',
                          accessor: 'id',
                          render: (row) => {
                            const st = row.status;
                            const reviewable = showReview && REVIEW_READY.includes(st);
                            const qcable = showQc && QC_READY.includes(st);
                            const actions = [];
                            if (reviewable) {
                              actions.push(
                                <Button key="r-app" size="sm" variant="primary" disabled={acting} onClick={() => decide(row.id, 'review', true)}>
                                  PE Review approve
                                </Button>,
                                <Button key="r-rej" size="sm" disabled={acting} onClick={() => decide(row.id, 'review', false)}>
                                  PE Review reject
                                </Button>,
                              );
                            }
                            if (qcable) {
                              actions.push(
                                <Button key="q-app" size="sm" variant="primary" disabled={acting} onClick={() => decide(row.id, 'qc', true)}>
                                  PE QC approve
                                </Button>,
                                <Button key="q-rej" size="sm" disabled={acting} onClick={() => decide(row.id, 'qc', false)}>
                                  PE QC reject
                                </Button>,
                              );
                            }
                            if (actions.length === 0) {
                              return <span className="v12-muted">Open item workspace to process</span>;
                            }
                            return <div className="v12-actions">{actions}</div>;
                          },
                        },
                      ]}
                      rows={batchItems[batch.id] || []}
                      rowKey="id"
                    />
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
