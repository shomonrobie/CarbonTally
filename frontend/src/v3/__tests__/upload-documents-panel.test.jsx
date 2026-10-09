// frontend/src/v3/__tests__/upload-documents-panel.test.jsx
//
// CT-PO-UPLOAD-UNIFY-001 — the unified "Upload documents" surface.
//
// This replaces the previous split (single-file "Upload document" form +
// separate "Batch upload" panel). It must:
//   * offer ONE multi-file entry point with NO mandatory "Data type" selector;
//   * drive the SAME approved signed-direct protocol once per file;
//   * report a REAL per-file outcome, showing the document type CarbonTally
//     classified each file as (with its confidence);
//   * keep going after a partial failure and never report an upload as completed
//     when a file did not reach storage.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import UploadDocumentsPanel from '../customer/UploadDocumentsPanel';

jest.mock('../api', () => ({
  v3UploadDocumentDirect: jest.fn(),
  v3CreateUploadBatch: jest.fn(),
  v3UpdateUploadBatchProgress: jest.fn(),
}));

import {
  v3CreateUploadBatch,
  v3UpdateUploadBatchProgress,
  v3UploadDocumentDirect,
} from '../api';

const ORG = { id: 'org-a', name: 'Acme Ltd' };

const CLASSIFIED = {
  document_type_code: 'invoice_electricity',
  document_type_id: 'dt-1',
  confidence: 0.8,
  suggested_type: 'Electricity Invoice',
  category: 'invoice',
  source: 'auto_classified',
  alternative_types: [],
};

const CLEAN = {
  status: 'clean',
  scan_state: 'clean',
  security_gate: { scanner: 'structural', scan_state: 'clean' },
  classification: CLASSIFIED,
};

const DETECTED_COPY =
  'Detected: Electricity Invoice (80% confidence — confirmed during processing).';

const selectFiles = (names) => {
  const files = names.map(
    (name) => new File([new Uint8Array([1, 2, 3])], name, { type: 'application/pdf' })
  );
  fireEvent.change(document.getElementById('upload-documents-files'), { target: { files } });
};

beforeEach(() => {
  jest.clearAllMocks();
  v3CreateUploadBatch.mockResolvedValue({ id: 'batch-1', status: 'pending' });
  v3UpdateUploadBatchProgress.mockResolvedValue({ id: 'batch-1' });
});

test('it refuses to offer document upload without an organisation', () => {
  render(<UploadDocumentsPanel org={null} />);
  expect(screen.getByText(/no organisation is selected/i)).toBeInTheDocument();
  expect(document.getElementById('upload-documents-files')).toBeNull();
});

test('there is no mandatory Data type selector and nothing uploads until asked', () => {
  render(<UploadDocumentsPanel org={ORG} />);
  // The pre-upload "Data type" choice is gone: no select, no label.
  expect(screen.queryByRole('combobox')).toBeNull();
  expect(screen.queryByText('Data type')).toBeNull();
  // ... and an honest empty state explains what to do next.
  expect(screen.getByText(/no files selected yet/i)).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /^upload /i })).toBeNull();
  expect(v3UploadDocumentDirect).not.toHaveBeenCalled();
  expect(v3CreateUploadBatch).not.toHaveBeenCalled();
});

test('each file is uploaded through the signed-direct flow and its type is shown', async () => {
  v3UploadDocumentDirect.mockResolvedValue(CLEAN);
  const onUploaded = jest.fn();

  render(<UploadDocumentsPanel org={ORG} onUploaded={onUploaded} />);
  selectFiles(['a.pdf', 'b.pdf']);
  expect(screen.getByText('a.pdf')).toBeInTheDocument();
  expect(screen.getByText('b.pdf')).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: /upload 2 files/i }));

  await waitFor(() => expect(onUploaded).toHaveBeenCalledTimes(1));

  // The batch grouping record is created for a multi-file upload only, and it no
  // longer carries a user-chosen data_type.
  expect(v3CreateUploadBatch).toHaveBeenCalledWith(
    'org-a',
    expect.objectContaining({ metadata: expect.objectContaining({ file_count: 2 }) })
  );
  expect(v3UploadDocumentDirect).toHaveBeenCalledTimes(2);
  expect(v3UploadDocumentDirect.mock.calls[0][0]).toMatchObject({ organization_id: 'org-a' });
  expect(v3UploadDocumentDirect.mock.calls[0][0].data_type).toBeUndefined();
  expect(v3UploadDocumentDirect.mock.calls[0][0].file.name).toBe('a.pdf');
  // The batch is only completed once BOTH files really landed.
  expect(v3UpdateUploadBatchProgress.mock.calls).toEqual([
    ['batch-1', { processed_files: 1, status: 'processing' }],
    ['batch-1', { processed_files: 2, status: 'completed' }],
  ]);
  expect(screen.getByText(/2 uploaded, 0 not uploaded/i)).toBeInTheDocument();
  expect(screen.getAllByText('Uploaded')).toHaveLength(2);
  // The per-file classification is the backend's verdict, explained honestly.
  expect(screen.getAllByText(DETECTED_COPY)).toHaveLength(2);
});

