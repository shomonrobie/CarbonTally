// frontend/src/v3/__tests__/source-evidence-viewer.test.jsx
// Shared Source Evidence Viewer (PO authorization, 2026-09-22).
//
// The viewer is one reusable capability: original source document (left) beside
// the extracted/mapped evidence and its calculation context (right), linked by an
// authoritative location when one exists. Access is decided by the backend on
// every read — the URL carries a locator only, and every failure renders one
// non-disclosing state.
import React from 'react';
import { render, screen, waitFor, cleanup, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

// The repo's component tests mock react-router-dom (the installed module cannot
// be resolved in this environment); only the primitives the viewer uses are
// provided, and they behave exactly like the real ones for this component.
jest.mock('react-router-dom', () => {
  const ReactActual = require('react');
  return {
    Link: ({ to, children, ...rest }) =>
      ReactActual.createElement('a', { href: to, ...rest }, children),
    useParams: () => ({ lineItemId: 'line-a-3' }),
    useSearchParams: () => [new URLSearchParams(), jest.fn()],
  };
});

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: jest.fn(), getUser: jest.fn() } },
}));

jest.mock('../api', () => ({
  getEvidenceLine: jest.fn(),
}));

import SourceEvidenceViewer from '../evidence/SourceEvidenceViewer';

const api = jest.requireMock('../api');

const LINE_ID = 'line-a-3';

function payload(overrides = {}) {
  return {
    evidence_line_item_id: LINE_ID,
    source_item_id: 'item-a',
    materialisation_kind: 'FORWARD',
    line: {
      id: LINE_ID,
      line_number: 3,
      raw_description: 'Waste disposal 60 t',
      raw_quantity: '60.0',
      raw_unit: 't',
      redacted_fields: [],
    },
    location: {
      kind: 'page',
      page: 2,
      page_state: 'verified',
      sheet: null,
      row: null,
      row_reference: null,
      line_number: 3,
      ordinal_note:
        'Line 3 of the extracted rows. That ordinal is not a physical file row or page on its own.',
      precision: 'page',
      display: 'Source page 2.',
    },
    document: {
      id: 'file-a',
      name: 'INV-10482.pdf',
      file_type: 'PDF',
      size_bytes: 2048,
      uploaded_at: null,
      signed_url: 'https://signed/x',
    },
    document_available: true,
    calculations: [
      {
        id: 'snap-a',
        activity: 'Waste disposal',
        co2e_kg: '150.4',
        scope: 'Scope 3',
        date: '2026-05-08',
        quantity: '60.0',
        quantity_unit: 't',
      },
    ],
    access: {
      drill_down_depth: 'FULL',
      drill_down_rationale: 'DM-6: organisation Owner/Admin have full drill-down',
      document_references_available: true,
    },
    ...overrides,
  };
}

function renderViewer() {
  return render(<SourceEvidenceViewer />);
}

beforeEach(() => {
  jest.clearAllMocks();
});

afterEach(cleanup);

