// frontend/src/v3/__tests__/dr007-investor-display-fixes.test.jsx
// DR-007 — narrow regressions for two investor-facing display defects:
//   Issue 2: the workspace Calculation panel must show the Scope that the backend
//            carries on the calculated emissions row (mapped_data has no scope).
//   Issue 3: the customer review detail must show the Mapped activity that the
//            backend carries as mapped_data.activity (not only activity_type).
// Both use the real payload shapes observed in the Demo Lab R-A item
// (snapshot af640887…, emissions log eb88e764…, 2469.16978 kg CO2e, Natural gas).
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
  useParams: () => ({ itemId: 'item-1', id: 'item-1' }),
}));

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: jest.fn(), getUser: jest.fn() } },
}));

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

const api = jest.requireMock('../api');

// Real Demo Lab shapes: mapped_data carries activity/methodology but NOT scope;
// scope lives on the emissions row produced from the calculation snapshot.
const RA_ITEM = {
  id: 'item-1',
  file_name: 't3imp_uk-gas__ORG_022_british_gas_202511.pdf',
  file_id: 'file-1',
  status: 'calculated',
  page_count: 1,
};

const RA_WORKSPACE = {
  item: RA_ITEM,
  batch: { id: 'batch-1', organization_id: 'org-1', status: 'in_progress' },
  source: { viewer_url: null, file_name: RA_ITEM.file_name, ocr_suggestions: {} },
  data: {
    extracted_data: { activity: 'Natural gas', quantity: 12181.4, unit: 'kWh', supplier: 'Clear Power PLC' },
    mapped_data: { factor_id: 'b9d1ed06-7e4a-4c26-a91a-46f3fb45bda5', activity: 'Natural gas', methodology: 'selection_policy' },
    calculated_emissions_kg_co2e: 2469.16978,
  },
  status: { status: 'calculated' },
  issues: [],
  workflow: { stages: [], allowed_transitions: [] },
};

const RA_EMISSIONS = {
  emissions: [
    {
      id: 'eb88e764-b93a-4bd6-8b66-a24fd6e45ca9',
      scope: 'Scope 1',
      start_date: '2025-05-05',
      snapshot_id: 'af640887-5818-47ad-b351-1505ac049c32',
      calculated_kg_co2e: 2469.16978,
      activity: 'Natural gas',
    },
  ],
};

beforeEach(() => {
  jest.clearAllMocks();
  api.getProcessingJobs.mockResolvedValue({ jobs: [] });
  api.getProcessingMappingOptions.mockResolvedValue({ factors: [], no_factors_reason: '' });
  api.resolveV3Membership.mockResolvedValue({ org: { id: 'org-1' }, role: 'owner' });
});

describe('DR-007 investor-facing display fixes', () => {
  test('Issue 2 — workspace Calculation panel shows the scope from the calculated emissions row', async () => {
    api.getProcessingItemWorkspace.mockResolvedValue(RA_WORKSPACE);
    api.getDocumentEmissions.mockResolvedValue(RA_EMISSIONS);
    render(<ProcessingItemWorkspace itemId="item-1" />);
    await waitFor(() => expect(screen.getByText('Calculated result')).toBeInTheDocument());
    // The result is unchanged and the scope is no longer rendered as '-'.
    await waitFor(() => expect(screen.getAllByText(/Scope 1/).length).toBeGreaterThanOrEqual(1));
    expect(screen.queryByText(/Scope - · Methodology/)).toBeNull();
    expect(screen.getAllByText(/2469\.16978 kg CO2e/).length).toBeGreaterThanOrEqual(1);
  });

  test('Issue 3 — customer review detail shows Mapped activity from mapped_data.activity', async () => {
    api.getProcessingItemWorkspace.mockResolvedValue(RA_WORKSPACE);
    render(<ReviewDetailPage />);
    await waitFor(() => expect(screen.getByText('Mapped activity')).toBeInTheDocument());
    const row = screen.getByText('Mapped activity').closest('div');
    expect(row).not.toBeNull();
    expect(row.textContent).toContain('Natural gas');
    expect(row.textContent).not.toContain('—');
  });
});
