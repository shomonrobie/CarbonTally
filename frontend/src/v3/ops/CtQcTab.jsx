// frontend/src/v3/ops/CtQcTab.jsx
// V1.2 — CarbonTally QC queue + decision workspace (internal /ops tab).
//
// Accepts work from BOTH origins:
//   CARBONTALLY_INTERNAL (status `reviewed`) and
//   PROCESSING_ENTITY    (status `pe_qc_approved`).
// Displays processing origin, the originating Processing Entity where
// applicable, current workflow state and QC decision controls. The tab is
// only shown to staff whose profile carries `can_qc` (migration grants it to
// internal qc_specialist + admin); every control still calls the backend
// /api/v3/ops/qc/* endpoints where require_internal_staff + can_qc remain the
// authoritative gate. Processing Entity users never see this surface.
import React, { useCallback, useEffect, useState } from 'react';
import {
  ctQcDecision,
  getCtQcQueue,
} from '../api';
import {
  Alert,
  Button,
  LoadingState,
  TextArea,
  TextInput,
} from '../components/ui';
import DataTable from '../components/ui/DataTable';
import './ops.css';
import './v12.css';

const ORIGIN_LABEL = (origin) =>
  origin === 'PROCESSING_ENTITY' ? 'Processing Entity' : 'CarbonTally internal';

export default function CtQcTab() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [score, setScore] = useState('90');
  const [notes, setNotes] = useState('');
  const [acting, setActing] = useState(false);
  const [actionError, setActionError] = useState('');
  const [notice, setNotice] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const body = await getCtQcQueue();
      setItems(body.items || []);
      setTotal(body.total || 0);
      setSelected(null);
    } catch (e) {
      setError(e.message || 'Failed to load the CarbonTally QC queue.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  const decide = async (approved) => {
    if (!selected) return;
    const qualityScore = parseInt(score, 10);
    if (Number.isNaN(qualityScore) || qualityScore < 0 || qualityScore > 100) {
      setActionError('Quality score must be between 0 and 100.');
      return;
    }
    setActing(true);
    setActionError('');
    setNotice('');
    try {
      await ctQcDecision(selected.id, {
        approved: !!approved,
        quality_score: qualityScore,
        qc_notes: notes.trim() || null,
      });
      setNotice(approved ? 'Approved — item passed CarbonTally QC.' : 'Rejected — item returned for rework.');
      setRefreshKey((k) => k + 1);
    } catch (e) {
      setActionError(e.message || 'Decision could not be applied.');
    } finally {
      setActing(false);
    }
  };

  if (loading) return <LoadingState label="Loading CarbonTally QC queue…" />;

  const columns = [
    {
      key: 'status',
      header: 'State',
      accessor: 'status',
      sortable: true,
      render: (row) => (
        <span className="v12-stage active">{row.status || '—'}</span>
      ),
    },
    {
      key: 'origin',
      header: 'Processing origin',
      accessor: 'processing_origin',
      sortable: true,
      render: (row) => (
        <span className={`v12-origin-chip ${row.processing_origin === 'PROCESSING_ENTITY' ? 'pe' : 'internal'}`}>
          {ORIGIN_LABEL(row.processing_origin)}
        </span>
      ),
    },
    {
      key: 'pe',
      header: 'Originating PE',
      accessor: 'processing_entity_name',
      render: (row) => row.processing_entity_name || '—',
    },
    {
      key: 'file_name',
      header: 'File',
      accessor: 'file_name',
      render: (row) => (row.file_name || '—').slice(0, 60),
    },
    {
      key: 'actions',
      header: '',
      accessor: 'id',
      render: (row) => (
        <Button variant="secondary" size="sm" onClick={() => { setSelected(row); setActionError(''); setNotice(''); }}>
          Open QC workspace
        </Button>
      ),
    },
  ];

  const stageRail = selected
    ? (selected.processing_origin === 'PROCESSING_ENTITY'
      ? ['calculated', 'pe_review', 'pe_qc', 'ct_qc']
      : ['calculated', 'reviewed', 'ct_qc'])
    : [];

  return (
    <div>
      <div className="v12-panel">
        <h3 style={{ marginTop: 0 }}>CarbonTally QC — late gate for both origins</h3>
        <p className="v12-muted" style={{ marginTop: 4 }}>
          Internal items arrive here <strong>reviewed</strong> (submitted by an internal reviewer).
          Processing Entity items arrive here <strong>pe_qc_approved</strong> (after PE Review + PE QC).
          Approval releases the item for customer review; rejection returns it for rework.
          This surface is internal CarbonTally only — Processing Entity users never see it.
        </p>
        {error && <Alert tone="error" title="Failed to load">{error}</Alert>}
        {notice && <Alert tone="success" title="Decision recorded">{notice}</Alert>}
      </div>
      {items.length === 0 ? (
        <Alert tone="info" title="Nothing awaiting CarbonTally QC">
          No internal-reviewed or PE-QC-approved items are waiting right now.
        </Alert>
      ) : (
        <DataTable
          caption={`CarbonTally QC queue — ${total} item${total === 1 ? '' : 's'} (internal + Processing Entity origins)`}
          columns={columns}
          rows={items}
          rowKey="id"
        />
      )}

      {selected && (
        <div className="v12-panel" data-testid="ctqc-workspace">
          <h3 style={{ marginTop: 0 }}>CarbonTally QC workspace</h3>
          <div className="v12-grid">
            <div>
              <div className="v12-label">File</div>
              <div className="v12-value">{selected.file_name || '—'}</div>
            </div>
            <div>
              <div className="v12-label">Processing origin</div>
              <div>
                <span className={`v12-origin-chip ${selected.processing_origin === 'PROCESSING_ENTITY' ? 'pe' : 'internal'}`}>
                  {ORIGIN_LABEL(selected.processing_origin)}
                </span>
              </div>
            </div>
            <div>
              <div className="v12-label">Originating PE</div>
              <div className="v12-value">{selected.processing_entity_name || '— (internal)'}</div>
            </div>
            <div>
              <div className="v12-label">Current state</div>
              <div><span className="v12-stage active">{selected.status}</span></div>
            </div>
          </div>

          <div className="v12-label" style={{ marginTop: 8 }}>Approach to this point</div>
          <div className="v12-stage-rail">
            {stageRail.map((s, i) => (
              <React.Fragment key={s}>
                {i > 0 && <span className="v12-stage-arrow">→</span>}
                <span className={`v12-stage ${s === selected.status ? 'active' : ''}`}>{s}</span>
              </React.Fragment>
            ))}
            <span className="v12-stage-arrow">→</span>
            <span className="v12-stage stop">customer review (CarbonTally released)</span>
          </div>

          <div className="v12-grid" style={{ marginTop: 12 }}>
            <TextInput
              label="Quality score (0–100)"
              type="number"
              min={0}
              max={100}
              value={score}
              onChange={(e) => setScore(e.target.value)}
            />
          </div>
          <div style={{ marginTop: 8 }}>
            <TextArea
              label="QC notes (optional)"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Findings, corrections, decision rationale…"
            />
          </div>
          {actionError && <Alert tone="error" title="Decision not applied">{actionError}</Alert>}
          <div className="v12-actions" style={{ marginTop: 12 }}>
            <Button variant="primary" disabled={acting} onClick={() => decide(true)}>
              Approve for customer review
            </Button>
            <Button variant="danger" disabled={acting} onClick={() => decide(false)}>
              Reject (return for rework)
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
