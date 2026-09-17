// frontend/src/v3/__tests__/structured-data-preview.test.jsx
// Step 2C / POD-3 — CSV/TSV/XLSX structured preview in the workbench viewer.
import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('xlsx', () => ({
  // NOTE: plain functions, not jest.fn() — react-scripts sets `resetMocks: true`,
  // which would wipe a mock implementation created in this factory.
  read: () => ({
    SheetNames: ['Summary', 'Readings'],
    Sheets: { Summary: {}, Readings: {} },
  }),
  utils: {
    sheet_to_json: () => [
      ['Transaction Date', 'Fuel Type', 'Volume (L)'],
      ['01/10/2023', 'Diesel', 53.8],
    ],
  },
}));

import StructuredDataPreview, {
  parseDelimited,
  previewKind,
} from '../components/workbench/StructuredDataPreview';

const CSV =
  'Transaction Date,Fuel Type,Volume (L),Total Cost (£)\n' +
  '01/10/2023,"Diesel, Premium",53.8,85.21\n' +
  '02/10/2023,diesel,20.96,32.87\n';

beforeEach(() => {
  global.fetch = jest.fn();
});
afterEach(() => {
  jest.clearAllMocks();
});

test('previewKind classifies csv/tsv/xlsx and ignores signed-URL parameters', () => {
  expect(previewKind('fuel_card.csv', 'https://x/y?sig=1')).toBe('csv');
  expect(previewKind('readings.tsv', '')).toBe('csv');
  expect(previewKind('readings.xlsx', '')).toBe('xlsx');
  expect(previewKind('', 'https://x/readings.xlsx?sig=1')).toBe('xlsx');
  expect(previewKind('scan.pdf', '')).toBe('unknown');
});

test('parseDelimited keeps quoted separators inside one cell', () => {
  const rows = parseDelimited('a,b\n"Diesel, Premium",53.8\n', ',');
  expect(rows).toEqual([['a', 'b'], ['Diesel, Premium', '53.8']]);
});

test('a CSV source renders a bounded tabular preview with its headers', async () => {
  global.fetch.mockResolvedValue({ ok: true, text: async () => CSV });

  render(<StructuredDataPreview src="https://signed/fuel_card.csv?sig=1" title="fuel_card.csv" />);

  const table = await screen.findByTestId('structured-data-table');
  expect(within(table).getByText('Fuel Type')).toBeInTheDocument();
  expect(within(table).getByText('Diesel, Premium')).toBeInTheDocument();
  expect(within(table).getByText('20.96')).toBeInTheDocument();
  expect(screen.getByTestId('structured-preview')).toHaveTextContent('Data preview');
  expect(screen.getByTestId('structured-preview')).toHaveTextContent('showing 2 rows');
});

test('an XLSX source renders a workbook/sheet-aware preview', async () => {
  global.fetch.mockResolvedValue({ ok: true, arrayBuffer: async () => new ArrayBuffer(8) });

  render(<StructuredDataPreview src="https://signed/readings.xlsx?sig=1" title="readings.xlsx" />);

  const preview = await screen.findByTestId('structured-preview');
  expect(preview).toHaveTextContent('Workbook preview');
  expect(preview).toHaveTextContent('sheets: Summary, Readings (showing Summary)');
  const table = within(preview).getByTestId('structured-data-table');
  expect(within(table).getByText('Fuel Type')).toBeInTheDocument();
  expect(within(table).getByText('01/10/2023')).toBeInTheDocument();
});

test('a failed fetch shows a truthful error state instead of an empty pane', async () => {
  global.fetch.mockResolvedValue({ ok: false, status: 403 });

  render(<StructuredDataPreview src="https://signed/fuel_card.csv" title="fuel_card.csv" />);

  await waitFor(() =>
    expect(screen.getByTestId('structured-preview-error')).toBeInTheDocument(),
  );
  expect(screen.getByTestId('structured-preview-error')).toHaveTextContent('HTTP 403');
  expect(screen.getByTestId('structured-preview-error')).toHaveTextContent(
    'server-side extraction is unaffected',
  );
});
