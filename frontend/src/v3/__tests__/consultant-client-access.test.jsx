// frontend/src/v3/__tests__/consultant-client-access.test.jsx
// CT-CONSULTANT-CLIENT-ACCESS-UX-01.
//
// Closes CoStrict finding F3 (consultant-side client-invitation UI was not wired)
// and the reported "You don't have permission to access this area" error: a
// consultant operating a managed client saw the Organisation-admin "Members &
// Invitations" surface, which calls ORG-member/org-admin-gated endpoints and
// therefore 403s for a consultant. The consultant plane now renders a dedicated
// "Client Access" tab wired to the EXISTING, server-gated CT-04 consultant
// endpoints.
//
// These are UI-wiring tests only. The security boundary is the backend and is
// asserted separately in test_ct_consultant_client_identity_04.py.
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getUser: jest.fn(), getSession: jest.fn() } },
}));

jest.mock('../api', () => {
  const actual = jest.requireActual('../api');
  return {
    ...actual,
    // Direct-customer Organisation admin plane
    resolveV3Organization: jest.fn(),
    resolveV3Membership: jest.fn(),
    listOrgRoles: jest.fn(),
    listMembers: jest.fn(),
    listInvitations: jest.fn(),
    createInvitation: jest.fn(),
    // Consultant client plane
    listClientUsers: jest.fn(),
    listClientInvitations: jest.fn(),
    createClientInvitation: jest.fn(),
    revokeClientInvitation: jest.fn(),
    updateClientUser: jest.fn(),
  };
});

import ClientAccessTab from '../consultant/ClientAccessTab';
import AdminPage from '../admin/AdminPage';
import { ConsultantClientProvider } from '../consultant/ConsultantClientContext';
import * as api from '../api';

const INVITATIONS = {
  organization_id: 'org-1',
  invitations: [
    { id: 'inv-1', email: 'client@example.com', role: 'member', state: 'pending' },
  ],
};
const USERS = {
  organization_id: 'org-1',
  users: [
    { id: 'm-1', user_id: 'u-1', email: 'owner@example.com', first_name: 'Client',
      last_name: 'Owner', role: 'owner', is_active: true },
    { id: 'm-2', user_id: 'u-2', email: 'staff@example.com', first_name: 'Client',
      last_name: 'Member', role: 'member', is_active: true },
  ],
};

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  api.listClientUsers.mockResolvedValue(USERS);
  api.listClientInvitations.mockResolvedValue(INVITATIONS);
  api.createClientInvitation.mockResolvedValue({ id: 'inv-2', email: 'new@example.com' });
  api.revokeClientInvitation.mockResolvedValue(null);
  api.updateClientUser.mockResolvedValue({ id: 'm-2', role: 'viewer', is_active: true });
  api.resolveV3Organization.mockResolvedValue({ id: 'org-1', name: 'Quayside Energy' });
  api.resolveV3Membership.mockResolvedValue(null);
  api.listOrgRoles.mockResolvedValue({ roles: [] });
  api.listMembers.mockResolvedValue({ members: [] });
  api.listInvitations.mockResolvedValue({ invitations: [] });
});

function renderTab() {
  return render(<ClientAccessTab clientId="client-1" />);
}

function renderAdminInPlane() {
  return render(
    <MemoryRouter initialEntries={['/organization?tab=members']}>
      <ConsultantClientProvider value={{ active: true, clientId: 'client-1' }}>
        <AdminPage />
      </ConsultantClientProvider>
    </MemoryRouter>,
  );
}

function renderAdminDirect() {
  return render(
    <MemoryRouter initialEntries={['/organization?tab=members']}>
      <AdminPage />
    </MemoryRouter>,
  );
}

