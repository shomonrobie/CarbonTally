// frontend/src/v3/ops/QcItemPage.jsx
// CL-59 — dedicated routed workspace for QC items. List page (/ops → QC)
// opens /ops/qc/:itemId; Back to queue returns with the queue tab restored.
// Deep-linkable, refresh-safe, history-aware.
import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { qcReviewItem } from '../api';
import WorkItemWorkspace from './WorkItemWorkspace';
import { Button } from '../components/ui';

export default function QcItemPage() {
  const { itemId } = useParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [score, setScore] = useState(80);
  const [notes, setNotes] = useState('');

  const onQc = async (approved) => {
    try {
      await qcReviewItem(itemId, { quality_score: Number(score), approved, qc_notes: notes });
      setNotice(approved ? 'QC passed.' : 'QC rejected — item returned for correction.');
      navigate('/ops?tab=qc');
    } catch (e) { setError(e.message); }
  };

  return (
    <div className="v3-ops-page">
      <div className="v3-ops-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h1>QC item workspace</h1>
          <div className="subtitle">{itemId}</div>
        </div>
        <Button variant="secondary" size="sm" onClick={() => navigate('/ops?tab=qc')}>
          ← Back to QC queue
        </Button>
      </div>
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      <WorkItemWorkspace
        itemId={itemId}
        renderActions={() => (
          <div>
            <div className="workspace-grid">
              <div className="workspace-field">
                <label>Quality score (0–100)</label>
                <input type="number" min={0} max={100} value={score} onChange={(e) => setScore(e.target.value)} />
              </div>
              <div className="workspace-field">
                <label>QC notes</label>
                <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
              </div>
            </div>
            <div className="workspace-actions">
              <button className="v3-btn primary" onClick={() => onQc(true)}>Pass QC</button>
              <button className="v3-btn" onClick={() => onQc(false)}>Reject QC</button>
            </div>
          </div>
        )}
      />
    </div>
  );
}
