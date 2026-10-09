// frontend/src/v3/__tests__/manual-processing-coverage.test.jsx
// CT-MP-SUB-004 — Manual Processing commercial/entitlement UI/UX
// (CT-UX-MP-SUB-003 acceptance criteria §10).
//
// Covers the two ADDITIVE caller-scoped surfaces plus the Admin commercial
// coverage split:
//   * customer   — effective service state only; never internal consultant data;
//   * consultant — its OWN firm's purchased coverage + selected-client capacity;
//   * admin      — commercial coverage visibly separate from operational routing.
//
// Everything is mocked at the api boundary; no network and no database access.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('react-router-dom', () => ({
  Link: ({ to, children, ...rest }) => <a href={to} {...rest}>{children}</a>,
}));

jest.mock('../api', () => ({
  getMyManualProcessing: jest.fn(),
  resolveV3Organization: jest.fn(),
  getConsultantManualProcessingCoverage: jest.fn(),
  allocateConsultantManualProcessingClient: jest.fn(),
  releaseConsultantManualProcessingAllocation: jest.fn(),
  getAdminManualProcessingCoverage: jest.fn(),
  getAdminManualProcessingClientState: jest.fn(),
  allocateAdminManualProcessingClient: jest.fn(),
  releaseAdminManualProcessingAllocation: jest.fn(),
  // F-11 — read-only searchable client-organisation lookup.
  searchAdminManualProcessingOrganizations: jest.fn(),
}));

import * as api from '../api';
import ManualProcessingPage from '../customer/ManualProcessingPage';
import ConsultantCoverageTab from '../consultant/ManualProcessingCoverageTab';
import AdminCoverageTab from '../ops/ManualProcessingCoverageTab';

const ORG = { id: 'org-a', name: 'Quayside Energy' };

function customerState(overrides = {}) {
  return {
    organization_id: 'org-a',
    status: 'not_included',
    coverage_sources: [],
    direct_entitled: false,
    sponsored_entitled: false,
    effective_entitled: false,
    consultant: null,
    processing_mode: null,
    governance: { enabled: false },
    processing_entity: { configured: false, processing_entity_id: null },
    operational_status: 'not_yet_configured',
    effective: { enabled: false, effective: false, outcome: 'not_entitled' },
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  api.resolveV3Organization.mockResolvedValue(ORG);
});

// ---------------------------------------------------------------------------
// Customer — §3 + §10 criteria 9, 10, 11
// ---------------------------------------------------------------------------

