// frontend/src/v3/ops/OperationalHealthTab.jsx
//
// Phase 8-X X5 — operations console extension (read-only).
//
// Authority: the 8-X discovery document's Stage X5 ("surface X2–X4 in the existing
// ops console as tabs/cards; frontend/src/v3/ops/** extension only; no new dashboard
// shell") plus the already PO-closed X1/X2/X4 deliverables. See
// CARBONTALLY_PHASE8X_X5_OPS_CONSOLE_CONTRACT_20260915.md.
//
// Scope discipline enforced in this file:
//   * it displays the existing internal payloads VERBATIM — no derived metric, no
//     percentage, no rate, no trend, no threshold invented here;
//   * the ONLY interactive control is a manual refresh (re-fetch of the same GETs);
//   * there is no filter, no sorting, no drill-down, no acknowledgement and no
//     mutation — none of those are authorised;
//   * authorization stays server-side (require_staff → require_internal_staff →
//     can_view_all); this component is not a security boundary.
import React, { useCallback, useEffect, useState } from 'react';
import {
  getOperationalHealthQueue,
  getOperationalHealthWorker,
  getOperationalIntelligence,
} from '../api';

const WORKER_STATE_LABELS = {
  HEALTHY: 'Reporting',
  STALE: 'Not reporting (stale)',
  UNKNOWN: 'No heartbeat recorded',
};

const SLA_STATE_LABELS = {
  configured: 'Configured',
  not_configured: 'Not configured',
  unknown: 'Unknown',
};

const formatAge = (seconds) => {
  if (seconds === null || seconds === undefined) return '—';
  const s = Number(seconds);
  if (!Number.isFinite(s)) return '—';
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
};

const formatStamp = (iso) => {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? String(iso) : d.toLocaleString();
};

function Figure({ label, value, hint }) {
  return (
    <div className="ops-figure" data-testid={`figure-${label}`}>
      <div className="k">{label}</div>
      <div className="v">{value === null || value === undefined ? '—' : value}</div>
      {hint ? <div className="hint">{hint}</div> : null}
    </div>
  );
}

