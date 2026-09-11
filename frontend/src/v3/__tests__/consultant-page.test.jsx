// frontend/src/v3/__tests__/consultant-page.test.jsx
// BL-6 / BL-7 — consultant workspace information architecture + upload feedback.
//
// BL-7: the client directory + lifecycle management now lives in a dedicated,
// always-available "Clients" tab instead of rendering below the workspace
// content; selection stays on the top-level switcher.
// BL-6: the upload notice reports the uploaded document's REAL pipeline stage
// from the refreshed items, and the workspace polls the backend stage state
// while any item is still in flight (no fake progress).
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
  useSearchParams: () => [new URLSearchParams(), jest.fn()],
}));

jest.mock('../consultant/WhiteLabelTab', () => () => <div>White-label tab</div>);
jest.mock('../consultant/ClientMessagingTab', () => () => <div>Client messaging tab</div>);
jest.mock('../consultant/ConsultantTeamTab', () => () => <div>Team tab</div>);
jest.mock('../consultant/NewCustomerView', () => () => <div>New customer view</div>);

jest.mock('../api', () => ({
  getClientDashboard: jest.fn(),
  getClientDocuments: jest.fn(),
  getClientEvidence: jest.fn(),
  getClientIssues: jest.fn(),
  getClientProcessingItems: jest.fn(),
  getClientProcessingStatus: jest.fn(),
  getClientReports: jest.fn(),
  getConsultantBranding: jest.fn(),
  getConsultantBrandingContext: jest.fn(),
  getConsultantClientDetail: jest.fn(),
  getConsultantDashboard: jest.fn(),
  getConsultantPortfolio: jest.fn(),
  getConsultantProfile: jest.fn(),
  listConsultantClients: jest.fn(),
  updateConsultantBranding: jest.fn(),
  updateConsultantClientStatus: jest.fn(),
  uploadConsultantDocument: jest.fn(),
  endConsultantClient: jest.fn(),
  reactivateConsultantClient: jest.fn(),
  suspendConsultantClient: jest.fn(),
}));

import ConsultantPage from '../consultant/ConsultantPage';
import * as api from '../api';

const CLIENTS = [
  { id: 'client-1', client_name: 'Quayside Energy', client_industry: 'Energy', status: 'active', organization_id: 'org-1' },
  { id: 'client-2', client_name: 'Granite Distribution', client_industry: 'Logistics', status: 'suspended', organization_id: 'org-2' },
];

const PROFILE = { id: 'consultant-1', company_name: 'Acme Consulting', can_manage_clients: true };

const WORKSPACE_ITEM = {
  id: 'item-1',
  file_name: 'bill.pdf',
  file_id: 'doc-1',
  status: 'pending',
  organization: { id: 'org-1', name: 'Quayside Energy' },
};

function mockWorkspaceEndpoints(status = 'pending') {
  api.getClientReports.mockResolvedValue({ reports: [] });
  api.getClientDashboard.mockResolvedValue({ total_co2e_kg: 0, total_rows: 0 });
  api.getClientProcessingStatus.mockResolvedValue({ status: { extraction: 1 } });
  api.getClientIssues.mockResolvedValue({ issues: [] });
  api.getClientDocuments.mockResolvedValue({ documents: [] });
  api.getClientProcessingItems.mockResolvedValue({
    items: [{ ...WORKSPACE_ITEM, status }],
  });
  api.getClientEvidence.mockResolvedValue({ calculations: [] });
}

beforeEach(() => {
  jest.clearAllMocks();
  window.confirm = jest.fn(() => true);
  // A returning consultant has a remembered active client; this also avoids the
  // CON-6 auto-select double-load flicker in the tests.
  localStorage.setItem('v3_consultant_active_client', 'client-1');
  api.getConsultantProfile.mockResolvedValue(PROFILE);
  api.listConsultantClients.mockResolvedValue({ clients: CLIENTS });
  api.getConsultantDashboard.mockResolvedValue({});
  api.getConsultantBrandingContext.mockResolvedValue({ brand_context: { kind: 'carbon_tally' } });
  api.getConsultantPortfolio.mockResolvedValue({ portfolio: {}, clients: [] });
});

