// frontend/src/v3/consultant/ManualProcessingCoverageTab.jsx
// CT-MP-SUB-004 — Consultant Manual Processing coverage (CT-UX-MP-SUB-003 §4, §7).
//
// The consultant sees what THEIR OWN FIRM purchased, how much selected capacity
// remains, and which of their eligible clients are covered. The firm identity is
// resolved server-side from the authenticated consultant context
// (GET /api/v3/consultants/me/manual-processing/coverage) — a consultant can
// never read or change another firm's coverage, and this component never sends a
// firm id.
//
// No commercial rule is invented here: pricing, plan names and capacity tiers are
// deliberately unresolved (§9), so the UI only displays configured values. Every
// capacity/eligibility decision is re-checked server-side before a write.
import React, { useCallback, useEffect, useState } from 'react';
import {
  allocateConsultantManualProcessingClient,
  getConsultantManualProcessingCoverage,
  releaseConsultantManualProcessingAllocation,
} from '../api';
import Badge from '../components/ui/Badge';
import Alert from '../components/ui/Alert';
import { Card } from '../components/ui/Card';
import { EmptyState, LoadingState } from '../components/ui/StateViews';
import './consultant.css';

const MODE_LABEL = {
  SELECTED_CLIENTS: 'SELECTED CLIENTS',
  ALL_ELIGIBLE_CLIENTS: 'ALL ELIGIBLE CLIENTS',
};

const modeLabel = (mode) => MODE_LABEL[mode] || mode || '—';

// §7 — consultant empty state.
const NO_COVERAGE_COPY = (
  <>
    <p style={{ margin: 0 }}>
      No Manual Processing consultant coverage is currently active.
    </p>
    <p style={{ margin: '6px 0 0' }}>
      Your firm&apos;s subscription coverage will appear here when configured.
    </p>
  </>
);

// §7 — allocation error copy (never reveals whether another organisation exists).
const ALLOCATION_ERROR_COPY = (
  <>
    <p style={{ margin: 0 }}>Unable to allocate this client.</p>
    <p style={{ margin: '6px 0 0' }}>Possible reasons:</p>
    <ul style={{ margin: '4px 0 0 18px' }}>
      <li>the client is not eligible;</li>
      <li>allocation capacity is exhausted;</li>
      <li>coverage is no longer active.</li>
    </ul>
    <p style={{ margin: '6px 0 0' }}>Refresh the coverage state and try again.</p>
  </>
);

function Meter({ allocated, capacity }) {
  if (!capacity) return null;
  const pct = Math.min(100, Math.round((allocated / capacity) * 100));
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
      <div
        role="progressbar"
        aria-valuenow={allocated}
        aria-valuemin={0}
        aria-valuemax={capacity}
        aria-label="Selected-client capacity used"
        style={{
          flex: '0 0 200px',
          height: 10,
          borderRadius: 999,
          background: 'var(--ct-color-border)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            background: pct >= 100 ? '#c53030' : 'var(--ct-color-primary)',
          }}
        />
      </div>
      <span className="v3-muted">{pct}%</span>
    </div>
  );
}


