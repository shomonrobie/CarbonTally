// frontend/src/v3/__tests__/report-lifecycle-panel.test.jsx
//
// S6 (visibility-first) reference test for the customer-facing report
// lifecycle panel:
//   * the displayed state is the persisted version state (not derived);
//   * the offered actions come only from the server's `allowed_actions`;
//   * submitting for review calls the existing lifecycle endpoint and reloads;
//   * a denied action (403) shows a friendly message (no raw technical error);
//   * immutable (FINAL) versions offer no actions and say so;
//   * no review-comment UI exists in the panel.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../api', () => ({
  REPORT_LIFECYCLE_ACTION_CALLS: {
    submit_review: jest.fn(),
    approve: jest.fn(),
    request_changes: jest.fn(),
    reject: jest.fn(),
    finalize: jest.fn(),
  },
}));

import ReportLifecyclePanel from '../reports/ReportLifecyclePanel';
import { REPORT_LIFECYCLE_ACTION_CALLS as calls } from '../api';

const version = (over = {}) => ({
  id: 'ver-1',
  version_number: 1,
  status: 'DRAFT',
  is_current: true,
  created_at: '2026-01-01T10:00:00Z',
  allowed_actions: ['submit_review'],
  ...over,
});

beforeEach(() => {
  jest.clearAllMocks();
});

it('shows the persisted state and the server-provided action only', () => {
  render(<ReportLifecyclePanel reportId="rep-1" versions={[version()]} />);
  expect(screen.getByLabelText('Report state: Draft')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Submit for review' })).toBeInTheDocument();
  // Not offered because the server did not list it for DRAFT.
  expect(screen.queryByRole('button', { name: 'Approve' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Finalize' })).not.toBeInTheDocument();
});

it('submits the current version for review and reloads authoritative state', async () => {
  calls.submit_review.mockResolvedValue({ status: 'REVIEWED' });
  const onChanged = jest.fn().mockResolvedValue(undefined);
  render(
    <ReportLifecyclePanel reportId="rep-1" versions={[version()]} onChanged={onChanged} />
  );
  fireEvent.click(screen.getByRole('button', { name: 'Submit for review' }));
  await waitFor(() =>
    expect(calls.submit_review).toHaveBeenCalledWith('rep-1', 1)
  );
  await waitFor(() => expect(onChanged).toHaveBeenCalled());
});

it('shows a friendly message when the user is not permitted (403)', async () => {
  const err = new Error('forbidden');
  err.status = 403;
  calls.submit_review.mockRejectedValue(err);
  render(<ReportLifecyclePanel reportId="rep-1" versions={[version()]} />);
  fireEvent.click(screen.getByRole('button', { name: 'Submit for review' }));
  await waitFor(() =>
    expect(screen.getByTestId('lifecycle-error')).toHaveTextContent(
      'You do not have permission to perform this action on this report.'
    )
  );
  expect(screen.queryByText('forbidden')).not.toBeInTheDocument();
});

it('locks an APPROVED version (no transition offered by the server)', () => {
  render(
    <ReportLifecyclePanel
      reportId="rep-1"
      versions={[
        version({ status: 'FINAL', is_current: false, allowed_actions: [] }),
        version({ id: 'ver-2', version_number: 2, status: 'APPROVED', allowed_actions: ['finalize'] }),
      ]}
    />
  );
  expect(screen.getByLabelText('Report state: Approved')).toBeInTheDocument();
  expect(screen.getByTestId('lifecycle-locked')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Finalize' })).toBeInTheDocument();
});

it('renders the version history with each persisted state', () => {
  render(
    <ReportLifecyclePanel
      reportId="rep-1"
      versions={[
        version({ status: 'CHANGES_REQUESTED', is_current: false, allowed_actions: [] }),
        version({ id: 'ver-2', version_number: 2, status: 'REVIEWED', allowed_actions: ['approve'] }),
      ]}
    />
  );
  expect(screen.getByText('Changes requested')).toBeInTheDocument();
  // "In review" appears on the current-state chip and in the history row.
  expect(screen.getAllByText('In review').length).toBeGreaterThanOrEqual(1);
  expect(screen.getAllByText('Current').length).toBeGreaterThanOrEqual(1);
  // S6 first release: no comment capability anywhere in the panel.
  expect(screen.queryByText(/comment/i)).not.toBeInTheDocument();
  expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
});

it('offers nothing when the server supplies no action set', () => {
  const v = version();
  delete v.allowed_actions;
  render(<ReportLifecyclePanel reportId="rep-1" versions={[v]} />);
  expect(screen.getByTestId('lifecycle-noactions')).toBeInTheDocument();
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
});

it('never renders a dead button for an action outside this release', () => {
  // The server legitimately offers `new_version` from FINAL. That transition is
  // outside the S6 first-release action list, so it must appear as guidance —
  // not as a button that does nothing.
  render(
    <ReportLifecyclePanel
      reportId="rep-1"
      versions={[version({ status: 'FINAL', allowed_actions: ['new_version'] })]}
    />
  );
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
  expect(screen.getByTestId('lifecycle-noactions')).toHaveTextContent(
    /revised version/
  );
  expect(screen.getByLabelText('Report state: Final')).toBeInTheDocument();
});

it('renders only the performable subset when the server offers both', () => {
  render(
    <ReportLifecyclePanel
      reportId="rep-1"
      versions={[
        version({ status: 'APPROVED', allowed_actions: ['finalize', 'new_version'] }),
      ]}
    />
  );
  expect(screen.getByRole('button', { name: 'Finalize' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /new version/i })).not.toBeInTheDocument();
});
