// frontend/src/v3/__tests__/operational-health-tab.test.jsx
//
// Phase 8-X X5 reference test for the read-only operational-health console tab:
//   * figures are displayed verbatim from the X1/X4 payloads (no derived metric);
//   * explicit truncation, SLA-not-configured and worker-UNKNOWN honesty states;
//   * a denied read shows a friendly message, never raw technical text;
//   * the panel offers NO operational control beyond Refresh — no mutation exists.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../api', () => ({
  getOpsMe: jest.fn(),
  getOperationalHealthQueue: jest.fn(),
  getOperationalHealthWorker: jest.fn(),
  getOperationalIntelligence: jest.fn(),
}));

import OperationalHealthTab from '../ops/OperationalHealthTab';
import * as api from '../api';

const intel = (over = {}) => ({
  scope: 'internal',
  x4_scope: 'failures_and_sla',
  failed_jobs: 2,
  retry_exhausted_jobs: 1,
  stuck_locked_jobs: 0,
  blocked_jobs: 3,
  manual_review_jobs: 4,
  error_rate_by_stage: { extracting: 1 },
  queue_depth_by_stage: { failed: 2, queued: 5 },
  open_vs_closed: { open: 5, closed: 2 },
  rows_examined: 7,
  read_limit: 2000,
  truncated: false,
  sla_configured: true,
  sla_hours: 48,
  sla_breached_items: 2,
  sla_state: 'configured',
  worker_liveness: { state: 'HEALTHY', age_seconds: 30, worker_id: 'w1' },
  evaluated_at: '2026-09-15T09:00:00Z',
  ...over,
});

const queue = {
  scope: 'internal',
  x1_scope: 'queue_visibility',
  oldest_waiting_age_seconds: 900,
};

beforeEach(() => {
  jest.clearAllMocks();
  api.getOperationalHealthQueue.mockResolvedValue(queue);
  api.getOperationalHealthWorker.mockResolvedValue({ generated_at: '2026-09-15T09:00:00Z' });
  api.getOperationalIntelligence.mockResolvedValue(intel());
});

it('displays the persisted figures verbatim', async () => {
  render(<OperationalHealthTab />);
  await waitFor(() => expect(screen.getByTestId('figure-Failed jobs')).toHaveTextContent('2'));
  expect(screen.getByTestId('figure-Retry exhausted')).toHaveTextContent('1');
  expect(screen.getByTestId('figure-Blocked')).toHaveTextContent('3');
  expect(screen.getByTestId('figure-Manual review')).toHaveTextContent('4');
  expect(screen.getByTestId('figure-SLA hours')).toHaveTextContent('48');
  expect(screen.getByTestId('figure-Breached items')).toHaveTextContent('2');
  // Counts, not rates: the stage table declares counts and shows no percentage.
  expect(
    screen.getByText('Jobs with recorded workflow errors, by stage (counts, not rates)')
  ).toBeInTheDocument();
  expect(screen.queryByText(/%/)).not.toBeInTheDocument();
});

it('shows the truncation notice when the read bound was reached', async () => {
  api.getOperationalIntelligence.mockResolvedValue(intel({ truncated: true }));
  render(<OperationalHealthTab />);
  await waitFor(() =>
    expect(screen.getByTestId('truncated-notice')).toHaveTextContent('2000-row limit')
  );
});

it('never reports a breach when the SLA setting is not configured', async () => {
  api.getOperationalIntelligence.mockResolvedValue(
    intel({
      sla_state: 'not_configured',
      sla_configured: false,
      sla_hours: null,
      sla_breached_items: null,
    })
  );
  render(<OperationalHealthTab />);
  await waitFor(() => expect(screen.getByTestId('sla-not-configured')).toBeInTheDocument());
  expect(screen.getByTestId('figure-SLA hours')).toHaveTextContent('—');
  expect(screen.getByTestId('figure-Breached items')).toHaveTextContent('—');
});

it('reports an unknown worker honestly rather than as healthy', async () => {
  api.getOperationalIntelligence.mockResolvedValue(
    intel({ worker_liveness: { state: 'UNKNOWN', age_seconds: null } })
  );
  render(<OperationalHealthTab />);
  await waitFor(() => expect(screen.getByTestId('worker-unknown')).toBeInTheDocument());
  expect(screen.getByTestId('figure-Worker')).toHaveTextContent('No heartbeat recorded');
});

it('warns that figures may not be current when the worker is stale', async () => {
  api.getOperationalIntelligence.mockResolvedValue(
    intel({ worker_liveness: { state: 'STALE', age_seconds: 1200 } })
  );
  render(<OperationalHealthTab />);
  await waitFor(() => expect(screen.getByTestId('worker-stale')).toBeInTheDocument());
});

