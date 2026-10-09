// frontend/src/v3/customer/UploadDocumentsPanel.jsx
//
// CT-PO-UPLOAD-UNIFY-001 — the ONE document-upload surface.
//
// The previous split (a single-file "Upload document" form plus a separate
// "Batch upload" panel on the same page) asked the user the same question twice
// and forced a pre-upload "Data type" choice CarbonTally can answer itself. This
// panel replaces both:
//
//   * one entry point, one drop zone, 1..25 files of mixed formats;
//   * no mandatory "Data type" selector — every file is type-classified by the
//     backend against the CarbonTally document taxonomy and the verdict is shown
//     per file, with its confidence;
//   * the SAME approved signed-direct protocol, once per file:
//       create the batch grouping record (POST /api/v3/batches, only when >1 file)
//       for each file: upload-url -> PUT bytes to private storage -> upload-complete
//       report the batch's REAL progress after each file (PATCH /api/v3/batches/{id})
//
// Nothing here fabricates a success. A refused file is reported as refused and
// never aborts the rest of the upload; the backend still decides everything —
// authorisation, size limits, the security gate and pipeline enqueue are
// unchanged and enforced server-side.
import React, { useRef, useState } from 'react';
import { formatBytes } from '../utils';
import {
  v3CreateUploadBatch,
  v3UpdateUploadBatchProgress,
  v3UploadDocumentDirect,
} from '../api';
import {
  ACCEPTED_DOCUMENT_TYPES,
  describeClassification,
  describeSecurityGate,
  describeUploadError,
} from '../uploadsCopy';
import { useClientAccess } from '../clientAccess';

//: Keep one upload within the per-batch limit the platform advertises.
const MAX_FILES = 25;

const STATUS_LABEL = {
  queued: 'Queued',
  uploading: 'Uploading…',
  uploaded: 'Uploaded',
  failed: 'Not uploaded',
};

/** Identity of a chosen file, used only to keep the queue free of duplicates. */
const fileKey = (file) => `${file.name}::${file.size}::${file.lastModified}`;

const newRow = (id, file) => ({
  id,
  file,
  status: 'queued',
  progress: 0,
  message: '',
  classification: null,
});