describe('ClientAccessTab — consultant-plane Client Access (CT04 wiring)', () => {
  test('12/13. renders the Client Access page and the Invite Client form', async () => {
    renderTab();
    expect(await screen.findByTestId('client-access')).toBeInTheDocument();
    expect(screen.getByText('Client Access')).toBeInTheDocument();
    expect(
      screen.getByText(/invite your client to access their carbontally dashboard/i),
    ).toBeInTheDocument();

    // Primary CTA is "Invite Client"; the form appears on demand.
    const cta = screen.getByRole('button', { name: /\+\s*invite client/i });
    fireEvent.click(cta);
    expect(await screen.findByTestId('invite-client-form')).toBeInTheDocument();
    expect(screen.getByLabelText(/client email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/client access level/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send invitation/i })).toBeInTheDocument();
  });

  test('14. sending an invitation calls the CONSULTANT endpoint (never the org one)', async () => {
    renderTab();
    await screen.findByTestId('client-access');
    fireEvent.click(screen.getByRole('button', { name: /\+\s*invite client/i }));
    fireEvent.change(screen.getByLabelText(/client email address/i), {
      target: { value: 'newclient@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/client access level/i), {
      target: { value: 'admin' },
    });
    fireEvent.click(screen.getByRole('button', { name: /send invitation/i }));

    await waitFor(() =>
      expect(api.createClientInvitation).toHaveBeenCalledWith('client-1', {
        email: 'newclient@example.com',
        role: 'admin',
      }),
    );
    // The org-plane invitation helper must never be used in the consultant plane.
    expect(api.createInvitation).not.toHaveBeenCalled();
  });

  test('15. the normal invite flow requires only email + role (no raw user id)', async () => {
    renderTab();
    await screen.findByTestId('client-access');
    fireEvent.click(screen.getByRole('button', { name: /\+\s*invite client/i }));
    await screen.findByTestId('invite-client-form');

    expect(screen.queryByPlaceholderText(/user id/i)).toBeNull();
    expect(screen.queryByLabelText(/user id/i)).toBeNull();
    // Send is disabled until an email is entered — user_id is never required.
    expect(screen.getByRole('button', { name: /send invitation/i })).toBeDisabled();
  });

  test('16. pending invitations render with human-readable access labels', async () => {
    renderTab();
    await screen.findByTestId('client-access');
    expect(screen.getByText('client@example.com')).toBeInTheDocument();
    expect(screen.getAllByText('Client Member').length).toBeGreaterThan(0);
    expect(screen.getByText('pending')).toBeInTheDocument();
    // No invitation bearer token or accept link is ever exposed.
    expect(document.body.textContent).not.toMatch(/token/i);
    expect(document.body.textContent).not.toMatch(/accept[-_ ]?url/i);
  });

  test('17. revoke calls the consultant invitation API', async () => {
    renderTab();
    await screen.findByTestId('client-access');
    fireEvent.click(screen.getByRole('button', { name: /revoke/i }));
    await waitFor(() =>
      expect(api.revokeClientInvitation).toHaveBeenCalledWith('client-1', 'inv-1'),
    );
  });

  test('18. changing a client user role calls the consultant role API', async () => {
    renderTab();
    await screen.findByTestId('client-access');
    fireEvent.change(screen.getByLabelText(/access for staff@example\.com/i), {
      target: { value: 'viewer' },
    });
    await waitFor(() =>
      expect(api.updateClientUser).toHaveBeenCalledWith('client-1', 'm-2', { role: 'viewer' }),
    );
  });

  test('19. a permission denial renders a controlled message (no raw error, no crash)', async () => {
    const denied = Object.assign(new Error('Forbidden'), { status: 403 });
    api.listClientUsers.mockRejectedValue(denied);
    api.listClientInvitations.mockRejectedValue(denied);
    renderTab();
    expect(await screen.findByTestId('client-access-unavailable')).toBeInTheDocument();
    expect(
      screen.getByText(/you do not have permission to manage client access/i),
    ).toBeInTheDocument();
  });

  test('10b. role escalation is not offered beyond the four client roles', async () => {
    renderTab();
    await screen.findByTestId('client-access');
    const roleSelect = screen.getByLabelText(/access for staff@example\.com/i);
    const options = Array.from(roleSelect.querySelectorAll('option')).map((o) => o.value);
    expect(options).toEqual(['owner', 'admin', 'member', 'viewer']);
  });
});

describe('AdminPage tab wiring — consultant plane vs direct customer', () => {
  test('12b. in the client plane the members tab is "Client Access" and uses the consultant API', async () => {
    renderAdminInPlane();
    // The tab label is the consultant-appropriate one…
    expect(await screen.findByRole('button', { name: 'Client Access' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Members & Invitations' })).toBeNull();
    // …and the pane is the consultant Client Access surface.
    expect(await screen.findByTestId('client-access')).toBeInTheDocument();
    await waitFor(() => expect(api.listClientUsers).toHaveBeenCalledWith('client-1'));
    // The org-scoped members endpoint is never probed in the consultant plane.
    expect(api.listMembers).not.toHaveBeenCalled();
  });

  test('20. the direct-customer plane keeps "Members & Invitations" (org API, unchanged)', async () => {
    renderAdminDirect();
    expect(await screen.findByRole('button', { name: 'Members & Invitations' })).toBeInTheDocument();
    await waitFor(() => expect(api.listMembers).toHaveBeenCalledWith('org-1'));
    expect(api.listClientUsers).not.toHaveBeenCalled();
    // The direct customer does not get the consultant "Client Access" surface.
    expect(screen.queryByTestId('client-access')).toBeNull();
  });
});


