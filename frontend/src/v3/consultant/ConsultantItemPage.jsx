// frontend/src/v3/consultant/ConsultantItemPage.jsx
// CON-3 / Phase G — dedicated routed processing workspace for a consultant's
// client item. The shared /api/v3/processing/* surface is consultant-authorized
// (active consultant_clients grant), so the same ExtractionPanel drives the
// real durable pipeline: extract → map → validate → calculate → evidence.
// Route: /consultant/items/:clientId/:itemId
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  calculateItem,
  consultantReviewItem,
  consultantSubmitItem,
  extractItem,
  getClientProcessingItems,
  getConsultantItemWorkspace,
  getMappingOptions,
  mapItem,
  startItem,
} from '../api';
import ExtractionPanel from '../ops/ExtractionPanel';
import { Button, LoadingState, ErrorState } from '../components/ui';

const INTERNAL_API = {
  startItem,
  extractItem,
  mapItem,
  calculateItem,
  getMappingOptions,
};

// P6-2B workflow-state eligibility (server-enforced; mirrored here for the UI).
const REVIEWABLE_STATUS = 'calculated';
const SUBMITTABLE_STATUS = 'consultant_reviewed';

const STATUS_LABELS = {
  pending: 'Pending',
  extracted: 'Extracted',
  mapped: 'Mapped',
  validated: 'Validated',
  calculated: 'Calculated — ready for consultant review',
  consultant_reviewed: 'Consultant reviewed — ready to submit to QC',
  reviewed: 'Submitted — awaiting CarbonTally QC',
  ct_qc_approved: 'CarbonTally QC approved — awaiting customer decision',
  ct_qc_rejected: 'CarbonTally QC rejected — rework required',
  approved: 'Approved',
  rejected: 'Rejected — rework required',
};

export default function ConsultantItemPage() {
  const { clientId, itemId } = useParams();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [showRework, setShowRework] = useState(false);
  const [reworkReason, setReworkReason] = useState('');

  const load = useCallback(async (id) => {
    setLoading(true);
    setError('');
    try {
      // P6-2F — scope-aware processing workspace (consultants are NOT staff, so
      // the internal /api/v3/ops workspace would correctly deny them).
      const ws = await getConsultantItemWorkspace(id);
      setWorkspace(ws);
      const list = await getClientProcessingItems(clientId);
      setItems(list.items || []);
    } catch (e) {
      setError(e.message || 'Failed to open item workspace');
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => {
    if (itemId) load(itemId);
  }, [itemId, load]);

  const onNavigate = useCallback((nextId) => {
    navigate(`/consultant/items/${encodeURIComponent(clientId)}/${encodeURIComponent(nextId)}`);
  }, [clientId, navigate]);

  const act = useCallback(async (fn, successMessage) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await fn();
      setNotice(successMessage);
      setShowRework(false);
      setReworkReason('');
      await load(itemId);
    } catch (e) {
      // The backend is the authorization boundary: a denied consultant action
      // surfaces here as an error and changes nothing.
      setError(e.message || 'Action failed');
    } finally {
      setBusy(false);
    }
  }, [itemId, load]);

  if (loading) return <LoadingState label="Loading item workspace…" />;
  if (error && !workspace) return <ErrorState message={error} onRetry={() => load(itemId)} />;
  if (!workspace) return <ErrorState message="Item not found." onRetry={() => load(itemId)} />;

  const status = workspace.item?.status || workspace.status?.status || '';
  const canReview = status === REVIEWABLE_STATUS;
  const canSubmit = status === SUBMITTABLE_STATUS;

  const onPassReview = () => act(
    () => consultantReviewItem(itemId, { passed: true }),
    'Review passed — the item is ready to submit to CarbonTally QC.',
  );
  const onSubmitToQc = () => act(
    () => consultantSubmitItem(itemId),
    'Submitted to CarbonTally QC.',
  );
  const onRequestRework = () => {
    if (!reworkReason.trim()) {
      setError('A rework reason is required.');
      return;
    }
    act(
      () => consultantReviewItem(itemId, { passed: false, rejection_reason: reworkReason.trim() }),
      'Returned for rework.',
    );
  };


  return (
    <div className="v3-ops-page">
      <div className="v3-ops-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h1>Client item workspace</h1>
          <div className="subtitle">
            {workspace.organization?.name ? `${workspace.organization.name} · ` : ''}
            {workspace.item?.file_name || '—'} · {STATUS_LABELS[status] || status}
          </div>
        </div>
        <Button variant="secondary" size="sm" onClick={() => navigate(`/consultant?client=${encodeURIComponent(clientId)}&view=workspace`)}>
          ← Back to client workspace
        </Button>
      </div>

      {notice && <div className="v3-note" role="status">{notice}</div>}
      {error && <ErrorState inline message={error} onRetry={() => setError('')} />}

      {(canReview || canSubmit) && (
        <div className="v3-card" style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
          <strong style={{ marginRight: 8 }}>Consultant review</strong>
          {canReview && (
            <>
              <Button size="sm" disabled={busy} onClick={onPassReview}>Pass review</Button>
              <Button size="sm" variant="secondary" disabled={busy} onClick={() => { setShowRework((v) => !v); setError(''); }}>
                Request rework
              </Button>
            </>
          )}
          {canSubmit && (
            <Button size="sm" disabled={busy} onClick={onSubmitToQc}>
              Submit to CarbonTally QC
            </Button>
          )}
          {showRework && canReview && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', width: '100%', marginTop: 8 }}>
              <label htmlFor="rework-reason" className="v3-muted">Rework reason (required)</label>
              <input
                id="rework-reason"
                type="text"
                value={reworkReason}
                onChange={(e) => setReworkReason(e.target.value)}
                style={{ flex: 1, minWidth: 200 }}
              />
              <Button size="sm" variant="secondary" disabled={busy} onClick={onRequestRework}>Confirm rework</Button>
            </div>
          )}
        </div>
      )}

      <ExtractionPanel
        item={workspace.item}
        items={items}
        api={INTERNAL_API}
        onItemChange={onNavigate}
        mode="staff"
        suggestions={workspace.source?.ocr_suggestions || null}
        validation={(workspace.validation && workspace.validation.findings) || []}
      />
    </div>
  );
}