it('shows a friendly message when the operator is not permitted (403)', async () => {
  const err = new Error('Forbidden: staff lacks permission: can_view_all');
  err.status = 403;
  api.getOperationalIntelligence.mockRejectedValue(err);
  render(<OperationalHealthTab />);
  await waitFor(() =>
    expect(screen.getByTestId('operational-health-error')).toHaveTextContent(
      'You do not have access to operational health information.'
    )
  );
  expect(screen.queryByText('can_view_all')).not.toBeInTheDocument();
});

it('offers no operational control other than Refresh', async () => {
  render(<OperationalHealthTab />);
  await waitFor(() => expect(screen.getByTestId('operational-health-tab')).toBeInTheDocument());

  const buttons = screen.getAllByRole('button').map((b) => b.textContent);
  expect(buttons).toEqual(['Refresh']);

  // No input/select/checkbox anywhere: no filter, no action, no acknowledgement.
  expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
});

it('re-fetches the same read-only endpoints on Refresh', async () => {
  render(<OperationalHealthTab />);
  await waitFor(() => expect(screen.getByTestId('operational-health-tab')).toBeInTheDocument());

  fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));

  await waitFor(() => expect(api.getOperationalIntelligence).toHaveBeenCalledTimes(2));
  expect(api.getOperationalHealthQueue).toHaveBeenCalledTimes(2);
  expect(api.getOperationalHealthWorker).toHaveBeenCalledTimes(2);
});

it('shows a meaningful empty state when the queue is empty', async () => {
  api.getOperationalIntelligence.mockResolvedValue(
    intel({ queue_depth_by_stage: {}, error_rate_by_stage: {} })
  );
  render(<OperationalHealthTab />);
  await waitFor(() => expect(screen.getByTestId('empty-queue')).toBeInTheDocument());
  expect(screen.getByTestId('no-stage-errors')).toBeInTheDocument();
});

// ---------------------------------------------------------------------------
// X5 role-based console gating: the tab exists only for `can_view_all` staff
// ---------------------------------------------------------------------------

jest.mock('react-router-dom', () => {
  const params = new URLSearchParams('tab=operational-health');
  return {
    Navigate: ({ to }) => <div data-testid="navigate-to">{String(to)}</div>,
    useSearchParams: () => [params, jest.fn()],
  };
});

jest.mock('../ops/OpsDashboard', () => () => <div>Dashboard stub</div>);
jest.mock('../ops/OperatorQueue', () => () => <div>Data entry stub</div>);
jest.mock('../ops/ProcessingEntitiesTab', () => () => <div>Entities stub</div>);
jest.mock('../ops/ReviewQueue', () => () => <div>Review stub</div>);
jest.mock('../ops/CtQcTab', () => () => <div>CT QC stub</div>);
jest.mock('../ops/QcQueue', () => () => <div>QC stub</div>);
jest.mock('../ops/SlaTab', () => () => <div>SLA stub</div>);
jest.mock('../ops/StaffRoster', () => () => <div>Staff stub</div>);
jest.mock('../ops/StaffRolesTab', () => () => <div>Roles stub</div>);
jest.mock('../ops/CommercialTab', () => () => <div>Commercial stub</div>);
jest.mock('../ops/SettingsTab', () => () => <div>Settings stub</div>);
jest.mock('../ops/IssuesTriageTab', () => () => <div>Issues stub</div>);
jest.mock('../ops/AuditConsoleTab', () => () => <div>Audit stub</div>);
jest.mock('../ops/OpsMessagingTab', () => () => <div>Messaging stub</div>);
jest.mock('../ops/OpsPeMessagingTab', () => () => <div>PE messages stub</div>);
jest.mock('../ops/OpsAssignmentsTab', () => () => <div>Assignment tab stub</div>);

describe('OperationsPage operational-health gating (X5)', () => {
  const OperationsPage = require('../ops/OperationsPage').default;

  it('renders the tab for internal staff with can_view_all', async () => {
    api.getOpsMe.mockResolvedValue({
      profile: { entity_id: null, role_name: 'operator', first_name: 'Ops', last_name: 'One' },
      permissions: { can_view_all: true, can_process: false },
    });
    render(<OperationsPage />);
    expect(
      await screen.findByRole('button', { name: /Operational health/ })
    ).toBeInTheDocument();
    // The active tab renders the real panel over the mocked read-only endpoints.
    expect(await screen.findByTestId('operational-health-tab')).toBeInTheDocument();
  });

  it('does not offer the tab to staff without can_view_all', async () => {
    api.getOpsMe.mockResolvedValue({
      profile: { entity_id: null, role_name: 'reviewer', first_name: 'Ops', last_name: 'Two' },
      permissions: { can_view_all: false, can_review: true },
    });
    render(<OperationsPage />);
    await waitFor(() => expect(api.getOpsMe).toHaveBeenCalled());
    expect(screen.queryByRole('button', { name: /Operational health/ })).not.toBeInTheDocument();
  });
});