describe('shared Source Evidence Viewer', () => {
  test('shows the original document beside the extracted evidence', async () => {
    api.getEvidenceLine.mockResolvedValue(payload());

    renderViewer();

    await waitFor(() =>
      expect(screen.getByText('Extracted and mapped evidence')).toBeInTheDocument(),
    );
    expect(api.getEvidenceLine).toHaveBeenCalledWith(LINE_ID);
    // Original document (left) — the signed URL renders in the secure frame.
    expect(screen.getByTitle('INV-10482.pdf')).toBeInTheDocument();
    // Extracted evidence (right) — read-only values, no editable control.
    expect(screen.getByText('Waste disposal 60 t')).toBeInTheDocument();
    expect(screen.getByText('60.0 t')).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /save|edit/i })).not.toBeInTheDocument();
  });

  test('links the evidence to its authoritative location', async () => {
    api.getEvidenceLine.mockResolvedValue(payload());

    renderViewer();

    const location = await screen.findByTestId('source-evidence-location');
    expect(location).toHaveAttribute('data-location-state', 'exact');
    expect(screen.getByText('Source page 2')).toBeInTheDocument();
    // The ordinal is stated as a line, never as a physical row/page.
    expect(screen.getByText(/not a physical file row or page/i)).toBeInTheDocument();
    expect(screen.queryByTestId('source-evidence-location-caveat')).not.toBeInTheDocument();
  });

  test('states honestly when no exact location is authoritative', async () => {
    api.getEvidenceLine.mockResolvedValue(
      payload({
        location: {
          kind: 'unavailable',
          page: null,
          page_state: 'unavailable',
          row: null,
          sheet: null,
          line_number: 3,
          ordinal_note: null,
          precision: 'none',
          display: 'Exact source location is not available for this line.',
        },
      }),
    );

    renderViewer();

    const location = await screen.findByTestId('source-evidence-location');
    expect(location).toHaveAttribute('data-location-state', 'unavailable');
    expect(screen.getByTestId('source-evidence-location-caveat')).toBeInTheDocument();
    // Never invents a page.
    expect(screen.queryByText(/Source page \d/)).not.toBeInTheDocument();
  });

  test('withholds the source document below FULL depth without hiding the evidence', async () => {
    api.getEvidenceLine.mockResolvedValue(
      payload({
        document: {
          id: 'file-a',
          name: 'INV-10482.pdf',
          file_type: 'PDF',
          size_bytes: 2048,
          uploaded_at: null,
          signed_url: '',
        },
        location: {
          state: 'restricted',
          display: 'Exact source location is not available for your access level.',
        },
        access: {
          drill_down_depth: 'CONTROLLED',
          drill_down_rationale:
            'DM-6: Viewer is controlled; a Member is treated as controlled (least privilege)',
          document_references_available: false,
        },
      }),
    );

    renderViewer();

    await waitFor(() =>
      expect(screen.getByTestId('source-evidence-document-withheld')).toBeInTheDocument(),
    );
    expect(screen.queryByTitle('INV-10482.pdf')).not.toBeInTheDocument();
    expect(screen.getByTestId('source-evidence-location')).toHaveAttribute(
      'data-location-state',
      'restricted',
    );
    // The extracted evidence is still explained.
    expect(screen.getByText('Waste disposal 60 t')).toBeInTheDocument();
  });

  test('renders the calculation context for the line (bounded, read-only)', async () => {
    api.getEvidenceLine.mockResolvedValue(payload());

    renderViewer();

    expect(await screen.findByText('150.4 kg CO₂e')).toBeInTheDocument();
    expect(screen.getByText('snap-a')).toBeInTheDocument();
  });

  test('a Member projection withholds the description instead of fabricating it', async () => {
    api.getEvidenceLine.mockResolvedValue(
      payload({
        line: {
          id: LINE_ID,
          line_number: 3,
          raw_quantity: '60.0',
          raw_unit: 't',
          redacted_fields: ['raw_description', 'source_page', 'payload_hash'],
        },
      }),
    );

    renderViewer();

    expect(await screen.findByText('Not available for your access level')).toBeInTheDocument();
  });

  test('an unavailable line renders one non-disclosing state (no existence leak)', async () => {
    api.getEvidenceLine.mockRejectedValue(new Error('403'));

    renderViewer();

    const alert = await screen.findByTestId('source-evidence-unavailable');
    expect(alert).toBeInTheDocument();
    expect(screen.queryByText(/not found/i)).not.toBeInTheDocument();
    expect(screen.queryByText(LINE_ID)).not.toBeInTheDocument();
    expect(screen.queryByText(/signed/i)).not.toBeInTheDocument();
  });

  test('a retry re-requests the same locator (authorization is per read)', async () => {
    api.getEvidenceLine.mockRejectedValueOnce(new Error('403'));
    api.getEvidenceLine.mockResolvedValue(payload());

    renderViewer();

    await screen.findByTestId('source-evidence-unavailable');
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));

    await waitFor(() => expect(api.getEvidenceLine).toHaveBeenCalledTimes(2));
    expect(await screen.findByText('Extracted and mapped evidence')).toBeInTheDocument();
  });
});
