// frontend/src/v3/customer/ReviewPage.jsx
// D2/D5/G-P0-2 — Customer review queue: items awaiting customer verification,
// evidence-first. Review (read) is available to all members; Approve/Reject is
// the distinct approver action (org owner/admin, D5) — enforced server-side.
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCustomerReviewQueue, resolveV3Membership } from '../api';
import { LoadingState, ErrorState, EmptyState } from '../components/ui';
import StatusBadge from '../components/ui/StatusBadge';
import DataTable from '../components/ui/DataTable';
import Button from '../components/ui/Button';

const APPROVER_ROLES = ['owner', 'admin'];

export default function ReviewPage() {
  const navigate = useNavigate();
  const [org, setOrg] = useState(null);
  const [role, setRole] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const membership = await resolveV3Membership();
      if (!membership || !membership.org) {
        setError('No organization is linked to this account.');
        setLoading(false);
        return;
      }
      setOrg(membership.org);
      setRole(membership.role);
      const result = await getCustomerReviewQueue(membership.org.id);
      setItems(result.items || []);
    } catch (e) {
      setError(e.message || 'Failed to load the review queue');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load, retryCount]);

  if (loading) return <LoadingState label="Loading review queue…" />;
  if (error) return <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  const isApprover = APPROVER_ROLES.includes(role);

  const columns = [
    {
      key: 'file_name',
      header: 'Item',
      accessor: 'file_name',
      render: (row) => <strong>{row.file_name || 'Unnamed item'}</strong>,
      isHeader: true,
    },
    { key: 'status', header: 'Status', accessor: 'status', render: (row) => <StatusBadge status={row.status} /> },
    {
      key: 'calculated',
      header: 'Calculated (kg CO₂e)',
      accessor: 'calculated_emissions_kg_co2e',
      render: (row) => row.calculated_emissions_kg_co2e ?? '—',
    },
    {
      key: 'reviewed',
      header: 'Reviewed',
      accessor: 'customer_reviewed_at',
      render: (row) => (row.customer_reviewed_at ? new Date(row.customer_reviewed_at).toLocaleDateString() : 'Not yet'),
    },
  ];

  return (
    <div className="v3-page">
      <header className="v3-page-header">
        <h1>Review &amp; approve</h1>
        <p className="v3-subtitle">
          {org ? `${org.name} · ` : ''}Items awaiting customer verification. Review shows the full evidence chain;
          approval is the distinct final gate (D5).
        </p>
      </header>

      {!isApprover && items.length > 0 && (
        <div className="ct-alert ct-alert--info" role="status">
          <div>You can review these items and their evidence. Approving or rejecting is reserved for an organisation
            owner or administrator.</div>
        </div>
      )}

      {items.length === 0 ? (
        <EmptyState icon="checkCircle" title="Nothing awaiting review">
          No items are currently waiting for customer review. New items appear here once calculation and evidence are
          complete.
        </EmptyState>
      ) : (
        <DataTable
          caption="Items awaiting customer review"
          columns={columns}
          rows={items}
          onRowClick={(row) => navigate(`/review/${row.id}`)}
        />
      )}

      <div style={{ marginTop: 20 }}>
        <Button variant="secondary" icon="arrowLeft" onClick={() => navigate('/processing')}>
          Back to processing
        </Button>
      </div>
    </div>
  );
}