describe('CT-MP-SUB-004 customer Manual Processing surface', () => {
  test('an unentitled customer is told why, and offered the plans path', async () => {
    api.getMyManualProcessing.mockResolvedValue(customerState());
    render(<ManualProcessingPage />);

    expect(await screen.findByText('NOT INCLUDED')).toBeInTheDocument();
    expect(
      screen.getByText(/not included in your current commercial coverage/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: /view available plans/i }),
    ).toHaveAttribute('href', '/billing');
  });

  test('direct coverage reports the subscription as the source', async () => {
    api.getMyManualProcessing.mockResolvedValue(
      customerState({
        status: 'available',
        coverage_sources: ['direct'],
        direct_entitled: true,
        effective_entitled: true,
        processing_mode: 'manual',
      }),
    );
    render(<ManualProcessingPage />);

    expect((await screen.findAllByText('AVAILABLE')).length).toBeGreaterThan(0);
    expect(screen.getByText('Included in your subscription')).toBeInTheDocument();
    expect(screen.getByText('Direct subscription')).toBeInTheDocument();
  });

  test('sponsored coverage names the consultant and never its capacity', async () => {
    api.getMyManualProcessing.mockResolvedValue(
      customerState({
        status: 'available',
        coverage_sources: ['sponsored'],
        sponsored_entitled: true,
        effective_entitled: true,
        processing_mode: 'manual',
        consultant: { company_name: 'ABC Consulting Ltd' },
      }),
    );
    const { container } = render(<ManualProcessingPage />);

    expect((await screen.findAllByText('AVAILABLE')).length).toBeGreaterThan(0);
    expect(screen.getByText('ABC Consulting Ltd')).toBeInTheDocument();
    expect(
      screen.getByText('Provided through your consultant'),
    ).toBeInTheDocument();
    // §10 criterion 11 — no internal consultant commercial state is exposed.
    const text = container.textContent.toLowerCase();
    for (const leaked of ['capacity', 'allocated', 'allocation', 'firm_id']) {
      expect(text).not.toContain(leaked);
    }
  });

  test('direct + sponsored is one service, not two', async () => {
    api.getMyManualProcessing.mockResolvedValue(
      customerState({
        status: 'available',
        coverage_sources: ['direct', 'sponsored'],
        direct_entitled: true,
        sponsored_entitled: true,
        effective_entitled: true,
        processing_mode: 'manual',
        consultant: { company_name: 'ABC Consulting Ltd' },
      }),
    );
    render(<ManualProcessingPage />);

    expect(await screen.findByText(/your coverage includes/i)).toBeInTheDocument();
    expect(screen.getByText('Direct subscription')).toBeInTheDocument();
    expect(screen.getByText('Consultant-sponsored coverage')).toBeInTheDocument();
    expect(screen.getAllByText('AVAILABLE').length).toBeGreaterThan(0);
  });

  test('entitled but not configured is NEVER shown as not subscribed', async () => {
    api.getMyManualProcessing.mockResolvedValue(
      customerState({
        status: 'available',
        coverage_sources: ['direct'],
        direct_entitled: true,
        effective_entitled: true,
        processing_mode: 'manual',
        operational_status: 'not_yet_configured',
      }),
    );
    render(<ManualProcessingPage />);

    expect((await screen.findAllByText('AVAILABLE')).length).toBeGreaterThan(0);
    expect(screen.queryByText('NOT INCLUDED')).not.toBeInTheDocument();
    expect(screen.getByText('NOT YET CONFIGURED')).toBeInTheDocument();
    expect(
      screen.getByText(/operational processing configuration is not yet complete/i),
    ).toBeInTheDocument();
  });

  test('a load failure offers a retry, not an empty success state', async () => {
    api.getMyManualProcessing.mockRejectedValue(new Error('Unable to load.'));
    render(<ManualProcessingPage />);

    expect(await screen.findByText('Unable to load.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Consultant — §4 + §7 + §10 criteria 5, 6, 7, 8, 14
// ---------------------------------------------------------------------------

function consultantCoverage(overrides = {}) {
  return {
    consultant_id: 'firm-1',
    company_name: 'Acme Consultants',
    enabled: true,
    mode: 'SELECTED_CLIENTS',
    capacity: 10,
    allocated: 2,
    available: 8,
    over_allocated: false,
    plan_code: 'consultant-mp',
    plan_version: 1,
    eligible_clients: [
      { organization_id: 'org-a', name: 'Quayside Energy' },
      { organization_id: 'org-b', name: 'Granite Distribution' },
    ],
    unallocated_eligible_clients: [
      { organization_id: 'org-b', name: 'Granite Distribution' },
    ],
    covered_clients: [
      { organization_id: 'org-a', name: 'Quayside Energy' },
      { organization_id: 'org-d', name: 'Harbour Foods' },
    ],
    allocations: [
      {
        id: 'alloc-1', organization_id: 'org-a', name: 'Quayside Energy',
        state: 'active', reason: null, allocated_at: '2026-09-01T00:00:00Z', released_at: null,
      },
      {
        id: 'alloc-2', organization_id: 'org-d', name: 'Harbour Foods',
        state: 'active', reason: null, allocated_at: '2026-09-02T00:00:00Z', released_at: null,
      },
      {
        id: 'alloc-0', organization_id: 'org-z', name: 'Former Client',
        state: 'released', reason: null, allocated_at: '2026-08-01T00:00:00Z', released_at: '2026-08-10T00:00:00Z',
      },
    ],
    ...overrides,
  };
}

describe('CT-MP-SUB-004 consultant coverage surface', () => {
  test('SELECTED_CLIENTS shows purchased capacity, remaining capacity and covered clients', async () => {
    api.getConsultantManualProcessingCoverage.mockResolvedValue(consultantCoverage());
    render(<ConsultantCoverageTab canManageClients />);

    expect((await screen.findAllByText('SELECTED CLIENTS')).length).toBeGreaterThan(0);
    expect(screen.getByText('10 clients')).toBeInTheDocument();
    expect(screen.getByText('2 / 10')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    // Covered clients only — a released allocation is history, not coverage.
    expect(screen.getByText('Quayside Energy')).toBeInTheDocument();
    expect(screen.getByText('Harbour Foods')).toBeInTheDocument();
    expect(screen.queryByText('Former Client')).not.toBeInTheDocument();
  });

  test('the capacity meter is exposed to assistive technology', async () => {
    api.getConsultantManualProcessingCoverage.mockResolvedValue(consultantCoverage());
    render(<ConsultantCoverageTab canManageClients />);
    const meter = await screen.findByRole('progressbar');
    expect(meter).toHaveAttribute('aria-valuenow', '2');
    expect(meter).toHaveAttribute('aria-valuemax', '10');
  });

  test('allocating an eligible client posts only the organisation id', async () => {
    api.getConsultantManualProcessingCoverage.mockResolvedValue(consultantCoverage());
    api.allocateConsultantManualProcessingClient.mockResolvedValue({});
    render(<ConsultantCoverageTab canManageClients />);

    fireEvent.change(await screen.findByLabelText(/eligible client/i), {
      target: { value: 'org-b' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Allocate' }));

    await waitFor(() =>
      expect(api.allocateConsultantManualProcessingClient).toHaveBeenCalledWith({
        organization_id: 'org-b',
      }),
    );
    // The firm is never named by the browser — it is resolved server-side.
    expect(
      Object.keys(api.allocateConsultantManualProcessingClient.mock.calls[0][0]),
    ).toEqual(['organization_id']);
  });

  test('releasing an allocation targets the allocation id', async () => {
    api.getConsultantManualProcessingCoverage.mockResolvedValue(consultantCoverage());
    api.releaseConsultantManualProcessingAllocation.mockResolvedValue({});
    render(<ConsultantCoverageTab canManageClients />);

    const releases = await screen.findAllByRole('button', { name: 'Release' });
    fireEvent.click(releases[0]);

    await waitFor(() =>
      expect(api.releaseConsultantManualProcessingAllocation).toHaveBeenCalledWith('alloc-1'),
    );
  });

  test('exhausted capacity explains the consequence rather than hiding it', async () => {
    api.getConsultantManualProcessingCoverage.mockResolvedValue(
      consultantCoverage({ allocated: 10, available: 0 }),
    );
    render(<ConsultantCoverageTab canManageClients />);

    expect(
      await screen.findByText(/no allocation capacity remains/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Allocate' })).not.toBeInTheDocument();
  });

  test('ALL_ELIGIBLE_CLIENTS covers automatically and allocates nothing', async () => {
    api.getConsultantManualProcessingCoverage.mockResolvedValue(
      consultantCoverage({ mode: 'ALL_ELIGIBLE_CLIENTS', capacity: null, allocated: 0 }),
    );
    render(<ConsultantCoverageTab canManageClients />);

    expect((await screen.findAllByText('ALL ELIGIBLE CLIENTS')).length).toBeGreaterThan(0);
    expect(screen.getAllByText('Automatically covered').length).toBeGreaterThan(0);
    expect(screen.queryByRole('button', { name: 'Allocate' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /view eligible clients/i }));
    expect(screen.getByText('Granite Distribution')).toBeInTheDocument();
  });

  test('a firm without active coverage gets the explicit empty state', async () => {
    api.getConsultantManualProcessingCoverage.mockResolvedValue(
      consultantCoverage({ enabled: false, mode: null, capacity: null, allocated: 0, available: null }),
    );
    render(<ConsultantCoverageTab canManageClients />);

    expect(
      await screen.findByText(/no manual processing consultant coverage is currently active/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/subscription coverage will appear here when configured/i),
    ).toBeInTheDocument();
  });

  test('without the manage-clients permission the write control is disabled', async () => {
    api.getConsultantManualProcessingCoverage.mockResolvedValue(consultantCoverage());
    render(<ConsultantCoverageTab canManageClients={false} />);

    fireEvent.change(await screen.findByLabelText(/eligible client/i), {
      target: { value: 'org-b' },
    });
    expect(screen.getByRole('button', { name: 'Allocate' })).toBeDisabled();
  });

  test('a rejected allocation shows the explicit allocation error state', async () => {
    api.getConsultantManualProcessingCoverage.mockResolvedValue(consultantCoverage());
    api.allocateConsultantManualProcessingClient.mockRejectedValue(
      new Error('This client already has an active sponsored coverage allocation.'),
    );
    render(<ConsultantCoverageTab canManageClients />);

    fireEvent.change(await screen.findByLabelText(/eligible client/i), {
      target: { value: 'org-b' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Allocate' }));

    expect(
      await screen.findByText(/unable to allocate this client/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/allocation capacity is exhausted/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Admin — §2 + §7 + §10 criteria 1, 2, 3, 4, 12, 13, 14
// ---------------------------------------------------------------------------

function adminCoverage(coverageOverrides = {}) {
  return {
    consultant_id: 'firm-1',
    company_name: 'Acme Consultants',
    coverage: {
      firm_id: 'firm-1',
      firm_organization_id: 'firm-org',
      enabled: true,
      mode: 'SELECTED_CLIENTS',
      capacity: 10,
      allocated: 1,
      available: 9,
      over_allocated: false,
      plan_code: 'consultant-mp',
      plan_version: 1,
      eligible_clients: ['org-a', 'org-b'],
      unallocated_eligible_clients: ['org-b'],
      allocations: [
        {
          id: 'alloc-1', organization_id: 'org-a', consultant_client_id: 'cc-a',
          state: 'active', reason: null, allocated_at: '2026-09-01T00:00:00Z', released_at: null,
        },
      ],
      ...coverageOverrides,
    },
  };
}

const ADMIN_CLIENT_STATE = {
  organization_id: 'org-a',
  direct: { entitled: true, source: 'feature', plan_code: 'mp' },
  sponsored: {
    entitled: true, firm_id: 'firm-1', mode: 'SELECTED_CLIENTS',
    reason: 'selected_allocated', allocated: 1, available: 9, over_allocated: false,
  },
  effective_entitlement: {
    entitled: true, source: 'direct+sponsored',
    sponsored_mode: 'SELECTED_CLIENTS', sponsored_reason: 'selected_allocated',
  },
  relationship: { consultant_client_id: 'cc-a', consultant_firm_id: 'firm-1' },
  governance: {
    enabled: true, source_level: 'explicit',
    source_scope_type: 'organization', source_scope_id: 'org-a',
  },
  effective: {
    entitled: true, enabled: true, effective: true, configured: true,
    processing_entity_id: 'pe-1', outcome: 'routable', entitlement_source: 'direct+sponsored',
  },
};

describe('CT-MP-SUB-004 admin commercial coverage surface', () => {
  test('firm coverage separates commercial coverage from operational routing', async () => {
    api.getAdminManualProcessingCoverage.mockResolvedValue(adminCoverage());
    render(<AdminCoverageTab canManage />);

    fireEvent.change(screen.getByLabelText(/consultant firm id/i), {
      target: { value: 'firm-1' },
    });
    fireEvent.click(screen.getByRole('button', { name: /load coverage/i }));

    expect((await screen.findAllByText('SELECTED CLIENTS')).length).toBeGreaterThan(0);
    expect(screen.getByText('10 clients')).toBeInTheDocument();
    expect(screen.getByText('1 / 10')).toBeInTheDocument();
    expect(screen.getByText('9')).toBeInTheDocument();
    expect(screen.getByText('org-a')).toBeInTheDocument();
    expect(await screen.findByRole('progressbar')).toBeInTheDocument();
    // §8 — the distinction is stated, not implied.
    expect(
      screen.getByText(/deliberately separate from the operational routing view/i),
    ).toBeInTheDocument();
  });

  test('a firm with no coverage configured gets the admin empty state', async () => {
    api.getAdminManualProcessingCoverage.mockResolvedValue(
      adminCoverage({
        enabled: false, mode: null, capacity: null, allocated: 0,
        available: null, allocations: [], unallocated_eligible_clients: [],
      }),
    );
    render(<AdminCoverageTab canManage />);

    fireEvent.change(screen.getByLabelText(/consultant firm id/i), {
      target: { value: 'firm-1' },
    });
    fireEvent.click(screen.getByRole('button', { name: /load coverage/i }));

    expect(
      await screen.findByText(/no consultant coverage configured for this organization/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/configure the firm's commercial coverage first/i),
    ).toBeInTheDocument();
  });

  test('allocating posts the firm, the client and the reason', async () => {
    api.getAdminManualProcessingCoverage.mockResolvedValue(adminCoverage());
    api.allocateAdminManualProcessingClient.mockResolvedValue({});
    render(<AdminCoverageTab canManage />);

    fireEvent.change(screen.getByLabelText(/consultant firm id/i), {
      target: { value: 'firm-1' },
    });
    fireEvent.click(screen.getByRole('button', { name: /load coverage/i }));
    fireEvent.change(await screen.findByLabelText(/eligible client/i), {
      target: { value: 'org-b' },
    });
    fireEvent.change(screen.getByLabelText(/reason/i), {
      target: { value: 'onboarding package' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Allocate' }));

    await waitFor(() =>
      expect(api.allocateAdminManualProcessingClient).toHaveBeenCalledWith({
        consultant_id: 'firm-1',
        organization_id: 'org-b',
        reason: 'onboarding package',
      }),
    );
  });

  test('releasing an allocation targets the allocation id', async () => {
    api.getAdminManualProcessingCoverage.mockResolvedValue(adminCoverage());
    api.releaseAdminManualProcessingAllocation.mockResolvedValue({});
    render(<AdminCoverageTab canManage />);

    fireEvent.change(screen.getByLabelText(/consultant firm id/i), {
      target: { value: 'firm-1' },
    });
    fireEvent.click(screen.getByRole('button', { name: /load coverage/i }));
    // F-11 — a release is state-changing and not reversible, so it now asks for
    // an explicit confirmation before issuing the write.
    fireEvent.click(await screen.findByRole('button', { name: 'Release' }));
    fireEvent.click(await screen.findByRole('button', { name: /confirm release/i }));

    await waitFor(() =>
      expect(api.releaseAdminManualProcessingAllocation).toHaveBeenCalledWith('alloc-1'),
    );
  });

  test('per-client state keeps every concept distinct', async () => {
    api.getAdminManualProcessingClientState.mockResolvedValue(ADMIN_CLIENT_STATE);
    api.searchAdminManualProcessingOrganizations.mockResolvedValue({
      organizations: [{ id: 'org-a', name: 'Quayside Energy', is_active: true }],
      total: 1,
      limit: 20,
      offset: 0,
      q: 'quay',
    });
    render(<AdminCoverageTab canManage />);

    // F-11 — the operator searches by NAME; no raw id is typed.
    fireEvent.change(screen.getByLabelText(/^organisation$/i), {
      target: { value: 'quay' },
    });
    fireEvent.click(
      await screen.findByRole('button', { name: /quayside energy/i }),
    );
    fireEvent.click(screen.getByRole('button', { name: /load client state/i }));

    await waitFor(() =>
      expect(api.getAdminManualProcessingClientState).toHaveBeenCalledWith('org-a'),
    );
    expect(
      await screen.findByText('Effective Manual Processing entitlement'),
    ).toBeInTheDocument();
    expect(screen.getByText('ENABLED')).toBeInTheDocument();
    expect(screen.getByText('CONFIGURED')).toBeInTheDocument();
    expect(screen.getByText(/direct\+sponsored/)).toBeInTheDocument();
    expect(screen.getByText(/never imply two separate/i)).toBeInTheDocument();
  });

  test('exhausted capacity is explained and the write control is not offered', async () => {
    api.getAdminManualProcessingCoverage.mockResolvedValue(
      adminCoverage({ allocated: 10, available: 0 }),
    );
    render(<AdminCoverageTab canManage />);

    fireEvent.change(screen.getByLabelText(/consultant firm id/i), {
      target: { value: 'firm-1' },
    });
    fireEvent.click(screen.getByRole('button', { name: /load coverage/i }));

    expect(
      await screen.findByText(/no allocation capacity remains/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Allocate' })).not.toBeInTheDocument();
  });

  test('a failed write shows the explicit allocation error state', async () => {
    api.getAdminManualProcessingCoverage.mockResolvedValue(adminCoverage());
    api.allocateAdminManualProcessingClient.mockRejectedValue(
      new Error('Selected-client capacity is exhausted.'),
    );
    render(<AdminCoverageTab canManage />);

    fireEvent.change(screen.getByLabelText(/consultant firm id/i), {
      target: { value: 'firm-1' },
    });
    fireEvent.click(screen.getByRole('button', { name: /load coverage/i }));
    fireEvent.change(await screen.findByLabelText(/eligible client/i), {
      target: { value: 'org-b' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Allocate' }));

    expect(
      await screen.findByText(/unable to allocate this client/i),
    ).toBeInTheDocument();
  });
});