export default function ManualProcessingCoverageTab({ canManageClients = false }) {
  const [coverage, setCoverage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [errorKind, setErrorKind] = useState('load');
  const [notice, setNotice] = useState('');
  const [target, setTarget] = useState('');
  const [showEligible, setShowEligible] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setErrorKind('load');
    try {
      const data = await getConsultantManualProcessingCoverage();
      setCoverage(data);
      setError('');
    } catch (e) {
      setCoverage(null);
      setError(e.message || 'Unable to load your Manual Processing coverage.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const allocate = async () => {
    if (!target) return;
    setBusy(true);
    setError('');
    setErrorKind('write');
    setNotice('');
    try {
      await allocateConsultantManualProcessingClient({ organization_id: target });
      setNotice('Client added to your Manual Processing coverage.');
      setTarget('');
      await load();
    } catch (e) {
      setError(e.message || 'Unable to allocate this client.');
    } finally {
      setBusy(false);
    }
  };

  const release = async (allocationId) => {
    setBusy(true);
    setError('');
    setErrorKind('write');
    setNotice('');
    try {
      await releaseConsultantManualProcessingAllocation(allocationId);
      setNotice('Allocation released — capacity is available again.');
      await load();
    } catch (e) {
      setError(e.message || 'Unable to release this allocation.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <LoadingState label="Loading Manual Processing coverage…" />;

  if (!coverage) {
    return (
      <Card title="Manual Processing Coverage">
        <EmptyState title="Coverage unavailable">{NO_COVERAGE_COPY}</EmptyState>
        {error && errorKind === 'load' && (
          <div className="v3-form-error" role="alert">{error}</div>
        )}
      </Card>
    );
  }

  const selected = coverage.mode === 'SELECTED_CLIENTS';
  const allocated = coverage.allocated || 0;
  const capacity = coverage.capacity;
  const available = coverage.available;
  const covered = (coverage.allocations || []).filter((a) => a.state === 'active');
  const eligible = coverage.eligible_clients || [];
  const unallocated = coverage.unallocated_eligible_clients || [];
  const exhausted = selected && available !== null && available !== undefined && available <= 0;

  const clientName = (entry) => entry.name || entry.organization_id;

  return (
    <div>
      {error && errorKind === 'write' && (
        <Alert tone="error" title="Allocation not completed">
          {ALLOCATION_ERROR_COPY}
        </Alert>
      )}
      {error && errorKind === 'load' && (
        <div className="v3-form-error" role="alert">{error}</div>
      )}
      {notice && <Alert tone="success" title="Done">{notice}</Alert>}

      <Card
        title="Manual Processing Coverage"
        actions={<Badge tone={selected ? 'info' : 'primary'}>{modeLabel(coverage.mode)}</Badge>}
      >
        {!coverage.enabled ? (
          <EmptyState title="No consultant coverage active">{NO_COVERAGE_COPY}</EmptyState>
        ) : (
          <>
            <table className="v3-table">
              <tbody>
                <tr>
                  <th scope="row">Coverage</th>
                  <td>{modeLabel(coverage.mode)}</td>
                </tr>
                <tr>
                  <th scope="row">Subscription status</th>
                  <td><Badge tone="success">ACTIVE</Badge></td>
                </tr>
                <tr>
                  <th scope="row">Clients covered</th>
                  <td>{covered.length}</td>
                </tr>
                {selected && (
                  <>
                    <tr>
                      <th scope="row">Purchased capacity</th>
                      <td>
                        {capacity === null || capacity === undefined
                          ? 'Not configured'
                          : `${capacity} clients`}
                      </td>
                    </tr>
                    <tr>
                      <th scope="row">Allocated</th>
                      <td>
                        {allocated} / {capacity === null || capacity === undefined ? '—' : capacity}
                      </td>
                    </tr>
                    <tr>
                      <th scope="row">Available</th>
                      <td>{available === null || available === undefined ? '—' : available}</td>
                    </tr>
                  </>
                )}
                {!selected && (
                  <>
                    <tr>
                      <th scope="row">Eligible clients</th>
                      <td>{eligible.length}</td>
                    </tr>
                    <tr>
                      <th scope="row">Covered automatically</th>
                      <td>{eligible.length}</td>
                    </tr>
                    <tr>
                      <th scope="row">Future eligible clients</th>
                      <td>Automatically covered</td>
                    </tr>
                    <tr>
                      <th scope="row">Eligibility source</th>
                      <td>Active consultant-client relationship</td>
                    </tr>
                  </>
                )}
              </tbody>
            </table>

            {selected && <Meter allocated={allocated} capacity={capacity} />}

            {selected && coverage.over_allocated && (
              <Alert tone="warning" title="Over-allocated">
                More clients hold an active allocation than the purchased capacity.
                Release an allocation or ask CarbonTally to increase capacity.
              </Alert>
            )}

            {selected && exhausted && (
              <Alert tone="warning" title="No allocation capacity remains">
                A newly eligible client cannot receive sponsored coverage until
                capacity is increased or an allocation is released.
              </Alert>
            )}
          </>
        )}
      </Card>

      {coverage.enabled && selected && (
        <Card title="Covered Clients">
          {covered.length === 0 ? (
            <EmptyState title="No clients covered yet">
              Add an eligible client to cover them under your selected-client
              capacity.
            </EmptyState>
          ) : (
            <div>
              <table className="v3-table">
                <thead>
                  <tr>
                    <th scope="col">Client</th>
                    <th scope="col">Coverage</th>
                    <th scope="col">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {covered.map((a) => (
                    <tr key={a.id}>
                      <td>{a.name || a.organization_id}</td>
                      <td><Badge tone="success">Active</Badge></td>
                      <td>
                        <button
                          type="button"
                          className="v3-btn v3-btn-sm danger"
                          disabled={!canManageClients || busy}
                          onClick={() => release(a.id)}
                        >
                          Release
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {coverage.enabled && selected && !exhausted && unallocated.length > 0 && (
        <Card title="Add Client">
          <p className="v3-muted">
            Only eligible consultant-client organisations may be selected. Capacity
            and eligibility are enforced server-side.
          </p>
          <div className="v3-form-group">
            <label htmlFor="mp-consultant-client">Eligible client</label>
            <select
              id="mp-consultant-client"
              value={target}
              disabled={!canManageClients || busy}
              onChange={(e) => setTarget(e.target.value)}
            >
              <option value="">Select an eligible client…</option>
              {unallocated.map((entry) => (
                <option key={entry.organization_id} value={entry.organization_id}>
                  {clientName(entry)}
                </option>
              ))}
            </select>
          </div>
          <div className="v3-actions">
            <button
              type="button"
              className="v3-btn v3-btn-primary"
              onClick={allocate}
              disabled={!canManageClients || busy || !target}
            >
              Allocate
            </button>
          </div>
          {!canManageClients && (
            <p className="v3-muted">
              Adding clients requires the &ldquo;manage clients&rdquo; permission on
              your firm membership; the server refuses it regardless of this control.
            </p>
          )}
        </Card>
      )}

      {coverage.enabled && !selected && (
        <Card
          title="Eligible Clients"
          actions={
            <button
              type="button"
              className="v3-btn v3-btn-sm"
              onClick={() => setShowEligible((v) => !v)}
            >
              {showEligible ? 'Hide' : 'View Eligible Clients'}
            </button>
          }
        >
          <p className="v3-muted">
            &ldquo;All&rdquo; means every currently and future eligible active
            consultant-client organisation of your firm — not every organisation in
            CarbonTally. No allocation is required and none is created.
          </p>
          {showEligible && (
            eligible.length === 0 ? (
              <EmptyState title="No eligible clients">
                Your firm has no active consultant-client relationships yet. Eligible
                clients are covered automatically once a relationship is active.
              </EmptyState>
            ) : (
              <ul>
                {eligible.map((entry) => (
                  <li key={entry.organization_id}>{clientName(entry)}</li>
                ))}
              </ul>
            )
          )}
        </Card>
      )}
    </div>
  );
}
