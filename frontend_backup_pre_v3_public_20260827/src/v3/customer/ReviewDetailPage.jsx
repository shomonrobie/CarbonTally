// frontend/src/v3/customer/ReviewDetailPage.jsx
// D2/D5/G-P0-2 — evidence-first customer review & approve workbench. Uses the
// shared D19 WorkbenchShell (top workflow nav + split source/data panes +
// status indicators). Approve/Reject is the distinct approver gate: org
// owner/admin only (D5), server-authoritative — the UI never approves locally.
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  getItemWorkspace,
  resolveV3Membership,
  submitCustomerReview,
} from '../api';
import WorkbenchShell from '../components/workbench/WorkbenchShell';
import { LoadingState, ErrorState, ConfirmationDialog, Alert, Button, StatusBadge } from '../components/ui';
import EvidenceRecordPanel from '../components/EvidenceRecordPanel';

const APPROVER_ROLES = ['owner', 'admin'];

const WORKFLOW_STAGES = [
  { id: 'queue', label: 'Queue' },
  { id: 'extract', label: 'Extract' },
  { id: 'map', label: 'Map' },
  { id: 'validate', label: 'Validate' },
  { id: 'review', label: 'Review' },
  { id: 'approve', label: 'Approve' },
  { id: 'evidence', label: 'Evidence' },
];

function stageForStatus(status) {
  if (['approved', 'rejected', 'qc_approved', 'qc_rejected', 'completed'].includes(status)) return 'approve';
  if (['calculated', 'customer_review'].includes(status)) return 'review';
  if (['validating', 'validated'].includes(status)) return 'validate';
  if (['mapping', 'mapped'].includes(status)) return 'map';
  return 'extract';
}

