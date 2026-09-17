// frontend/src/v3/__tests__/customer-blocked-visibility.test.jsx
// Step 2 / WS-H (F-11) — a blocked automatic-processing job must remain visible
// to the customer with the truthful block reason and a next step, rather than
// silently dropping out of the "in flight" view.
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
}));

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: jest.fn(), getUser: jest.fn() } },
}));

jest.mock('../api', () => ({
  confirmProcessingJob: jest.fn(),
  getProcessingJobs: jest.fn(),
  getProcessingStatus: jest.fn(),
  resolveV3Organization: jest.fn(),
  retryProcessingJob: jest.fn(),
  v3ListExtractionBatches: jest.fn(),
  v3ListExtractionItems: jest.fn(),
  v3UploadDocument: jest.fn(),
}));

import ProcessingPage from '../customer/ProcessingPage';

const api = jest.requireMock('../api');

const BLOCKED_JOB = {
  id: 'job-1',
  file_name: 'color_07_water.pdf',
  stage: 'blocked',
  status: 'manual_review',
  stage_label: 'Blocked',
  manual_review_reason:
    'extraction completeness 0.33 below 0.50 threshold - unresolved: quantity, unit',
  completeness: 0.33,
  attempt_count: 0,
};

beforeEach(() => {
  jest.clearAllMocks();
  api.resolveV3Organization.mockResolvedValue({ id: 'org-1', name: 'Org One' });
  api.getProcessingStatus.mockResolvedValue({ pipeline: {}, total_items: 0, pct_complete: 0 });
  api.getProcessingJobs.mockResolvedValue({ jobs: [] });
  api.v3ListExtractionBatches.mockResolvedValue({ batches: [] });
  api.v3ListExtractionItems.mockResolvedValue({ items: [] });
});

test('a blocked job is surfaced to the customer with its reason and a next step', async () => {
  api.getProcessingJobs.mockResolvedValue({ jobs: [BLOCKED_JOB] });

  render(<ProcessingPage />);

  const notice = await screen.findByTestId('blocked-jobs-notice');
  expect(notice).toBeInTheDocument();
  expect(notice).toHaveTextContent('Waiting for review (1)');
  expect(notice).toHaveTextContent('color_07_water.pdf');
  // the truthful server-provided reason is shown, not a generic message
  expect(notice).toHaveTextContent('unresolved: quantity, unit');
  // and the customer is told what happens next / that data was preserved
  expect(notice).toHaveTextContent('Nothing has been discarded');
});

test('no blocked notice is shown when nothing is blocked', async () => {
  api.getProcessingJobs.mockResolvedValue({
    jobs: [{ ...BLOCKED_JOB, id: 'job-2', stage: 'completed', status: 'completed', manual_review_reason: null }],
  });

  render(<ProcessingPage />);

  await waitFor(() => expect(api.getProcessingJobs).toHaveBeenCalled());
  expect(screen.queryByTestId('blocked-jobs-notice')).not.toBeInTheDocument();
});