export default function UploadDocumentsPanel({ org, onUploaded }) {
  // CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05 — a consultant-managed
  // client's own user reaches the SAME Organisation surface but document upload
  // is bounded by the client access profile (COLLABORATIVE only). This hides the
  // control; the backend enforces the identical ceiling (upload_gate). Absent
  // view (direct customer / consultant / staff) → unrestricted.
  const canUpload = useClientAccess().can('upload_document');
  const [queue, setQueue] = useState([]);
  const [running, setRunning] = useState(false);
  const [batchWarning, setBatchWarning] = useState('');
  const [summary, setSummary] = useState(null);
  const [selectWarning, setSelectWarning] = useState('');
  const [dragging, setDragging] = useState(false);
  const nextId = useRef(1);

  const patchItem = (id, patch) =>
    setQueue((prev) => prev.map((q) => (q.id === id ? { ...q, ...patch } : q)));

  const addFiles = (chosen) => {
    const incoming = Array.from(chosen || []);
    if (incoming.length === 0) return;
    setSummary(null);
    setBatchWarning('');

    const seen = new Set(queue.map((q) => fileKey(q.file)));
    const fresh = [];
    let duplicates = 0;
    for (const file of incoming) {
      const key = fileKey(file);
      if (seen.has(key)) {
        duplicates += 1;
        continue;
      }
      seen.add(key);
      fresh.push(file);
    }

    const room = Math.max(0, MAX_FILES - queue.length);
    const kept = fresh.slice(0, room);
    const overflow = fresh.length - kept.length;

    const notes = [];
    if (overflow > 0) {
      notes.push(
        `Only the first ${MAX_FILES} files were kept — one upload is limited to ${MAX_FILES} files at a time.`
      );
    }
    if (duplicates > 0) {
      notes.push(
        duplicates === 1
          ? '1 file was already in the list and was not added again.'
          : `${duplicates} files were already in the list and were not added again.`
      );
    }
    setSelectWarning(notes.join(' '));

    const rows = kept.map((file) => newRow(nextId.current++, file));
    setQueue((prev) => [...prev, ...rows]);
  };

  const onSelect = (event) => {
    addFiles(event.target.files);
    event.target.value = '';
  };

  const onDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    addFiles(event.dataTransfer?.files);
  };

  const removeItem = (id) => {
    if (running) return;
    setSummary(null);
    setQueue((prev) => prev.filter((q) => q.id !== id));
  };

  const clearQueue = () => {
    if (running) return;
    setQueue([]);
    setSelectWarning('');
    setBatchWarning('');
    setSummary(null);
  };

  const onRun = async () => {
    if (!org || queue.length === 0 || running) return;
    setRunning(true);
    setSummary(null);
    setBatchWarning('');
    setSelectWarning('');

    const items = queue;
    setQueue((prev) =>
      prev.map((q) => ({
        ...q,
        status: 'queued',
        progress: 0,
        message: '',
        classification: null,
      }))
    );

    // 1. Create the real grouping record — only when this really is a multi-file
    //    upload (existing POST /api/v3/batches). If it fails the individual
    //    uploads still proceed: a missing grouping record must never silently
    //    drop the user's files.
    let activeBatchId = null;
    if (items.length > 1) {
      try {
        const batch = await v3CreateUploadBatch(org.id, {
          batch_name: `Upload documents — ${new Date().toLocaleString()}`,
          metadata: {
            surface: 'v3_documents_batch',
            file_count: items.length,
          },
        });
        activeBatchId = batch?.id || null;
      } catch (e) {
        setBatchWarning(
          `The batch grouping record could not be created (${e.message || 'unknown error'}). ` +
            'The files are still uploaded individually below.'
        );
      }
    }

    // 2. Upload each file through the approved signed-direct protocol. A failure
    //    is recorded per file and does not abort the remaining files.
    let processed = 0;
    let accepted = 0;
    let failed = 0;
    for (const item of items) {
      patchItem(item.id, {
        status: 'uploading',
        progress: 0,
        message: '',
        classification: null,
      });
      try {
        const result = await v3UploadDocumentDirect({
          organization_id: org.id,
          file: item.file,
          onProgress: (p) => patchItem(item.id, { progress: p }),
        });
        accepted += 1;
        patchItem(item.id, {
          status: 'uploaded',
          progress: 100,
          // The type CarbonTally decided for THIS file — never assumed by the UI.
          classification: result?.classification || null,
          message: `status ${result.status}. Security gate: ${describeSecurityGate(result)}.`,
        });
      } catch (e) {
        failed += 1;
        patchItem(item.id, { status: 'failed', message: describeUploadError(e) });
      }

      processed += 1;
      if (activeBatchId) {
        const status =
          processed < items.length ? 'processing' : failed > 0 ? 'partial' : 'completed';
        try {
          await v3UpdateUploadBatchProgress(activeBatchId, {
            processed_files: processed,
            status,
          });
        } catch (_e) {
          /* progress reporting is best-effort; it must not fail the batch */
        }
      }
    }

    setSummary({ accepted, failed, total: items.length });
    setRunning(false);
    if (accepted > 0) onUploaded?.();
  };

  const done = queue.filter((q) => q.status === 'uploaded' || q.status === 'failed').length;

  return (
    <div className="v3-card">
      <h2>Upload documents</h2>
      <p className="v3-muted">
        Upload one or many documents — PDF, JPG/PNG/GIF/WEBP/BMP, CSV or Excel, in
        any mix. You do not have to tell CarbonTally what each file is: every
        document is type-classified automatically and the result is shown per file
        below. Each file goes straight to private storage and is security-gated
        individually, so a file that is refused does not stop the others.
      </p>

      {!org && (
        <p className="v3-muted">
          No organisation is selected, so document upload is unavailable.
        </p>
      )}

      {org && !canUpload && (
        <p className="v3-muted">
          Your client access level does not permit document upload. Your
          consultant uploads documents on your behalf.
        </p>
      )}

      {org && canUpload && (
        <>
          <div
            className="v3-form-group"
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            style={{
              border: `1px dashed ${
                dragging ? 'var(--v3-accent, #2b6cb0)' : 'var(--v3-border, #e2e8f0)'
              }`,
              borderRadius: 8,
              padding: 16,
              textAlign: 'center',
            }}
          >
            <label htmlFor="upload-documents-files">
              {dragging
                ? 'Drop the files to add them'
                : 'Drag and drop documents here, or choose files'}
            </label>
            <input
              id="upload-documents-files"
              type="file"
              multiple
              accept={ACCEPTED_DOCUMENT_TYPES}
              onChange={onSelect}
              disabled={running}
            />
            <p className="v3-muted" style={{ marginTop: 4 }}>
              Up to {MAX_FILES} files at a time. Every file is uploaded directly to
              private storage and validated by CarbonTally&apos;s security gate
              before it is processed.
            </p>
          </div>

          {selectWarning && (
            <div className="v3-note" style={{ marginTop: 8 }}>{selectWarning}</div>
          )}
          {batchWarning && (
            <div className="v3-note" style={{ marginTop: 8 }}>{batchWarning}</div>
          )}

          {queue.length === 0 ? (
            <p className="v3-muted" style={{ marginTop: 12 }}>
              No files selected yet. Choose one or more documents above and they
              will be listed here with their upload status and detected type.
            </p>
          ) : (
            <>
              <ul
                aria-label="Documents to upload"
                style={{ listStyle: 'none', margin: '12px 0 0', padding: 0 }}
              >
                {queue.map((item) => (
                  <li
                    key={item.id}
                    style={{
                      padding: '10px 0',
                      borderBottom: '1px solid var(--v3-border, #e2e8f0)',
                    }}
                  >
                    <div style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                      <strong style={{ flex: 1, wordBreak: 'break-all' }}>
                        {item.file.name}
                      </strong>
                      <span className="v3-muted">{formatBytes(item.file.size)}</span>
                      <span className="v3-muted">{STATUS_LABEL[item.status]}</span>
                      {!running && item.status === 'queued' && (
                        <button
                          type="button"
                          className="v3-btn v3-btn-sm"
                          onClick={() => removeItem(item.id)}
                          aria-label={`Remove ${item.file.name}`}
                        >
                          Remove
                        </button>
                      )}
                    </div>

                    {item.status === 'uploading' && (
                      <div className="v3-muted" role="status" aria-live="polite">
                        Uploading… {item.progress}%
                      </div>
                    )}

                    {item.status === 'uploaded' && (
                      <div className="v3-muted">{item.message}</div>
                    )}

                    {item.status === 'uploaded' && item.classification && (
                      <div className="v3-muted">
                        {describeClassification(item.classification)}
                      </div>
                    )}

                    {item.status === 'failed' && (
                      <div className="v3-error">{item.message}</div>
                    )}
                  </li>
                ))}
              </ul>

              <div className="v3-actions" style={{ marginTop: 12 }}>
                <button
                  className="v3-btn v3-btn-primary"
                  onClick={onRun}
                  disabled={running || queue.length === 0}
                >
                  {running
                    ? `Uploading… ${done}/${queue.length}`
                    : `Upload ${queue.length} file${queue.length === 1 ? '' : 's'}`}
                </button>
                <button
                  type="button"
                  className="v3-btn"
                  onClick={clearQueue}
                  disabled={running}
                >
                  Clear list
                </button>
              </div>
            </>
          )}

          {running && (
            <div className="v3-muted" role="status" aria-live="polite" style={{ marginTop: 8 }}>
              {done} of {queue.length} finished — do not close this window while
              files are uploading. An unfinished upload is refused and can be
              started again.
            </div>
          )}

          {summary && (
            <div className="v3-note" style={{ marginTop: 8 }}>
              {summary.accepted} uploaded, {summary.failed} not uploaded
              {summary.failed > 0
                ? ' — the files that did not reach storage are listed with the reason above.'
                : '.'}
            </div>
          )}
        </>
      )}
    </div>
  );
}
