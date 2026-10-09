// frontend/src/v3/__tests__/consultant-client-org-shell.test.jsx
// CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01 (PD-1/PD-3/PD-6/PD-9).
// CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01 (UX-01..UX-05).
//
// A consultant managing a client operates the SAME CarbonTally Organisation
// product surface a customer uses — the shared D18 navigation rendered under the
// selected client's route prefix — inside an explicit operating-context shell.
// These tests pin what makes that true, and what the UX remediation added:
//
//   PD-1/PD-3 — the customer Organisation destinations are rendered (reused),
//               prefixed by the selected client.
//   PD-6      — Billing is deliberately NOT carried into a managed client context.
//   PD-9      — the selected client is always explicit and persisted.
//   UX-06     — exactly ONE primary, textual "Back to Consultant" return path.
//   UX-02     — ACTOR (consultant firm) vs SUBJECT (client) is unambiguous.
//   UX-05     — the in-workspace "Switch client" control is REMOVED (a client is
//               chosen in the Consultant Plane via Clients → Open workspace).
//
// The shell grants nothing: the client id in the URL is re-authorised server-side.
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import '@testing-library/jest-dom';

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { signOut: jest.fn(), getSession: jest.fn() } },
}));

jest.mock('../api', () => {
  const actual = jest.requireActual('../api');
  return {
    ...actual,
    getMeContext: jest.fn(),
    getClientWorkspaceContext: jest.fn(),
    getConsultantProfile: jest.fn(),
    listConsultantClients: jest.fn(),
  };
});

import ClientOrgShell from '../consultant/ClientOrgShell';
import * as api from '../api';

const CLIENT_CONTEXT = {
  client: {
    id: 'client-1',
    client_name: 'Quayside Energy',
    organization_id: 'org-1',
    status: 'active',
    client_access_profile: 'managed',
  },
  organization: { id: 'org-1', name: 'Quayside Energy' },
};

function renderClientOrg(clientId = 'client-1') {
  return render(
    <MemoryRouter initialEntries={[`/consultant/clients/${clientId}/home`]}>
      <Routes>
        <Route
          path="/consultant/clients/:clientId/*"
          element={
            <ClientOrgShell>
              <div>client home body</div>
            </ClientOrgShell>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  api.getMeContext.mockResolvedValue({
    actor_type: 'consultant',
    destination: '/consultant',
  });
  api.getClientWorkspaceContext.mockResolvedValue(CLIENT_CONTEXT);
  api.getConsultantProfile.mockResolvedValue({ company_name: 'Acme Consulting' });
  api.listConsultantClients.mockResolvedValue({
    clients: [
      { id: 'client-1', client_name: 'Quayside Energy', status: 'active' },
      { id: 'client-2', client_name: 'Granite Distribution', status: 'active' },
    ],
  });
});

describe('Consultant client operating plane (CT03 parity + UX remediation)', () => {
  test('renders the SAME customer Organisation destinations under the client prefix', async () => {
    renderClientOrg();
    await screen.findByTestId('client-operating-context');

    const hrefs = Array.from(document.querySelectorAll('nav a')).map(
      (a) => a.getAttribute('href'),
    );
    expect(hrefs).toContain('/consultant/clients/client-1/home');
    expect(hrefs).toContain('/consultant/clients/client-1/documents');
    expect(hrefs).toContain('/consultant/clients/client-1/processing');
    expect(hrefs).toContain('/consultant/clients/client-1/emissions');
    expect(hrefs).toContain('/consultant/clients/client-1/reports');
    expect(hrefs).toContain('/consultant/clients/client-1/issues');
    expect(hrefs).toContain('/consultant/clients/client-1/organization');
    expect(hrefs).toContain('/consultant/clients/client-1/messaging');
    // Prefixes are client-scoped: no un-prefixed customer destination is offered.
    expect(hrefs).not.toContain('/documents');
  });

  test('does not offer Billing in a managed client context (PD-6)', async () => {
    renderClientOrg();
    await screen.findByTestId('client-operating-context');

    const billing = Array.from(document.querySelectorAll('nav a')).filter((a) =>
      /billing/i.test(a.getAttribute('href') || ''),
    );
    expect(billing).toHaveLength(0);
  });

  test('gives EXACTLY ONE primary, textual return path to the Consultant Plane (UX-06/AC-06)', async () => {
    renderClientOrg();
    await screen.findByTestId('client-operating-context');

    // CT-CONSULTANT-PLATFORM-CLOSURE-01 §11 — the client plane exposes EXACTLY
    // ONE return path to the Consultant Plane: the context bar's "← Back to
    // Consultant". The shared nav's plain "Consultant" hub entry is REMOVED in
    // the client plane (it renders only on the firm plane), so the return path is
    // never duplicated as a second nav item.
    const back = screen.getAllByText(/back to consultant/i);
    expect(back).toHaveLength(1);
    expect(back[0].closest('a')).toHaveAttribute('href', '/consultant');
    // Exactly one anchor targets the Consultant Plane root — the context bar. The
    // shared nav contributes none in the client plane (nav-cleanup, supersedes
    // the earlier UX-NAV-01A "keep a plain hub entry" rationale).
    const hrefs = Array.from(document.querySelectorAll('a')).map((a) => a.getAttribute('href'));
    expect(hrefs.filter((h) => h === '/consultant')).toHaveLength(1);
  });

  test('states the ACTOR (consultant firm) and SUBJECT (client) unambiguously (UX-02/AC-03/AC-04)', async () => {
    renderClientOrg();
    const bar = await screen.findByTestId('client-operating-context');

    expect(bar).toHaveTextContent('Consultant');
    expect(bar).toHaveTextContent('Acme Consulting');
    expect(bar).toHaveTextContent('Working on');
    expect(bar).toHaveTextContent('Quayside Energy');
    expect(bar).toHaveTextContent('Consultant-managed');
    // The consultant is never presented as the client.
    expect(bar).not.toHaveTextContent(/current organization/i);
  });

  test('does NOT offer a switch-client control inside the workspace (UX-05/AC-07)', async () => {
    renderClientOrg();
    await screen.findByTestId('client-operating-context');

    // CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A — a client is chosen in the
    // Consultant Plane (Clients → Open workspace). The operating plane DISPLAYS
    // context only; it must never re-offer a client selector.
    expect(screen.queryByLabelText(/switch client/i)).toBeNull();
    expect(screen.queryByText(/switch client/i)).toBeNull();
  });

  test('persists the selected client for the shared page components (PD-9)', async () => {
    renderClientOrg('client-7');
    await waitFor(() =>
      expect(localStorage.getItem('v3_consultant_active_client')).toBe('client-7'),
    );
  });

  test('renders the client body inside the shared shell', async () => {
    renderClientOrg();
    expect(await screen.findByText('client home body')).toBeInTheDocument();
  });

  test('resolves the client context from the URL, not from local state', async () => {
    renderClientOrg('client-9');
    await waitFor(() =>
      expect(api.getClientWorkspaceContext).toHaveBeenCalledWith('client-9'),
    );
  });

  test('shows a controlled denial (never data) when the client is not authorised (security)', async () => {
    api.getClientWorkspaceContext.mockRejectedValue(new Error('Forbidden'));
    renderClientOrg('client-9');
    expect(await screen.findByText(/client not available/i)).toBeInTheDocument();
    expect(screen.queryByText('client home body')).not.toBeInTheDocument();
  });
});
