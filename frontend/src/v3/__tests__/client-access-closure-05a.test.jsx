// frontend/src/v3/__tests__/client-access-closure-05a.test.jsx
// CT-CONSULTANT-CLIENT-PLANE-AUTH-CLOSURE-05A.
//
// UI-reflection tests for the client-access ceiling on the two remaining
// ORGANISATION-plane actions from CT-05 §8.2:
//
//   approve_final          → customer FINAL approval / rejection
//   correct_submitted_data → correcting a consultant's submitted extraction
//
// The ratified ceiling is ✗OFF ✗READ_ONLY ✓COLLABORATIVE ✗MANAGED ✗RETAINED
// (CT-CONSULTANT-PO-CONSOLIDATION-01 §8.2), and the server enforces the
// identical ceiling in api/client_access_guard.py on
// /processing/items/{id}/customer-review, /extract,
// /automatic-processing/jobs/{id}/review and /confirm, and
// /manual-extraction/items/{id}. These tests assert only that the UI stops
// OFFERING the actions a MANAGED client may not perform, and that the control
// is accompanied by an explanation instead of silently vanishing.
//
// PRESENTATION ONLY — the default (direct customer, consultant, staff) is
// unrestricted, so those surfaces are unchanged.
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: jest.fn(), getUser: jest.fn(), signOut: jest.fn() } },
}));

const api = jest.requireMock('../api');
jest.mock('../api', () => ({
  resolveV3Membership: jest.fn(),
  getProcessingItemWorkspace: jest.fn(),
  getProcessingJobs: jest.fn(),
  getDocumentEmissions: jest.fn(),
  getProcessingMappingOptions: jest.fn(),
  getEmissionEvidence: jest.fn(),
  saveProcessingExtraction: jest.fn(),
  saveProcessingMapping: jest.fn(),
  validateProcessingItem: jest.fn(),
  calculateProcessingItem: jest.fn(),
  startProcessingItem: jest.fn(),
  submitCustomerReview: jest.fn(),
  retryProcessingJob: jest.fn(),
  confirmProcessingJob: jest.fn(),
  reviewProcessingJob: jest.fn(),
}));

import ProcessingItemWorkspace from '../customer/ProcessingItemWorkspace';
import ReviewDetailPage from '../customer/ReviewDetailPage';
import { ClientAccessProvider } from '../clientAccess';

// CT-05A §8.2 — the ratified client-access ceiling for these two operations.
const MANAGED = {
  profile: 'managed',
  state: 'active',
  capabilities: { approve_final: false, correct_submitted_data: false },
};

function workspace(status = 'extracted') {
  return {
    item: {
      id: 'item-1',
      file_name: 'electricity_invoice.pdf',
      file_id: 'file-1',
      status,
      page_count: 1,
    },
    batch: { id: 'batch-1', organization_id: 'org-1', status: 'in_progress' },
    source: {
      viewer_url: 'https://signed/viewer',
      file_name: 'electricity_invoice.pdf',
      ocr_suggestions: { activity: 'Electricity' },
    },
    data: {
      extracted_data: { activity: 'Electricity', quantity: 12500, unit: 'kWh' },
      mapped_data: {},
      calculated_emissions_kg_co2e: null,
    },
    status: { status },
    issues: [],
    workflow: { stages: [], allowed_transitions: [] },
  };
}

function workspaceElement() {
  return (
    <MemoryRouter>
      <ProcessingItemWorkspace itemId="item-1" />
    </MemoryRouter>
  );
}

function reviewElement() {
  return (
    <MemoryRouter initialEntries={['/review/item-1']}>
      <Routes>
        <Route path="/review/:itemId" element={<ReviewDetailPage />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  api.getProcessingJobs.mockResolvedValue({ jobs: [] });
  api.getDocumentEmissions.mockResolvedValue({ emissions: [] });
  api.getProcessingMappingOptions.mockResolvedValue({ factors: [], no_factors_reason: '' });
});

describe('CT-05A — the ceiling is applied per operation, not as a blanket block', () => {
  test('a capability the profile does not mention still fails OPEN in the UI', async () => {
    // Only approve_final is denied. The UI must not infer a wider restriction:
    // unknown / not-applicable operations keep their historical behaviour and
    // the server remains the authority.
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'owner' });
    api.getProcessingItemWorkspace.mockResolvedValue(workspace('extracted'));
    render(
      <ClientAccessProvider
        value={{ profile: 'managed', state: 'active', capabilities: { approve_final: false } }}
      >
        {workspaceElement()}
      </ClientAccessProvider>,
    );
    await waitFor(() => expect(screen.getByText('Processing workspace')).toBeInTheDocument());
    expect(screen.getByText('Save extraction')).toBeInTheDocument();
  });
});

