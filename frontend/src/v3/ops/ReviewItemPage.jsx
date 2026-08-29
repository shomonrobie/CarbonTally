// frontend/src/v3/ops/ReviewItemPage.jsx
// CL-59 — dedicated routed workspace for reviewer items. List page (/ops →
// Review) opens /ops/review/:itemId; Back to queue returns with the queue tab
// restored. Deep-linkable, refresh-safe, history-aware.
import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { assignReview, completeReview, validateItem } from '../api';
import WorkItemWorkspace from './WorkItemWorkspace';
import { Button } from '../components/ui';

export default function ReviewItemPage() {
  const { itemId } = useParams();
  const navigate = useNavigate();
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  const onValidate = async () => {
    try {
      const result = await validateItem(itemId);
      setNotice(result.blocking ? 'Blocking findings — routed back to mapping.' : 'Validated.');
      setRefreshKey((k) => k + 1);
    } catch (e) { setError(e.message); }
  };

  const onAssign = async () => {
    try {
      await assignReview(itemId, ''); // assigned_to resolved server-side for internal reviewers
      setNotice('Review assigned.');
      setRefreshKey((k) => k + 1);
    } catch (e) { setError(e.message); }
  };

  const onComplete = async () => {
    try {
      await completeReview(itemId, { manual_extraction_result: { reviewed: true }, review_time_seconds: 60 });
      setNotice('Review completed.');
      // Completed items leave the reviewer queue — return to the queue.
      navigate('/ops?tab=review');
    } catch (e) { setError(e.message); }
  };

  return (
    <div className="v3-ops-page">
      <div className="v3-ops-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h1>Review item workspace</h1>
          <div className="subtitle">{itemId}</div>
        </div>
        <Button variant="secondary" size="sm" onClick={() => navigate('/ops?tab=review')}>
          ← Back to review queue
        </Button>
      </div>
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      <WorkItemWorkspace
        key={refreshKey}
        itemId={itemId}
        renderActions={({ item }) => (
          <div className="workspace-actions">
            <button className="v3-btn primary" onClick={onValidate} disabled={item.status !== 'mapped' && item.status !== 'validated'}>
              Validate
            </button>
            <button className="v3-btn" onClick={onAssign}>Assign to me</button>
            <button className="v3-btn primary" onClick={onComplete}>Complete review</button>
          </div>
        )}
      />
    </div>
  );
}
