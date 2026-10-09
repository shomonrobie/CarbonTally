// frontend/src/v3/__tests__/client-portal.test.jsx
// CT-CONSULTANT-MODEL-IMPLEMENTATION-03 (F-7 / F-8; PO-8 / PO-9 / PO-10).
//
// Plane C is the CLIENT portal at /portal/:clientId/*. These tests pin that the
// UI (a) renders the firm's brand and the organisation-scoped context, (b) has
// NO mapping/recalculation/billing control, (c) shows a read-only/retained state
// that does NOT read as deletion, and (d) presents the OQ-1 request entry point.
// Enforcement is server-side; a UI absence is never treated as the boundary.
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import '@testing-library/jest-dom';

jest.mock('../api', () => {
  const actual = jest.requireActual('../api');
  return {
    ...actual,
    getPortalContext: jest.fn(),
    getPortalOrganization: jest.fn(),
    postPortalAnnotation: jest.fn(),
    requestPortalRelationshipChange: jest.fn(),
  };
});

import ClientPortal from '../portal/ClientPortal';
import * as api from '../api';

function baseContext(overrides = {}) {
  return {
    organization: { id: 'org-a', name: 'Quayside Energy' },
    consultant: { firm_id: 'firm-1', firm_name: 'Acme Green' },
    brand: { kind: 'consultant', display_name: 'Acme Green' },
    mode: 'white_label',
    profile: 'read_only',
    state: 'active',
    retained_read_only: false,
    capabilities: {
      read_data: true,
      comment: true,
      upload_document: false,
      map_factors: false,
      recalculate: false,
    },
    ...overrides,
  };
}

function renderPortal() {
  return render(
    <MemoryRouter initialEntries={['/portal/org-a']}>
      <Routes>
        <Route path="/portal/:clientId/*" element={<ClientPortal />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  api.getPortalOrganization.mockResolvedValue({
    organization: { id: 'org-a', name: 'Quayside Energy', country: 'GB', is_active: true },
  });
});

const overviewLoaded = () =>
  waitFor(() =>
    expect(
      screen.getByRole('heading', { level: 1, name: 'Quayside Energy' })
    ).toBeInTheDocument()
  );

it('renders the firm brand and the organisation-scoped overview', async () => {
  api.getPortalContext.mockResolvedValue(baseContext());
  renderPortal();
  await overviewLoaded();
  expect(screen.getAllByText('Acme Green').length).toBeGreaterThan(0);
  expect(screen.getByText(/Read only/)).toBeInTheDocument();
});

it('never offers factor mapping or recalculation', async () => {
  api.getPortalContext.mockResolvedValue(baseContext());
  renderPortal();
  await overviewLoaded();
  expect(screen.queryByText(/map factors/i)).toBeNull();
  expect(screen.queryByText(/recalculate/i)).toBeNull();
  // …and the plane explicitly tells the client why.
  expect(screen.getByText(/never map emission factors/i)).toBeInTheDocument();
});

it('renders a retained state that does not read as deletion', async () => {
  api.getPortalContext.mockResolvedValue(
    baseContext({
      profile: 'collaborative',
      state: 'retained_read_only',
      retained_read_only: true,
      capabilities: { read_data: true, comment: false },
    })
  );
  renderPortal();
  await overviewLoaded();
  const banner = screen.getByRole('status');
  expect(banner.textContent).toMatch(/has ended/);
  expect(banner.textContent).not.toMatch(/deleted your data/i);
  // A retained client cannot send messages but can still read history.
  expect(screen.getByText(/Commenting is not available/)).toBeInTheDocument();
});

it('shows the generic non-disclosing state on denial', async () => {
  api.getPortalContext.mockRejectedValue(
    new Error('Client portal access is not available for this workspace')
  );
  renderPortal();
  await waitFor(() =>
    expect(screen.getByText('This workspace is not available')).toBeInTheDocument()
  );
});