describe('CT-05A §8.2 approve_final — customer final approval', () => {
  test('a MANAGED client owner is not offered Approve/Reject on a decidable item', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'owner' });
    api.getProcessingItemWorkspace.mockResolvedValue(workspace('calculated'));
    render(
      <ClientAccessProvider value={MANAGED}>{workspaceElement()}</ClientAccessProvider>,
    );
    await waitFor(() => expect(screen.getByText('Processing workspace')).toBeInTheDocument());
    // The actionable decision buttons are gone (the workflow nav has no Reject
    // step, so any Reject button would be a live decision control).
    expect(screen.queryByRole('button', { name: /^reject/i })).not.toBeInTheDocument();
    // …and the reason is stated rather than the control silently vanishing.
    expect(screen.getByText(/client access level does not permit final approval/i)).toBeInTheDocument();
  });

  test('an unrestricted owner keeps Approve/Reject', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'owner' });
    api.getProcessingItemWorkspace.mockResolvedValue(workspace('calculated'));
    render(workspaceElement());
    await waitFor(() => expect(screen.getByText('Processing workspace')).toBeInTheDocument());
    expect(screen.getAllByRole('button', { name: /^reject/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText(/does not permit final approval/i)).not.toBeInTheDocument();
  });

  test('the review workbench hides Approve/Reject for a MANAGED client owner', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'owner' });
    api.getProcessingItemWorkspace.mockResolvedValue(workspace('customer_review'));
    render(<ClientAccessProvider value={MANAGED}>{reviewElement()}</ClientAccessProvider>);
    await waitFor(() => expect(screen.getByText(/Structured data/)).toBeInTheDocument());
    // The workflow nav renders a (disabled) "Approve" STEP button; the live
    // decision controls are the Reject button and the shared notes field, which
    // only exist when the approver may actually decide.
    expect(screen.queryByRole('button', { name: /^reject$/i })).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Notes \(optional\)/i)).not.toBeInTheDocument();
    expect(screen.getByText(/client access level does not permit final approval/i)).toBeInTheDocument();
  });

  test('the review workbench keeps Approve/Reject for an owner outside a managed client', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'owner' });
    api.getProcessingItemWorkspace.mockResolvedValue(workspace('customer_review'));
    render(reviewElement());
    await waitFor(() => expect(screen.getByText(/Structured data/)).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /^reject$/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Notes \(optional\)/i)).toBeInTheDocument();
  });
});

describe('CT-05A §8.2 correct_submitted_data — correcting submitted data', () => {
  test('a MANAGED client owner cannot save a correction to the submitted extraction', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'owner' });
    api.getProcessingItemWorkspace.mockResolvedValue(workspace('extracted'));
    render(
      <ClientAccessProvider value={MANAGED}>{workspaceElement()}</ClientAccessProvider>,
    );
    await waitFor(() => expect(screen.getByText('Processing workspace')).toBeInTheDocument());
    expect(screen.queryByText('Save extraction')).not.toBeInTheDocument();
    expect(screen.getByText(/does not permit correcting submitted data/i)).toBeInTheDocument();
  });

  test('a COLLABORATIVE client keeps the correction control', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'owner' });
    api.getProcessingItemWorkspace.mockResolvedValue(workspace('extracted'));
    render(
      <ClientAccessProvider
        value={{
          profile: 'collaborative',
          state: 'active',
          capabilities: { approve_final: true, correct_submitted_data: true },
        }}
      >
        {workspaceElement()}
      </ClientAccessProvider>,
    );
    await waitFor(() => expect(screen.getByText('Processing workspace')).toBeInTheDocument());
    expect(screen.getByText('Save extraction')).toBeInTheDocument();
    expect(screen.queryByText(/does not permit correcting submitted data/i)).not.toBeInTheDocument();
  });

  test('an unrestricted user keeps the correction control and its historical copy', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'member' });
    api.getProcessingItemWorkspace.mockResolvedValue(workspace('extracted'));
    render(workspaceElement());
    await waitFor(() => expect(screen.getByText('Processing workspace')).toBeInTheDocument());
    expect(screen.getByText('Save extraction')).toBeInTheDocument();
    expect(
      screen.getByText(/Confirm or correct the fields extracted from the source document/i),
    ).toBeInTheDocument();
  });
});
