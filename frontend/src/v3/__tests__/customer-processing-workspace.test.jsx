// frontend/src/v3/__tests__/customer-processing-workspace.test.jsx
// CL-54 — the customer processing workspace renders the source/data panes and
// exposes the org-scoped stage actions. Approve/Reject only appears for
// owner/admin (D5) on a decidable item.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
}));

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: jest.fn(), getUser: jest.fn() } },
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

const BASE_WORKSPACE = {
  item: {
    id: 'item-1',
    file_name: 'electricity_invoice.pdf',
    file_id: 'file-1',
    status: 'extracted',
    page_count: 1,
  },
  batch: { id: 'batch-1', organization_id: 'org-1', status: 'in_progress' },
  source: { viewer_url: 'https://signed/viewer', file_name: 'electricity_invoice.pdf', ocr_suggestions: { activity: 'Electricity', quantity: 12500, unit: 'kWh' } },
  data: {
    extracted_data: { activity: 'Electricity', quantity: 12500, unit: 'kWh' },
    mapped_data: {},
    calculated_emissions_kg_co2e: null,
  },
  status: { status: 'extracted' },
  issues: [],
  workflow: { stages: [], allowed_transitions: [] },
};

const CALCULATED_WORKSPACE = {
  ...BASE_WORKSPACE,
  item: { ...BASE_WORKSPACE.item, status: 'calculated', calculated_emissions_kg_co2e: 2212.5 },
  data: {
    ...BASE_WORKSPACE.data,
    mapped_data: { factor_id: 'f1', activity_type: 'Electricity', scope: 'Scope 2' },
    calculated_emissions_kg_co2e: 2212.5,
  },
};

beforeEach(() => {
  jest.clearAllMocks();
  api.getProcessingJobs.mockResolvedValue({ jobs: [] });
  api.getDocumentEmissions.mockResolvedValue({ emissions: [] });
  api.getProcessingMappingOptions.mockResolvedValue({ factors: [], no_factors_reason: '' });
});

describe('Customer processing workspace (CL-54)', () => {
  test('renders the workspace panes for an editable item', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'member' });
    api.getProcessingItemWorkspace.mockResolvedValue(BASE_WORKSPACE);
    render(<ProcessingItemWorkspace itemId="item-1" />);
    await waitFor(() => expect(screen.getByText('Processing workspace')).toBeInTheDocument());
    expect(screen.getByText('electricity_invoice.pdf')).toBeInTheDocument();
    expect(screen.getByText('Extraction')).toBeInTheDocument();
    expect(screen.getByText('Mapping')).toBeInTheDocument();
    expect(screen.getByText('Validation')).toBeInTheDocument();
    expect(screen.getByText('Save extraction')).toBeInTheDocument();
    // A member is not an approver: every "Approve" button (workflow nav step
    // only) is disabled — there is no actionable Approve/Reject in the actions.
    const approveButtons = screen.getAllByRole('button', { name: /^approve/i });
    expect(approveButtons.length).toBeGreaterThanOrEqual(1);
    approveButtons.forEach((b) => expect(b).toBeDisabled());
    expect(screen.queryByRole('button', { name: /^reject/i })).toBeNull();
  });

  test('shows the calculated result when present', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'owner' });
    api.getProcessingItemWorkspace.mockResolvedValue(CALCULATED_WORKSPACE);
    render(<ProcessingItemWorkspace itemId="item-1" />);
    await waitFor(() => expect(screen.getByText('Calculated result')).toBeInTheDocument());
    expect(screen.getAllByText(/2212\.5 kg CO2e/).length).toBeGreaterThanOrEqual(1);
  });

  test('owner/admin sees Approve/Reject on a decidable item (D5)', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'owner' });
    api.getProcessingItemWorkspace.mockResolvedValue(CALCULATED_WORKSPACE);
    render(<ProcessingItemWorkspace itemId="item-1" />);
    await waitFor(() => expect(screen.getByText('Calculated result')).toBeInTheDocument());
    // The workflow nav includes an "Approve" step button; the action area adds
    // the real Approve/Reject decision buttons.
    const approveButtons = screen.getAllByRole('button', { name: /^approve/i });
    const rejectButtons = screen.getAllByRole('button', { name: /^reject/i });
    expect(approveButtons.length).toBeGreaterThanOrEqual(1);
    expect(rejectButtons.length).toBeGreaterThanOrEqual(1);
  });

  test('CL-44 — approved customer factors appear in the mapping picker with the source made clear', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'member' });
    api.getProcessingItemWorkspace.mockResolvedValue(BASE_WORKSPACE);
    api.getProcessingMappingOptions.mockResolvedValue({
      factors: [
        { id: 'sys-1', activity_type: 'Electricity', unit: 'kWh', factor_source: 'DEFRA', reporting_year: 2025 },
      ],
      customer_factors: [
        { id: 'cust-2', activity_type: 'Electricity', unit: 'kWh', factor_source: 'CUSTOMER', factor_kind: 'customer_factor', version: 2, reporting_year: 2025 },
      ],
      no_factors_reason: '',
      spend_suggestion: null,
    });
    render(<ProcessingItemWorkspace itemId="item-1" />);
    await waitFor(() => expect(screen.getByText('Mapping')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /Load factor options/i }));
    // The customer factor is listed first (D-cf-5 precedence) and is labelled
    // with its source and version so the selection is never ambiguous.
    await waitFor(() => {
      const options = screen.getAllByRole('option');
      expect(options.some((o) => /Customer factor v2/i.test(o.textContent))).toBe(true);
      const custIndex = options.findIndex((o) => /Customer factor v2/i.test(o.textContent));
      const sysIndex = options.findIndex((o) => /DEFRA 2025/i.test(o.textContent));
      expect(custIndex).toBeGreaterThan(0); // after the placeholder
      expect(custIndex).toBeLessThan(sysIndex); // precedence: customer first
    });
  });

  test('CL-47 — a spend activity with no factors shows an actionable path instead of a dead-end', async () => {
    api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'member' });
    api.getProcessingItemWorkspace.mockResolvedValue(BASE_WORKSPACE);
    api.getProcessingMappingOptions.mockResolvedValue({
      factors: [],
      customer_factors: [],
      no_factors_reason: 'Spend-based activity (GBP) has no emission factor in the current factor set…',
      spend_suggestion: {
        kind: 'spend_based',
        activity: 'Purchased goods',
        unit: 'GBP',
        action: 'create_customer_factor',
      },
    });
    render(<ProcessingItemWorkspace itemId="item-1" />);
    await waitFor(() => expect(screen.getByText('Mapping')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /Load factor options/i }));
    // The supported spend workflow is surfaced explicitly (create an approved
    // customer factor) rather than an unexplained empty list.
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Create a spend-based customer factor/i })).toBeInTheDocument(),
    );
    expect(screen.getByText(/Spend-based activity/)).toBeInTheDocument();
  });
});
