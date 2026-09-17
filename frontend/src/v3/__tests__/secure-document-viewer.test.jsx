// frontend/src/v3/__tests__/secure-document-viewer.test.jsx
// P0-1 — SecureDocumentViewer must:
//  * render PDFs in a NON-sandboxed iframe (Chromium disables its PDF viewer
//    in sandboxed frames — the root of the blank document-preview defect);
//  * keep images in a sandboxed frame;
//  * never frame non-renderable types (CSV/XLSX/other) — show a restricted
//    placeholder instead;
//  * keep the "view only — download disabled" affordance (no download control).
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import SecureDocumentViewer from '../components/workbench/SecureDocumentViewer';

describe('SecureDocumentViewer (P0-1 inline preview)', () => {
  test('renders a PDF in a non-sandboxed iframe', () => {
    const { container } = render(
      <SecureDocumentViewer src="https://example.test/storage/sign/x?token=1" title="bill.pdf" allowDownload={false} />
    );
    const iframe = container.querySelector('iframe');
    expect(iframe).toBeInTheDocument();
    expect(iframe).not.toHaveAttribute('sandbox');
    expect(screen.getByText(/view only — download disabled/i)).toBeInTheDocument();
  });

  test('keeps images in a sandboxed iframe', () => {
    const { container } = render(
      <SecureDocumentViewer src="https://example.test/storage/sign/x?token=1" title="scan.png" />
    );
    const iframe = container.querySelector('iframe');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('sandbox', 'allow-same-origin');
  });

  // Step 2C / POD-3 — the CSV case changed deliberately: a CSV/TSV/XLSX is no
  // longer shown as "preview not available" (that was the PO-visible defect);
  // it now renders the bounded structured-data preview, still without any
  // iframe and still without a download control for restricted roles.
  test('renders the structured-data preview for a CSV (no iframe, no download)', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      text: async () => 'Transaction Date,Fuel Type,Volume (L)\n01/10/2023,Diesel,53.8\n',
    });
    const { container } = render(
      <SecureDocumentViewer src="https://example.test/storage/sign/x?token=1" title="usage.csv" allowDownload={false} />
    );
    expect(container.querySelector('iframe')).not.toBeInTheDocument();
    expect(await screen.findByTestId('structured-preview')).toBeInTheDocument();
    expect(screen.getByText(/Download disabled for this role/i)).toBeInTheDocument();
    delete global.fetch;
  });

  test('never frames an unknown file type', () => {
    const { container } = render(
      <SecureDocumentViewer src="https://example.test/storage/sign/x?token=1" title="notes.docx" allowDownload={false} />
    );
    expect(container.querySelector('iframe')).not.toBeInTheDocument();
    expect(screen.getByText(/Document preview is not available/i)).toBeInTheDocument();
    expect(screen.getByText(/Download is restricted/i)).toBeInTheDocument();
  });

  test('shows the empty state when no source is present', () => {
    render(<SecureDocumentViewer src="" title="bill.pdf" />);
    expect(screen.getByText(/No source document available/i)).toBeInTheDocument();
  });
});
