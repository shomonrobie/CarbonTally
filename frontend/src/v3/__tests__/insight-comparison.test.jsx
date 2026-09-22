// frontend/src/v3/__tests__/insight-comparison.test.jsx
// P2 — the temporal-comparison detail must present the *deterministic* result.
//
// The load-bearing assertions:
//
//   * both periods, the absolute change and the percentage come from the tool
//     output (the UI computes nothing);
//   * a zero baseline is shown as "not computable" and NO percentage appears —
//     the UI must never invent one;
//   * a non-success tool status is shown as-is (no uplifting into a figure).
import React from 'react';
import { render, screen, cleanup, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../api', () => ({
  invokeInsightTool: jest.fn(),
}));

import { invokeInsightTool } from '../api';
import InsightComparison from '../insight/InsightComparison';

afterEach(() => {
  cleanup();
  jest.clearAllMocks();
});

const ARGS = {
  period_a_start: '2026-01-01',
  period_a_end: '2026-01-31',
  period_b_start: '2025-01-01',
  period_b_end: '2025-01-31',
};

function toolResult(overrides = {}) {
  return {
    tool: 'insight_temporal_comparison',
    status: 'success',
    reason: null,
    contract_version: 'i3-6point-v1',
    references: [],
    truncated: false,
    data: {
      group_by: null,
      period_a: {
        start_date: '2026-01-01',
        end_date: '2026-01-31',
        total_co2e_kg: '100',
        row_count: 4,
      },
      period_b: {
        start_date: '2025-01-01',
        end_date: '2025-01-31',
        total_co2e_kg: '150',
        row_count: 6,
      },
      absolute_change_kg: '50',
      percentage_change: '50.000000',
      percentage_change_available: true,
      percentage_basis: 'period_a_total',
      direction: 'increase',
      groups: [],
      group_count: 0,
      groups_truncated: false,
      empty_periods: [],
      comparison_dimensions: ['scope', 'activity', 'facility', 'asset'],
      basis: 'kg CO2e from emissions_logs.calculated_kg_co2e (organization-scoped)',
      provenance_tool: 'insight_aggregate_provenance',
      ...overrides,
    },
  };
}

async function renderComparison(result) {
  invokeInsightTool.mockResolvedValue(result);
  render(<InsightComparison organizationId="org-1" toolArguments={ARGS} />);
  await waitFor(() => expect(invokeInsightTool).toHaveBeenCalled());
}

test('renders both periods, the absolute change and the percentage from the tool', async () => {
  await renderComparison(toolResult());
  expect(await screen.findByText(/Period A \(baseline\)/)).toBeInTheDocument();
  expect(screen.getByText(/Period B/)).toBeInTheDocument();
  expect(screen.getByText(/Increase:/)).toBeInTheDocument();
  expect(screen.getAllByText(/50 kg CO₂e/).length).toBeGreaterThan(0);
  expect(screen.getByText(/\+50%/)).toBeInTheDocument();
  // The read uses the persisted bounded arguments and the authorized tool only.
  expect(invokeInsightTool).toHaveBeenCalledWith(
    'org-1',
    'insight_temporal_comparison',
    ARGS,
  );
});

test('a zero baseline is shown as not computable and no percentage is invented', async () => {
  await renderComparison(
    toolResult({
      period_a: {
        start_date: '2026-01-01',
        end_date: '2026-01-31',
        total_co2e_kg: '0',
        row_count: 0,
      },
      absolute_change_kg: '150',
      percentage_change: null,
      percentage_change_available: false,
      percentage_basis: 'zero_baseline',
      empty_periods: ['period_a'],
    }),
  );
  expect(
    await screen.findByText(/Percentage change is not computable/i),
  ).toBeInTheDocument();
  // The absolute difference is still shown…
  expect(screen.getAllByText(/150 kg CO₂e/).length).toBeGreaterThan(0);
  // …and no percentage is rendered anywhere.
  expect(screen.queryByText(/%/)).not.toBeInTheDocument();
});

test('grouped rows show a per-group percentage only when one was computed', async () => {
  await renderComparison(
    toolResult({
      group_by: 'scope',
      group_count: 2,
      groups: [
        {
          key: 'Scope 1',
          label: null,
          period_a_co2e_kg: '40',
          period_b_co2e_kg: '90',
          period_a_row_count: 2,
          period_b_row_count: 2,
          absolute_change_kg: '50',
          percentage_change: '125.000000',
          percentage_change_available: true,
          percentage_basis: 'period_a_total',
          direction: 'increase',
        },
        {
          key: 'Scope 2',
          label: null,
          period_a_co2e_kg: '0',
          period_b_co2e_kg: '60',
          period_a_row_count: 0,
          period_b_row_count: 1,
          absolute_change_kg: '60',
          percentage_change: null,
          percentage_change_available: false,
          percentage_basis: 'zero_baseline',
          direction: 'increase',
        },
      ],
    }),
  );
  expect(await screen.findByText(/By scope/)).toBeInTheDocument();
  expect(screen.getByText(/\+125%/)).toBeInTheDocument();
  expect(screen.getByText(/not computable/)).toBeInTheDocument();
});

test('a non-success tool status is presented truthfully, never as a figure', async () => {
  await renderComparison({
    tool: 'insight_temporal_comparison',
    status: 'no_data',
    reason: 'no_rows_in_periods',
    data: {},
    references: [],
  });
  expect(await screen.findByText(/No comparison figures available/i)).toBeInTheDocument();
  expect(screen.getByText(/no_rows_in_periods/)).toBeInTheDocument();
  expect(screen.queryByText(/kg CO₂e/)).not.toBeInTheDocument();
});
