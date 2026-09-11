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

  test('never frames a non-renderable file type (CSV)', () => {
    const { container } = render(
      <SecureDocumentViewer src="https://example.test/storage/sign/x?token=1" title="usage.csv" allowDownload={false} />
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
