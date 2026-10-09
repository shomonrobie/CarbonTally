// frontend/src/v3/__tests__/consultant-page.test.jsx
// BL-6 / BL-7 — consultant workspace information architecture + upload feedback.
//
// BL-7: the client directory + lifecycle management now lives in a dedicated,
// always-available "Clients" tab instead of rendering below the workspace
// content. CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A (UX-01/AC-01): the
// Consultant Plane represents the FIRM and has no global "Active client"; a
// client is chosen via Clients → Open workspace (the Client Operating Plane).
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
  api.getConsultantProfile.mockResolvedValue(PROFILE);
  api.listConsultantClients.mockResolvedValue({ clients: CLIENTS });
  api.getConsultantDashboard.mockResolvedValue({});
  api.getConsultantBrandingContext.mockResolvedValue({ brand_context: { kind: 'carbon_tally' } });
  api.getConsultantPortfolio.mockResolvedValue({ portfolio: {}, clients: [] });
});

describe('Consultant workspace IA (BL-7)', () => {
  test('renders the firm context banner and a Clients tab, with NO global Active client', async () => {
    render(<ConsultantPage />);
    expect(await screen.findByText('Acme Consulting · multi-client portal')).toBeInTheDocument();
    // CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01 (UX-02/AC-04) — the actor is the
    // consultant firm; the old "Current organization / <client> / Client" wording
    // (which implied impersonation) is gone.
    expect(screen.getByText('Consultant')).toBeInTheDocument();
    expect(screen.getByText(/you operate your clients on their behalf/i)).toBeInTheDocument();
    expect(screen.queryByText(/current organization/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /clients/i })).toBeInTheDocument();
    // UX-03/AC-02 — "Client workspace" no longer competes as a consultant-plane tab.
    expect(screen.queryByRole('button', { name: /client workspace/i })).not.toBeInTheDocument();
    // CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A (UX-01/AC-01) — the Consultant
    // Plane represents the FIRM and has NO global Active client selector.
    expect(screen.queryByLabelText(/select active client/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Active client')).not.toBeInTheDocument();
    expect(screen.queryByText(/no client selected/i)).not.toBeInTheDocument();
    expect(document.querySelector('.v3-client-switcher')).toBeNull();
  });

  test('client directory + lifecycle actions live in the Clients tab', async () => {
    const { container } = render(<ConsultantPage />);
    await screen.findByText('Acme Consulting · multi-client portal');

    // On the default dashboard the directory is NOT rendered below content
    // (no lifecycle controls anywhere until the Clients tab is opened).
    expect(screen.queryByRole('button', { name: /suspend/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /clients/i }));
    // The directory renders one row per client.
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

// CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01 (UX-03/AC-02) — the legacy inline
// "Client workspace" mini-dashboard and its BL-6 upload/polling feedback were
// removed from the consultant hub: a client's workspace is now the Client Org
// plane (/consultant/clients/:clientId/*), reached via "Open workspace". Those
// behaviours live on the shared customer Documents/Processing surfaces, so the
// BL-6 consultant-hub tests were deleted with the component rather than left
// asserting removed UI.
