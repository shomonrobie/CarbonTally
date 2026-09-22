// frontend/src/v3/insight/InsightComparison.jsx
// CarbonTally Insight P2 — the deterministic temporal-comparison detail.
//
// The I4 interaction record deliberately persists *metadata only* (PO Q6), so the
// comparison figures are not stored with the answer. They are re-read on demand
// through the already-authorized I3 tool surface using the bounded arguments the
// interaction did persist (four period bounds and an optional dimension), which
// means:
//
//   * no new API route, no new evidence route and no new persistence;
//   * the read is the same deterministic, organisation-scoped, rate-limited
//     execution path as any other Insight tool call;
//   * the figures shown are the tool's output — the UI never computes a
//     percentage, never invents a missing value and never decides validity.
//
// A zero baseline is presented as "not computable" because that is exactly what
// the deterministic result says; no percentage is displayed in that case.
import React, { useCallback, useEffect, useState } from 'react';
import Alert from '../components/ui/Alert';
import Button from '../components/ui/Button';
import { LoadingState } from '../components/ui/StateViews';
import { invokeInsightTool } from '../api';
import './insight.css';

const DIRECTION_LABEL = {
  increase: 'Increase',
  decrease: 'Decrease',
  no_change: 'No change',
};

/** kg CO₂e for display: the deterministic string, grouped for readability. */
function kg(value) {
  if (value === null || value === undefined || value === '') return '—';
  const number = Number(value);
  if (Number.isNaN(number)) return String(value);
  return `${number.toLocaleString(undefined, { maximumFractionDigits: 6 })} kg CO₂e`;
}

/** The deterministic percentage, or `null` when none was computed. */
function percent(value) {
  if (value === null || value === undefined || value === '') return null;
  const number = Number(value);
  if (Number.isNaN(number)) return null;
  const sign = number > 0 ? '+' : '';
  return `${sign}${number.toLocaleString(undefined, { maximumFractionDigits: 6 })}%`;
}

function periodLabel(period) {
  if (!period) return '—';
  return period.start_date === period.end_date
    ? period.start_date
    : `${period.start_date} → ${period.end_date}`;
}

export default function InsightComparison({ organizationId, toolArguments }) {
  const [state, setState] = useState({ loading: true, error: null, result: null });
  const [attempt, setAttempt] = useState(0);

  const load = useCallback(() => setAttempt((value) => value + 1), []);

  useEffect(() => {
    let cancelled = false;
    setState({ loading: true, error: null, result: null });
    invokeInsightTool(organizationId, 'insight_temporal_comparison', toolArguments || {})
      .then((result) => {
        if (!cancelled) setState({ loading: false, error: null, result });
      })
      .catch((error) => {
        if (!cancelled) setState({ loading: false, error, result: null });
      });
    return () => {
      cancelled = true;
    };
  }, [organizationId, toolArguments, attempt]);

  if (state.loading) {
    return <LoadingState label="Loading the comparison…" inline />;
  }

  if (state.error) {
    return (
      <Alert tone="error" title="Unable to load the comparison.">
        <p>The deterministic comparison could not be read. Please try again.</p>
        <Button size="sm" icon="refresh" onClick={load}>
          Try again
        </Button>
      </Alert>
    );
  }

  const result = state.result || {};
  const data = result.data || {};

  if (result.status !== 'success') {
    // The tool's own status is shown; the UI does not reinterpret it.
    return (
      <p className="v3-muted">
        No comparison figures available ({result.status || 'unknown'}
        {result.reason ? `: ${result.reason}` : ''}).
      </p>
    );
  }

  const percentage = percent(data.percentage_change);
  const emptyPeriods = data.empty_periods || [];

  return (
    <div className="ct-insight-comparison">
      <dl className="ct-insight-comparison__periods">
        <div>
          <dt>Period A (baseline)</dt>
          <dd>
            {periodLabel(data.period_a)}
            <span className="v3-muted">
              {' '}
              · {kg(data.period_a && data.period_a.total_co2e_kg)}
              {data.period_a && data.period_a.row_count === 0 ? ' · no records' : ''}
            </span>
          </dd>
        </div>
        <div>
          <dt>Period B</dt>
          <dd>
            {periodLabel(data.period_b)}
            <span className="v3-muted">
              {' '}
              · {kg(data.period_b && data.period_b.total_co2e_kg)}
              {data.period_b && data.period_b.row_count === 0 ? ' · no records' : ''}
            </span>
          </dd>
        </div>
      </dl>

      <p className="ct-insight-comparison__delta">
        <strong>{DIRECTION_LABEL[data.direction] || 'Change'}:</strong>{' '}
        {kg(data.absolute_change_kg)}
        {percentage ? <span> ({percentage})</span> : null}
      </p>

      {!data.percentage_change_available ? (
        <p className="v3-muted">
          Percentage change is not computable because the comparison baseline
          (Period A) is zero. The absolute difference above is authoritative.
        </p>
      ) : null}

      {emptyPeriods.length > 0 ? (
        <p className="v3-muted">
          {emptyPeriods.length === 2
            ? 'Neither period contains authoritative records.'
            : `No authoritative records fall in ${
                emptyPeriods[0] === 'period_a' ? 'Period A' : 'Period B'
              }, so that side is reported as zero.`}
        </p>
      ) : null}

      {data.group_count > 0 ? (
        <div className="ct-insight-comparison__groups">
          <h5 className="ct-insight-comparison__subhead">
            By {data.group_by} · {data.group_count} group
            {data.group_count === 1 ? '' : 's'}
          </h5>
          <table className="ct-table ct-insight-comparison__table">
            <thead>
              <tr>
                <th scope="col">{data.group_by}</th>
                <th scope="col">Period A</th>
                <th scope="col">Period B</th>
                <th scope="col">Change</th>
                <th scope="col">%</th>
              </tr>
            </thead>
            <tbody>
              {(data.groups || []).map((group) => {
                const groupPercentage = percent(group.percentage_change);
                return (
                  <tr key={group.key}>
                    <td>{group.label || group.key}</td>
                    <td>{kg(group.period_a_co2e_kg)}</td>
                    <td>{kg(group.period_b_co2e_kg)}</td>
                    <td>{kg(group.absolute_change_kg)}</td>
                    <td>
                      {groupPercentage || (
                        <span className="v3-muted" title={group.percentage_basis}>
                          not computable
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {data.groups_truncated ? (
            <p className="v3-muted">
              More groups exist than the bounded result shows; the period totals
              above remain complete.
            </p>
          ) : null}
        </div>
      ) : null}

      <p className="v3-muted ct-insight-comparison__basis">
        Basis: {data.basis}
        {data.provenance_tool ? (
          <>
            {' '}
            · contributing calculations are available through{' '}
            <code>{data.provenance_tool}</code> for these exact periods.
          </>
        ) : null}
      </p>
    </div>
  );
}
