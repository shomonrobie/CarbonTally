// frontend/src/v3/__tests__/processing-upload-capability.test.jsx
//
// I-03 (CT-CARBONTALLY-FOUNDATION-CLOSURE-02) — the customer Processing page must
// not offer a document upload that the caller's client-access profile cannot
// perform. UploadDocumentsPanel.jsx already gates on the same `upload_document`
// capability; ProcessingPage.jsx previously rendered the upload control
// unconditionally. The backend (api/upload_gate.py) is authoritative in every
// case — this is presentation only.
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('react-router-dom', () => ({ useNavigate: () => jest.fn() }));

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
import { ClientAccessProvider } from '../clientAccess';

const api = jest.requireMock('../api');

beforeEach(() => {
  jest.clearAllMocks();
  api.resolveV3Organization.mockResolvedValue({ id: 'org-1' });
  api.getProcessingStatus.mockResolvedValue({ total_items: 0, pct_complete: 0, pipeline: {} });
  api.getProcessingJobs.mockResolvedValue({ jobs: [] });
  api.v3ListExtractionBatches.mockResolvedValue({ batches: [] });
});

function renderWithAccess(value) {
  const page = <ProcessingPage />;
  return render(
    value ? <ClientAccessProvider value={value}>{page}</ClientAccessProvider> : page
  );
}

test('offers the upload control when there is no client restriction', async () => {
  renderWithAccess(null);
  expect(await screen.findByText('Upload & process')).toBeInTheDocument();
  expect(screen.queryByTestId('upload-unavailable-notice')).toBeNull();
});

test('hides the upload control when the profile denies upload_document', async () => {
  renderWithAccess({
    profile: 'managed',
    state: 'active',
    capabilities: { upload_document: false },
  });
  expect(await screen.findByTestId('upload-unavailable-notice')).toBeInTheDocument();
  expect(screen.queryByText('Upload & process')).toBeNull();
});

test('offers the upload control when the profile permits upload_document', async () => {
  renderWithAccess({
    profile: 'collaborative',
    state: 'active',
    capabilities: { upload_document: true },
  });
  expect(await screen.findByText('Upload & process')).toBeInTheDocument();
  expect(screen.queryByTestId('upload-unavailable-notice')).toBeNull();
});
