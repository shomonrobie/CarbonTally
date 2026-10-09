// frontend/src/v3/__tests__/client-access-guard.test.jsx
// CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05.
//
// UI-reflection tests for the client-access ceiling on the ORGANISATION plane:
// a consultant-managed client's own user reaches the SAME surface a direct
// customer uses, but its master-data / upload affordances are bounded by the
// client access profile (server-enforced; these tests assert the UI hides them).
// The default (direct customer, consultant, staff) is unrestricted.
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getUser: jest.fn(), getSession: jest.fn(), signOut: jest.fn() } },
}));

jest.mock('../api', () => {
  const actual = jest.requireActual('../api');
  return {
    ...actual,
    getMeContext: jest.fn(),
    getClientWorkspaceContext: jest.fn(),
    listFacilities: jest.fn(),
    listAssets: jest.fn(),
    createFacility: jest.fn(),
    createAsset: jest.fn(),
    updateFacility: jest.fn(),
    updateAsset: jest.fn(),
    removeFacility: jest.fn(),
    removeAsset: jest.fn(),
  };
});

import FacilitiesTab from '../admin/FacilitiesTab';
import V3Layout from '../components/V3Layout';
import { ClientAccessProvider, useClientAccess } from '../clientAccess';
import * as api from '../api';

const ORG = { id: 'org-1', name: 'CT03-QA Managed Client' };
const FACILITY = {
  id: 'f-1', name: 'Birmingham Head Office', postcode: 'B1 1AA', country: 'GB', type: 'office',
};

const MANAGED = {
  profile: 'managed',
  state: 'active',
  capabilities: { edit_master_data: false, upload_document: false },
};

function CanProbe({ op }) {
  return <span data-testid="can">{String(useClientAccess().can(op))}</span>;
}

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  api.listFacilities.mockResolvedValue({ facilities: [FACILITY] });
  api.listAssets.mockResolvedValue({ assets: [] });
});

describe('ClientAccessProvider (presentation-only capability view)', () => {
  test('defaults to unrestricted when no client ceiling applies', () => {
    render(<CanProbe op="edit_master_data" />);
    expect(screen.getByTestId('can')).toHaveTextContent('true');
  });

  test('an explicit false capability is honoured', () => {
    render(
      <ClientAccessProvider value={MANAGED}>
        <CanProbe op="edit_master_data" />
      </ClientAccessProvider>,
    );
    expect(screen.getByTestId('can')).toHaveTextContent('false');
  });
});

describe('FacilitiesTab reflects the client-access ceiling', () => {
  test('a managed client sees no master-data write controls', async () => {
    render(
      <ClientAccessProvider value={MANAGED}>
        <FacilitiesTab organization={ORG} />
      </ClientAccessProvider>,
    );
    await waitFor(() => expect(screen.getByText('Birmingham Head Office')).toBeInTheDocument());
    expect(screen.queryByText('+ New facility')).not.toBeInTheDocument();
    expect(screen.queryByText('+ New asset')).not.toBeInTheDocument();
    expect(screen.getByText(/read-only for organisation master data/i)).toBeInTheDocument();
  });

  test('an unrestricted user keeps the master-data write controls', async () => {
    render(<FacilitiesTab organization={ORG} />);
    await waitFor(() => expect(screen.getByText('Birmingham Head Office')).toBeInTheDocument());
    expect(screen.getByText('+ New facility')).toBeInTheDocument();
    expect(screen.getByText('+ New asset')).toBeInTheDocument();
  });
});

describe('V3Layout user-facing branding', () => {
  test('shows "CarbonTally" and never a bare "V3" product tag', async () => {
    api.getMeContext.mockResolvedValue({
      actor_type: 'customer',
      destination: '/home',
      organization: { id: 'org-1', name: 'Direct Customer Ltd', role: 'owner' },
      client_access: null,
    });
    render(
      <MemoryRouter>
        <V3Layout>
          <div>page</div>
        </V3Layout>
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('CarbonTally')).toBeInTheDocument());
    expect(screen.queryByText('V3')).not.toBeInTheDocument();
  });
});