test('a single file does not create a batch grouping record', async () => {
  v3UploadDocumentDirect.mockResolvedValue(CLEAN);
  const onUploaded = jest.fn();

  render(<UploadDocumentsPanel org={ORG} onUploaded={onUploaded} />);
  selectFiles(['only.pdf']);
  fireEvent.click(screen.getByRole('button', { name: /upload 1 file/i }));

  await waitFor(() => expect(onUploaded).toHaveBeenCalledTimes(1));
  expect(v3UploadDocumentDirect).toHaveBeenCalledTimes(1);
  expect(v3CreateUploadBatch).not.toHaveBeenCalled();
  expect(v3UpdateUploadBatchProgress).not.toHaveBeenCalled();
  expect(screen.getByText(/1 uploaded, 0 not uploaded/i)).toBeInTheDocument();
});

test('a partial failure is reported per file and does not abort the upload', async () => {
  const failure = Object.assign(new Error('storage refused it'), { code: 'UPLOAD_STORAGE' });
  v3UploadDocumentDirect.mockResolvedValueOnce(CLEAN).mockRejectedValueOnce(failure);
  const onUploaded = jest.fn();

  render(<UploadDocumentsPanel org={ORG} onUploaded={onUploaded} />);
  selectFiles(['good.pdf', 'bad.pdf']);
  fireEvent.click(screen.getByRole('button', { name: /upload 2 files/i }));

  await waitFor(() => expect(onUploaded).toHaveBeenCalledTimes(1));

  expect(v3UploadDocumentDirect).toHaveBeenCalledTimes(2); // the second file still ran
  expect(screen.getByText('Not uploaded')).toBeInTheDocument();
  expect(screen.getByText('Uploaded')).toBeInTheDocument();
  expect(screen.getByText(/1 uploaded, 1 not uploaded/i)).toBeInTheDocument();
  // The refused file shows the real reason; only the accepted file gets a type.
  expect(
    screen.getByText(/The file did not reach storage, so no document was added/i)
  ).toBeInTheDocument();
  expect(screen.getAllByText(DETECTED_COPY)).toHaveLength(1);
  // An upload with a refused file is 'partial' — never 'completed'.
  expect(v3UpdateUploadBatchProgress.mock.calls[1][1]).toEqual({
    processed_files: 2,
    status: 'partial',
  });
});

test('a missing batch grouping record does not block the individual uploads', async () => {
  v3CreateUploadBatch.mockRejectedValue(new Error('forbidden'));
  v3UploadDocumentDirect.mockResolvedValue(CLEAN);
  const onUploaded = jest.fn();

  render(<UploadDocumentsPanel org={ORG} onUploaded={onUploaded} />);
  selectFiles(['a.pdf', 'b.pdf']);
  fireEvent.click(screen.getByRole('button', { name: /upload 2 files/i }));

  await waitFor(() => expect(onUploaded).toHaveBeenCalledTimes(1));

  expect(v3UploadDocumentDirect).toHaveBeenCalledTimes(2);
  expect(v3UpdateUploadBatchProgress).not.toHaveBeenCalled();
  expect(screen.getByText(/batch grouping record could not be created/i)).toBeInTheDocument();
  expect(screen.getByText(/2 uploaded, 0 not uploaded/i)).toBeInTheDocument();
});

test('files can be dropped onto the panel, and duplicates are not listed twice', async () => {
  const files = [
    new File([new Uint8Array([1, 2, 3])], 'dropped.pdf', { type: 'application/pdf' }),
  ];

  render(<UploadDocumentsPanel org={ORG} />);
  const dropZone = document.getElementById('upload-documents-files').parentElement;
  fireEvent.drop(dropZone, { dataTransfer: { files } });
  expect(screen.getByText('dropped.pdf')).toBeInTheDocument();

  // Dropping the same file again is refused with an explanation, not a second row.
  fireEvent.drop(dropZone, { dataTransfer: { files } });
  expect(screen.getByText(/already in the list/i)).toBeInTheDocument();
  expect(screen.getAllByText('dropped.pdf')).toHaveLength(1);
});

test('an unclassified document says so instead of inventing a type', async () => {
  v3UploadDocumentDirect.mockResolvedValue({
    ...CLEAN,
    classification: {
      document_type_code: null,
      document_type_id: null,
      confidence: 0,
      suggested_type: null,
      category: null,
      source: 'unavailable',
      alternative_types: [],
    },
  });

  render(<UploadDocumentsPanel org={ORG} onUploaded={jest.fn()} />);
  selectFiles(['mystery.pdf']);
  fireEvent.click(screen.getByRole('button', { name: /upload 1 file/i }));

  await waitFor(() =>
    expect(screen.getByText(/type not detected/i)).toBeInTheDocument()
  );
  expect(screen.getByText(/will confirm the document type during processing/i)).toBeInTheDocument();
});

test('an explicit type chosen by the uploader is reported as such', async () => {
  v3UploadDocumentDirect.mockResolvedValue({
    ...CLEAN,
    classification: { ...CLASSIFIED, source: 'user_selected', confidence: 0.95 },
  });

  render(<UploadDocumentsPanel org={ORG} onUploaded={jest.fn()} />);
  selectFiles(['a.pdf']);
  fireEvent.click(screen.getByRole('button', { name: /upload 1 file/i }));

  await waitFor(() =>
    expect(screen.getByText('Type set to Electricity Invoice.')).toBeInTheDocument()
  );
});