describe('Consultant workspace IA (BL-7)', () => {
  test('renders the active-client context banner and a Clients tab', async () => {
    render(<ConsultantPage />);
    expect(await screen.findByText('Acme Consulting · multi-client portal')).toBeInTheDocument();
    expect(screen.getByText(/current organization/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /clients/i })).toBeInTheDocument();
  });

  test('client directory + lifecycle actions live in the Clients tab', async () => {
    const { container } = render(<ConsultantPage />);
    await screen.findByText('Acme Consulting · multi-client portal');

    // On the default dashboard the directory is NOT rendered below content
    // (no lifecycle controls anywhere until the Clients tab is opened).
    expect(screen.queryByRole('button', { name: /suspend/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /clients/i }));
    // The directory renders one row per client (the switcher options are not rows).
    expect(container.querySelectorAll('.v3-client-list-item')).toHaveLength(2);
    expect(screen.getAllByText(/ACTIVE|SUSPENDED/).length).toBe(2);
    // Lifecycle actions reachable from the tab (was previously buried at the bottom).
    expect(screen.getByRole('button', { name: /suspend/i })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /^end$/i }).length).toBe(2);
    expect(screen.getByRole('button', { name: /reactivate/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /\+ new customer/i })).toBeInTheDocument();
  });

  test('lifecycle actions call the backend and refresh the list', async () => {
    render(<ConsultantPage />);
    await screen.findByText('Acme Consulting · multi-client portal');
    fireEvent.click(screen.getByRole('button', { name: /clients/i }));

    const endButton = screen.getAllByRole('button', { name: /^end$/i })[0];
    fireEvent.click(endButton);
    await waitFor(() => {
      expect(api.endConsultantClient).toHaveBeenCalledWith('client-1');
    });
    expect(window.confirm).toHaveBeenCalled();
  });

  test('non-manager consultants see the directory without lifecycle controls', async () => {
    api.getConsultantProfile.mockResolvedValue({ ...PROFILE, can_manage_clients: false });
    const { container } = render(<ConsultantPage />);
    await screen.findByText('Acme Consulting · multi-client portal');
    fireEvent.click(screen.getByRole('button', { name: /clients/i }));

    expect(container.querySelectorAll('.v3-client-list-item')).toHaveLength(2);
    expect(screen.queryByRole('button', { name: /suspend/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /\+ new customer/i })).not.toBeInTheDocument();
  });
});



describe('Consultant upload / processing feedback (BL-6)', () => {
  const renderWorkspace = async () => {
    const { container } = render(<ConsultantPage />);
    await screen.findByText('Acme Consulting · multi-client portal');
    fireEvent.click(screen.getByRole('button', { name: /client workspace/i }));
    await waitFor(() => expect(screen.getByText(/processing pipeline/i)).toBeInTheDocument());
    return { container };
  };

  test('upload notice reports the document real pipeline stage', async () => {
    mockWorkspaceEndpoints('pending');
    api.uploadConsultantDocument.mockResolvedValue({
      document: { id: 'doc-1', name: 'bill.pdf', organization_id: 'org-1', client_id: 'client-1' },
    });
    const { container } = await renderWorkspace();

    const fileInput = container.querySelector('input[type="file"]');
    const file = new File(['data'], 'bill.pdf', { type: 'application/pdf' });
    fireEvent.change(fileInput, { target: { files: [file] } });

    expect(api.uploadConsultantDocument).toHaveBeenCalledWith('client-1', file, 'utility');
    await waitFor(() => {
      expect(screen.getByText(/current stage: pending/i)).toBeInTheDocument();
    });
  });

  test('failed upload surfaces an error and does not claim completion', async () => {
    mockWorkspaceEndpoints('pending');
    api.uploadConsultantDocument.mockRejectedValue(new Error('storage unavailable'));
    const { container } = await renderWorkspace();

    const fileInput = container.querySelector('input[type="file"]');
    fireEvent.change(fileInput, { target: { files: [new File(['x'], 'bad.pdf', { type: 'application/pdf' })] } });

    await waitFor(() => {
      expect(screen.getByText(/storage unavailable/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/current stage:/i)).not.toBeInTheDocument();
  });

  test('polls the real backend stage while items are in flight', async () => {
    jest.useFakeTimers();
    try {
      mockWorkspaceEndpoints('extracting');
      render(<ConsultantPage />);
      // Flush the initial load promises (all mockResolvedValue).
      await act(async () => {});
      await act(async () => {});
      fireEvent.click(screen.getByRole('button', { name: /client workspace/i }));
      await act(async () => {});
      await act(async () => {});

      const callsBefore = api.getClientProcessingItems.mock.calls.length;
      await act(async () => {
        jest.advanceTimersByTime(10000);
      });
      expect(api.getClientProcessingItems.mock.calls.length).toBeGreaterThan(callsBefore);
      expect(api.getClientProcessingStatus.mock.calls.length).toBeGreaterThanOrEqual(2);
    } finally {
      jest.useRealTimers();
    }
  });
});
