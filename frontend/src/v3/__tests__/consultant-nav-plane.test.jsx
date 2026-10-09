// frontend/src/v3/__tests__/consultant-nav-plane.test.jsx
// CT-CONSULTANT-PLATFORM-CLOSURE-01 §11 — client-plane navigation cleanup.
//
// Pins that the shared D18 navigation exposes the "Consultant" hub entry ONLY on
// the consultant FIRM plane. Inside a managed client's operating plane (a
// ``navPrefix`` is set) that entry is removed, so the client context bar's single
// "← Back to Consultant" is the one and only return path — no duplicated hub
// item, no second affordance competing with the context bar.
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
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
  };
});

import V3Layout from '../components/V3Layout';
import * as api from '../api';

// The shared D18 header nav (never the tablet/mobile tray).
const navHrefs = () =>
  Array.from(document.querySelectorAll('nav.v3-nav-links a')).map((a) =>
    a.getAttribute('href'),
  );

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  api.getMeContext.mockResolvedValue({
    actor_type: 'consultant',
    destination: '/consultant',
  });
});

test('consultant FIRM plane keeps the single Consultant hub entry', async () => {
  render(
    <MemoryRouter initialEntries={['/consultant']}>
      <V3Layout>
        <div>firm body</div>
      </V3Layout>
    </MemoryRouter>,
  );
  await screen.findByText('firm body');
  await screen.findByRole('link', { name: 'Consultant' });
  expect(navHrefs()).toContain('/consultant');
});

test('client operating plane removes the Consultant hub entry (one return path)', async () => {
  api.getClientWorkspaceContext.mockResolvedValue({
    client: {
      id: 'client-1',
      client_name: 'Quayside Energy',
      organization_id: 'org-1',
      status: 'active',
    },
    organization: { id: 'org-1', name: 'Quayside Energy' },
  });
  render(
    <MemoryRouter initialEntries={['/consultant/clients/client-1/home']}>
      <V3Layout navPrefix="/consultant/clients/client-1" clientId="client-1">
        <div>client body</div>
      </V3Layout>
    </MemoryRouter>,
  );
  // Client-scoped Organisation destinations are still offered (the shared nav
  // adopts the client prefix) ...
  await waitFor(() =>
    expect(navHrefs()).toContain('/consultant/clients/client-1/home'),
  );
  // ... but the plain Consultant hub item is NOT (the nav does not duplicate the
  // context bar's single return path).
  expect(navHrefs()).not.toContain('/consultant');
});