export default function ReviewDetailPage() {
  const { itemId } = useParams();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState(null);
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(null); // {tone:'approve'|'reject'}
  const [rejectionReason, setRejectionReason] = useState('');
  const [customerNotes, setCustomerNotes] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const membership = await resolveV3Membership();
      setRole(membership?.role || null);
      const w = await getItemWorkspace(itemId);
      setWorkspace(w);
    } catch (e) {
      setError(e.message || 'Failed to load the review workspace');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [itemId, retryCount]);

  const item = workspace?.item || {};
  const status = item.status;
  const isApprover = APPROVER_ROLES.includes(role);
  const data = workspace?.data || {};
  const source = workspace?.source || {};

  const keyFacts = useMemo(() => {
    const rows = [
      ['Status', <StatusBadge status={status} key="s" />],
      ['Extracted activity', data.extracted_data?.activity || '—'],
      ['Quantity', data.extracted_data?.quantity ? `${data.extracted_data.quantity} ${data.extracted_data.unit || ''}` : '—'],
      ['Mapped activity', data.mapped_data?.activity_type || '—'],
      ['Emission factor', data.mapped_data?.factor_label || data.emission_factor_used || '—'],
      ['Calculated (kg CO₂e)', data.calculated_emissions_kg_co2e ?? '—'],
    ];
    return rows;
  }, [status, data]);

  const onDecide = async () => {
    if (!isApprover) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const approved = confirm.tone === 'approve';
      if (!approved && !rejectionReason.trim()) {
        setError('A rejection reason is required.');
        setBusy(false);
        return;
      }
      await submitCustomerReview(itemId, {
        approved,
        rejection_reason: approved ? undefined : rejectionReason.trim(),
        customer_notes: customerNotes.trim() || undefined,
      });
      setNotice(approved ? 'Item approved.' : 'Item rejected and returned for correction.');
      setConfirm(null);
      setRejectionReason('');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to record your decision');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <LoadingState label="Loading review workspace…" />;
  if (error && !workspace) return <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  const alreadyDecided = ['approved', 'rejected'].includes(status);


  const dataPane = (
    <>
      <div className="ct-pane__header">Structured data &amp; evidence</div>
      <div className="ct-pane__body">
        <div className="v3-meta-list">
          {keyFacts.map(([k, v]) => (
            <div className="v3-meta-item" key={k}>
              <div className="k">{k}</div>
              <div className="v">{v}</div>
            </div>
          ))}
        </div>

        {item.evidence && <EvidenceRecordPanel evidence={item.evidence} />}

        {workspace.issues && workspace.issues.length > 0 && (
          <div style={{ marginTop: 14 }}>
            <h4>Linked issues</h4>
            {workspace.issues.map((issue) => (
              <div key={issue.id} className="v3-inline-card">
                <strong>{issue.title || issue.issue_type}</strong>
                <span style={{ marginLeft: 8 }}><StatusBadge status={issue.status} /></span>
              </div>
            ))}
          </div>
        )}

        {isApprover && !alreadyDecided && (
          <div style={{ marginTop: 18 }}>
            <label className="ct-field__label" htmlFor="review-notes">Notes (optional)</label>
            <textarea
              id="review-notes"
              className="ct-field__control"
              rows={3}
              value={customerNotes}
              onChange={(e) => setCustomerNotes(e.target.value)}
              placeholder="Context for this decision (stored with the audit record)."
            />
            <div className="ct-wb-actions" style={{ padding: '12px 0 0', border: 'none' }}>
              <Button variant="approve" icon="check" onClick={() => setConfirm({ tone: 'approve' })} disabled={busy}>
                Approve
              </Button>
              <Button variant="reject" icon="x" onClick={() => setConfirm({ tone: 'reject' })} disabled={busy}>
                Reject
              </Button>
            </div>
          </div>
        )}

        {!isApprover && (
          <p className="ct-field__hint" style={{ marginTop: 16 }}>
            You can review this item and its evidence. Approval is reserved for organisation owners and administrators.
          </p>
        )}

        {alreadyDecided && (
          <p className="ct-field__hint" style={{ marginTop: 16 }}>
            This item has already been decided ({status}). Decisions are recorded server-side with the reviewer identity
            and timestamp.
          </p>
        )}
      </div>
    </>
  );

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div className="v3-page" style={{ paddingBottom: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 20 }}>Review item</h1>
            <p className="v3-subtitle" style={{ marginTop: 4 }}>{item.file_name || 'Unnamed item'}</p>
          </div>
          <Button variant="secondary" icon="arrowLeft" onClick={() => navigate('/review')}>Back to queue</Button>
        </div>
        {notice && <Alert tone="success" title="Decision recorded">{notice}</Alert>}
        {error && <Alert tone="error" title="Decision not recorded">{error}</Alert>}
      </div>

      <WorkbenchShell
        stages={WORKFLOW_STAGES}
        currentStage={stageForStatus(status)}
        preset="50-50"
        sourceUrl={source.viewer_url}
        sourceTitle={source.file_name}
        status={status}
        data={dataPane}
        dataLabel="Data & evidence"
        actions={
          <Button variant="secondary" onClick={() => navigate('/review')}>Close</Button>
        }
      />

      {confirm && (
        <ConfirmationDialog
          open
          title={confirm.tone === 'approve' ? 'Approve this item?' : 'Reject this item?'}
          message={
            confirm.tone === 'approve'
              ? 'Approval records a customer decision on this calculated result. The decision is stored server-side with your identity and timestamp.'
              : 'Rejection returns the item for correction. A reason is required.'
          }
          confirmLabel={confirm.tone === 'approve' ? 'Approve' : 'Reject'}
          tone={confirm.tone}
          busy={busy}
          onClose={() => setConfirm(null)}
          onConfirm={onDecide}
        >
          {confirm.tone === 'reject' && (
            <label className="ct-field__label" htmlFor="rejection-reason">
              Rejection reason <span className="ct-field__required">*</span>
              <textarea
                id="rejection-reason"
                className="ct-field__control"
                rows={3}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Explain what needs correcting."
              />
            </label>
          )}
        </ConfirmationDialog>
      )}
    </div>
  );
}