export default function OperationalHealthTab() {
  const [queue, setQueue] = useState(null);
  const [worker, setWorker] = useState(null);
  const [intel, setIntel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [queueResult, workerResult, intelResult] = await Promise.all([
        getOperationalHealthQueue(),
        getOperationalHealthWorker(),
        getOperationalIntelligence(),
      ]);
      setQueue(queueResult);
      setWorker(workerResult);
      setIntel(intelResult);
    } catch (e) {
      // Never surface raw technical text to an operator.
      const status = e && e.status;
      if (status === 403) {
        setError('You do not have access to operational health information.');
      } else {
        setError(
          (e && e.message) || 'Unable to load operational health. Please try again.'
        );
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading && !intel) {
    return (
      <div className="v3-loading" role="status">
        <div className="spinner" />
        Loading operational health…
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="v3-ops-error" role="alert" data-testid="operational-health-error">
          {error}
        </div>
        <button type="button" className="v3-btn" onClick={load}>
          Try again
        </button>
      </div>
    );
  }

  if (!intel) return null;

  const liveness = intel.worker_liveness || {};
  const slaConfigured = intel.sla_state === 'configured';

  return (
    <div data-testid="operational-health-tab">
      <div className="ops-tab-head">
        <div>
          <h3>Operational health</h3>
          <p className="ops-muted">
            Read-only operational view. Figures come from the existing processing queue,
            the persisted SLA flag and the worker heartbeat — nothing is estimated here.
          </p>
        </div>
        <button type="button" className="v3-btn" onClick={load} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {intel.truncated ? (
        <div className="v3-ops-notice" role="status" data-testid="truncated-notice">
          Showing a partial population: the read reached its {intel.read_limit}-row limit,
          so these counts are a floor, not a total.
        </div>
      ) : null}

      <section className="workspace-pane" style={{ marginBottom: 16 }}>
        <h4>What is failing</h4>
        <div className="ops-figures">
          <Figure label="Failed jobs" value={intel.failed_jobs} />
          <Figure label="Retry exhausted" value={intel.retry_exhausted_jobs} />
          <Figure label="Stuck claims" value={intel.stuck_locked_jobs} />
          <Figure label="Blocked" value={intel.blocked_jobs} hint="awaiting a human" />
          <Figure label="Manual review" value={intel.manual_review_jobs} hint="awaiting a human" />
          <Figure
            label="Open / closed"
            value={`${intel.open_vs_closed?.open ?? '—'} / ${intel.open_vs_closed?.closed ?? '—'}`}
          />
          <Figure
            label="Rows examined"
            value={intel.rows_examined}
            hint={`read limit ${intel.read_limit}`}
          />
          <Figure
            label="Oldest waiting"
            value={formatAge(queue && queue.oldest_waiting_age_seconds)}
          />
        </div>

        {intel.error_rate_by_stage && Object.keys(intel.error_rate_by_stage).length > 0 ? (
          <div className="ops-table-wrap" style={{ marginTop: 12 }}>
            <table className="ops-table">
              <caption>Jobs with recorded workflow errors, by stage (counts, not rates)</caption>
              <thead>
                <tr>
                  <th scope="col">Stage</th>
                  <th scope="col">Jobs with errors</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(intel.error_rate_by_stage).map(([stage, count]) => (
                  <tr key={stage}>
                    <td>{stage}</td>
                    <td>{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="ops-muted" data-testid="no-stage-errors">
            No jobs with recorded workflow errors.
          </p>
        )}
      </section>

      <section className="workspace-pane" style={{ marginBottom: 16 }}>
        <h4>What is breaching SLA</h4>
        <div className="ops-figures">
          <Figure
            label="SLA state"
            value={SLA_STATE_LABELS[intel.sla_state] || intel.sla_state}
          />
          <Figure label="SLA hours" value={slaConfigured ? intel.sla_hours : null} />
          <Figure
            label="Breached items"
            value={slaConfigured ? intel.sla_breached_items : null}
          />
        </div>
        {!slaConfigured ? (
          <p className="ops-muted" data-testid="sla-not-configured">
            The SLA setting is not configured, so no breach position can be reported. A breach
            is never inferred from a missing configuration.
          </p>
        ) : null}
      </section>

      <section className="workspace-pane" style={{ marginBottom: 16 }}>
        <h4>Processing worker</h4>
        <div className="ops-figures">
          <Figure
            label="Worker"
            value={WORKER_STATE_LABELS[liveness.state] || liveness.state || '—'}
          />
          <Figure label="Last heartbeat" value={formatAge(liveness.age_seconds)} hint="age" />
        </div>
        {liveness.state === 'UNKNOWN' ? (
          <p className="ops-muted" data-testid="worker-unknown">
            No heartbeat has ever been recorded, so worker health is unknown — this is not
            reported as healthy.
          </p>
        ) : null}
        {liveness.state === 'STALE' ? (
          <p className="ops-muted" data-testid="worker-stale">
            The worker has not reported recently; the failure figures above may not be
            current.
          </p>
        ) : null}
      </section>

      <section className="workspace-pane">
        <h4>Queue depth by stage</h4>
        {intel.queue_depth_by_stage &&
        Object.keys(intel.queue_depth_by_stage).length > 0 ? (
          <div className="ops-table-wrap">
            <table className="ops-table">
              <caption>Jobs by persisted processing stage</caption>
              <thead>
                <tr>
                  <th scope="col">Stage</th>
                  <th scope="col">Jobs</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(intel.queue_depth_by_stage).map(([stage, count]) => (
                  <tr key={stage}>
                    <td>{stage}</td>
                    <td>{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="ops-muted" data-testid="empty-queue">
            No processing jobs to report.
          </p>
        )}
        <p className="ops-muted" data-testid="evaluated-at">
          Evaluated {formatStamp(intel.evaluated_at)}
          {worker && worker.generated_at
            ? ` · worker reading taken ${formatStamp(worker.generated_at)}`
            : ''}
        </p>
      </section>
    </div>
  );
}


