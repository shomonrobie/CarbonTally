// frontend/src/v3/__tests__/customer-factors-tab.test.jsx
// CL-43 — customer-factor version lifecycle is explicit in the UI: versions are
// visible, an approved factor can be given a new draft version, and a duplicate
// family/version create surfaces a clean conflict (never a 500).
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: jest.fn(), getUser: jest.fn() } },
}));

const api = jest.requireMock('../api');
jest.mock('../api', () => ({
  listCustomerFactors: jest.fn(),
  createCustomerFactor: jest.fn(),
  updateCustomerFactor: jest.fn(),
  approveCustomerFactor: jest.fn(),
  deactivateCustomerFactor: jest.fn(),
}));

import CustomFactorsTab from '../admin/CustomFactorsTab';

const ORG = { id: 'org-1', name: 'Test Org' };

const FACTORS = [
  {
    id: 'f-1',
    name: 'Customer Diesel factor',
    activity_type: 'Diesel',
    co2e_multiplier: '2.65',
    unit: 'litres',
    scope: 'Scope 1',
    country: 'GB',
    reporting_year: 2025,
    status: 'active',
    version: 1,
  },
  {
    id: 'f-2',
    name: 'Customer Diesel factor v2',
    activity_type: 'Diesel',
    co2e_multiplier: '2.71',
    unit: 'litres',
    scope: 'Scope 1',
    country: 'GB',
    reporting_year: 2025,
    status: 'draft',
    version: 2,
  },
];

beforeEach(() => {
  jest.clearAllMocks();
  api.listCustomerFactors.mockResolvedValue({ factors: FACTORS });
});

describe('CustomFactorsTab — version lifecycle (CL-43)', () => {
  test('renders the factor version explicitly', async () => {
    render(<CustomFactorsTab organization={ORG} isAdmin />);
    await waitFor(() => expect(screen.getByText('Customer Diesel factor')).toBeInTheDocument());
    expect(screen.getByText('v1')).toBeInTheDocument();
    expect(screen.getByText('v2')).toBeInTheDocument();
  });

  test('an approved factor exposes a "New version" action that pre-fills the draft form', async () => {
    render(<CustomFactorsTab organization={ORG} isAdmin />);
    await waitFor(() => expect(screen.getByText('Customer Diesel factor')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /New version/i }));
    await waitFor(() =>
      expect(screen.getByText(/Create a new version of “Customer Diesel factor”/)).toBeInTheDocument(),
    );
    expect(screen.getByRole('button', { name: /Create new version \(draft\)/i })).toBeInTheDocument();
  });

  test('a duplicate create (409) surfaces a clean conflict message instead of a raw error', async () => {
    api.listCustomerFactors.mockResolvedValue({ factors: [] });
    api.createCustomerFactor.mockRejectedValue(
      Object.assign(new Error('Request failed (409)'), {
        status: 409,
        raw: 'a customer factor with this family and version (1) already exists',
      }),
    );
    render(<CustomFactorsTab organization={ORG} isAdmin />);
    await waitFor(() => expect(screen.getByText(/No custom factors yet/i)).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /New factor/i }));
    fireEvent.change(screen.getByLabelText(/Factor name/i), { target: { value: 'Diesel duplicate' } });
    fireEvent.change(screen.getByLabelText(/Activity type/i), { target: { value: 'Diesel' } });
    fireEvent.change(screen.getByLabelText(/CO₂e multiplier/i), { target: { value: '2.5' } });
    fireEvent.click(screen.getByRole('button', { name: /Create draft/i }));
    await waitFor(() =>
      expect(screen.getByText(/a customer factor with this family and version \(1\) already exists/i)).toBeInTheDocument(),
    );
  });

  test('a spend/currency unit is representable (CL-47 spend factors)', async () => {
    api.listCustomerFactors.mockResolvedValue({ factors: [] });
    render(<CustomFactorsTab organization={ORG} isAdmin />);
    await waitFor(() => expect(screen.getByText(/No custom factors yet/i)).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /New factor/i }));
    const unitSelect = screen.getByLabelText(/Unit/i);
    expect(unitSelect).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'GBP' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'EUR' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'USD' })).toBeInTheDocument();
  });
});
