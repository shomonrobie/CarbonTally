// frontend/src/v3/__tests__/reports-page.test.jsx
// BL-2 — ReportsPage reference test for the shared customer table behaviour:
// honest full-set load (limit 500), client pagination, filter propagation to
// the server, meaningful empty state, and error recovery. The API layer is
// mocked; router rendering uses MemoryRouter.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// react-router-dom v7 re-exports from `react-router` which jest cannot resolve;
// the codebase's convention is to stub the router primitives in tests.
jest.mock('react-router-dom', () => ({
  Link: ({ to, className, children }) => <a href={to} className={className}>{children}</a>,
}));

jest.mock('../api', () => ({
  resolveV3Organization: jest.fn(),
  listReports: jest.fn(),
  getReportTypes: jest.fn(),
  generateReport: jest.fn(),
  downloadReport: jest.fn(),
  downloadExport: jest.fn(),
  exportEmissionsUrl: jest.fn(() => '/api/v3/exports/emissions.csv'),
  exportDocumentsUrl: jest.fn(() => '/api/v3/exports/documents.csv'),
}));

import ReportsPage from '../reports/ReportsPage';
import * as api from '../api';

const ORG = { id: 'org-1', name: 'Acme Ltd' };

const makeReports = (n) => Array.from({ length: n }, (_, i) => ({
  id: `rep-${i}`,
  report_name: `Report ${i}`,
  report_type: 'annual',
  reporting_year: 2025,
  status: 'completed',
  created_at: '2025-01-01T00:00:00Z',
  completed_at: '2025-01-02T00:00:00Z',
  current_version: { version_number: 1 },
  ready: true,
  created_by: 'user-1234',
}));

beforeEach(() => {
  jest.clearAllMocks();
  api.resolveV3Organization.mockResolvedValue(ORG);
  api.listReports.mockResolvedValue({
    reports: makeReports(25),
    count_by_status: { completed: 25, pending: 0, generating: 0, failed: 0 },
  });
  api.getReportTypes.mockResolvedValue({
    report_types: [{ id: 'annual', name: 'Annual emissions report' }],
  });
});

const renderPage = () => render(<ReportsPage />);

describe('ReportsPage (BL-2)', () => {
  test('loads with an honest limit and paginates client-side', async () => {
    renderPage();
    expect(await screen.findByText('Report 0')).toBeInTheDocument();
    expect(api.listReports).toHaveBeenCalledWith('org-1', expect.objectContaining({ limit: 500 }));
    expect(screen.getByText('1–10 of 25')).toBeInTheDocument();
    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText('11–20 of 25')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Rows per page'), { target: { value: '25' } });
    // One page now: the pagination bar hides and all rows are visible.
    expect(screen.getAllByRole('row')).toHaveLength(26);
    expect(screen.queryByText('Page 1 of 3')).not.toBeInTheDocument();
  });

  test('sorts the report table by status without losing the total', async () => {
    renderPage();
    await screen.findByText('Report 0');
    fireEvent.click(screen.getByRole('button', { name: /status/i }));
    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
  });

  test('renders a meaningful empty state', async () => {
    api.listReports.mockResolvedValue({ reports: [], count_by_status: {} });
    renderPage();
    expect(await screen.findByText(/No reports found/i)).toBeInTheDocument();
  });

  test('forwards filter selections to the server with the limit', async () => {
    renderPage();
    await screen.findByText('Report 0');
    const statusSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(statusSelect, { target: { value: 'pending' } });
    await waitFor(() => {
      expect(api.listReports).toHaveBeenCalledWith(
        'org-1',
        expect.objectContaining({ status: 'pending', limit: 500 }),
      );
    });
  });

  test('error state offers a retry', async () => {
    api.listReports.mockRejectedValue(new Error('reports unavailable'));
    renderPage();
    expect(await screen.findByText(/reports unavailable/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});
