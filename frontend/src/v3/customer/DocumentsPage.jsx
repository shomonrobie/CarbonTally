// frontend/src/v3/customer/DocumentsPage.jsx
// Documents — upload to Supabase Storage via the V3 surface (/api/v3/uploads)
// and browse persisted documents (/api/v3/documents) + upload batches
// (/api/v3/batches). All org-scoped, real backend data.
import React, { useCallback, useEffect, useState } from 'react';
import { getDocumentEmissions, resolveV3Organization, v3ListDocuments, v3ListUploadBatches, v3UploadDocumentDirect } from '../api';
import { formatBytes } from '../utils';
import { ErrorState } from '../components/StateViews';
import DataTable from '../components/ui/DataTable';

// Storage Management Step 2A — user-facing copy for the direct-upload outcomes.
// Every string explains the BACKEND's answer; nothing here invents a success.
const describeUploadError = (e) => {
  switch (e?.code) {
    case 'UPLOAD_TOO_LARGE':
      return (
        e.message ||
        'That file is larger than the platform per-file limit. The original is never compressed server-side — please upload a smaller file or split the document.'
      );
    case 'UPLOAD_UNSUPPORTED_TYPE':
      return (
        e.message ||
        'That file type is not supported. Supported: PDF, JPG/PNG/GIF/WEBP/BMP, CSV, XLSX/XLS.'
      );
    case 'UPLOAD_SECURITY_REJECTED':
      return (
        e.message ||
        'The document was rejected by the security check, so it did not enter processing.'
      );
    case 'UPLOAD_AUTHORIZATION_EXPIRED':
      return (
        'The upload authorisation expired before the file finished uploading (or it was refused). Nothing was added — please start the upload again.'
      );
    case 'UPLOAD_STORAGE':
      return 'Storage did not accept the file. Nothing was added to your documents.';
    case 'UPLOAD_NETWORK':
      return 'The upload was interrupted. Nothing was added to your documents.';
    default:
      return e?.message || 'Upload failed';
  }
};

const describeSecurityGate = (result) => {
  const gate = result?.security_gate || {};
  if (result?.virus_scanned) return `virus scan reported by ${gate.scanner}`;
  const state = result?.scan_state || gate.scan_state;
  if (state === 'clean') {
    return 'structural validation passed — no external virus scanner is configured for this deployment';
  }
  return state || 'recorded by the backend';
};

/** The supported document types (mirrors the server-side allow-list). */
const ACCEPTED_DOCUMENT_TYPES = '.pdf,.jpg,.jpeg,.png,.gif,.webp,.bmp,.csv,.xlsx,.xls';

export default function DocumentsPage() {
  const [org, setOrg] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [batches, setBatches] = useState([]);
  const [file, setFile] = useState(null);
  const [dataType, setDataType] = useState('utility');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  const [docEmissions, setDocEmissions] = useState(null);
  const [docEmissionsError, setDocEmissionsError] = useState('');

  const openDocumentEmissions = (fileId) => {
    setDocEmissions(null);
    setDocEmissionsError('');
    getDocumentEmissions(fileId)
      .then(setDocEmissions)
      .catch((e) => setDocEmissionsError(e.message || 'Emissions lookup unavailable'));
  };

  const load = useCallback(async (organizationId) => {
    try {
      const [docs, batchesResult] = await Promise.all([
        v3ListDocuments(organizationId, { limit: 500 }),
        v3ListUploadBatches(organizationId).catch(() => ({ batches: [] })),
      ]);
      setDocuments(docs.documents || []);
      setBatches(batchesResult.batches || []);
    } catch (e) {
      setError(e.message || 'Failed to load documents');
    }
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const organization = await resolveV3Organization();
        if (!organization) {
          setError('No organization is linked to this account.');
          return;
        }
        setOrg(organization);
        await load(organization.id);
      } catch (e) {
        setError(e.message || 'Failed to load documents');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [load, retryCount]);

  const onUpload = async () => {
    if (!file || !org) return;
    setUploading(true);
    setProgress(0);
    setError('');
    setNotice('');
    try {
      // Storage Management Step 2A — the browser uploads the bytes straight to
      // private storage with a short-lived, object-scoped authorisation and then
      // asks CarbonTally to verify + security-gate the result. Only the backend
      // decides whether the document is accepted.
      const result = await v3UploadDocumentDirect({
        organization_id: org.id,
        data_type: dataType,
        file,
        onProgress: setProgress,
      });
      setFile(null);
      setNotice(
        `“${file.name}” uploaded — status ${result.status}. Security gate: ${describeSecurityGate(result)}.`
      );
      await load(org.id);
    } catch (e) {
      setError(describeUploadError(e));
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const documentColumns = [
    {
      key: 'name',
      header: 'Name',
      accessor: 'name',
      sortable: true,
      sortValue: (d) => (d.name || d.file_name || '').toLowerCase(),
      render: (d) => <strong>{d.name || d.file_name}</strong>,
      isHeader: true,
    },
    {
      key: 'type',
      header: 'Type',
      accessor: 'file_type',
      sortable: true,
      sortValue: (d) => (d.file_type || d.document_type || '').toLowerCase(),
      render: (d) => d.file_type || d.document_type || '—',
    },
    {
      key: 'size',
      header: 'Size',
      accessor: 'size_bytes',
      sortable: true,
      sortValue: (d) => (d.size_bytes != null ? d.size_bytes : -1),
      render: (d) => <span className="v3-muted">{d.size_bytes != null ? formatBytes(d.size_bytes) : '—'}</span>,
    },
    {
      key: 'created',
      header: 'Uploaded',
      accessor: 'uploaded_at',
      sortable: true,
      // DR-007 — the V3 documents API exposes the upload timestamp as
      // `uploaded_at` (backend/data/documents.py: upload_date or created_at);
      // `created_at` is kept as a fallback for older payloads.
      sortValue: (d) => {
        const t = d.uploaded_at || d.created_at;
        return t ? new Date(t).getTime() : -1;
      },
      render: (d) => <span className="v3-muted">{d.uploaded_at || d.created_at || '—'}</span>,
    },
    {
      key: 'actions',
      header: '',
      accessor: 'id',
      render: (d) => (
        <button className="v3-btn v3-btn-sm" onClick={() => openDocumentEmissions(d.id)}>
          Emissions from this document
        </button>
      ),
    },
  ];

  const batchColumns = [
    {
      key: 'batch_name',
      header: 'Batch',
      accessor: 'batch_name',
      sortable: true,
      sortValue: (b) => (b.batch_name || b.id).toLowerCase(),
      render: (b) => <strong>{b.batch_name || b.id}</strong>,
      isHeader: true,
    },
    {
      key: 'status',
      header: 'Status',
      accessor: 'status',
      sortable: true,
      sortValue: (b) => (b.status || '').toLowerCase(),
      render: (b) => b.status || '—',
    },
    {
      key: 'created',
      header: 'Created',
      accessor: 'created_at',
      sortable: true,
      sortValue: (b) => (b.created_at ? new Date(b.created_at).getTime() : -1),
      render: (b) => <span className="v3-muted">{b.created_at || '—'}</span>,
    },
  ];

  if (loading) return <div className="v3-loading"><div className="spinner" />Loading documents…</div>;
  if (error && !org) return <ErrorState message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  return (
    <div className="v3-page">
      <div className="v3-page-header">
        <h1>Documents</h1>
        <p className="v3-subtitle">
          Upload and browse org documents (Supabase Storage via the V3 API).
        </p>
      </div>

      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note">{notice}</div>}

      <div className="v3-card">
        <h2>Upload document</h2>
        <div className="v3-form-grid">
          <div className="v3-form-group">
            <label>File</label>
            <input
              type="file"
              accept={ACCEPTED_DOCUMENT_TYPES}
              onChange={(e) => setFile(e.target.files[0] || null)}
            />
            <p className="v3-muted" style={{ marginTop: 4 }}>
              PDF, JPG/PNG/GIF/WEBP/BMP, CSV or Excel. The file is uploaded
              directly to private storage and validated by CarbonTally's security
              gate before it is processed.
            </p>
          </div>
          <div className="v3-form-group">
            <label>Data type</label>
            <select value={dataType} onChange={(e) => setDataType(e.target.value)}>
              <option value="utility">Utility</option>
              <option value="fuel">Fuel</option>
              <option value="scope3">Scope 3</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
        <div className="v3-actions">
          <button className="v3-btn v3-btn-primary" onClick={onUpload} disabled={uploading || !file}>
            {uploading ? `Uploading… ${progress}%` : 'Upload'}
          </button>
        </div>
        {uploading && (
          <div className="v3-muted" role="status" aria-live="polite" style={{ marginTop: 8 }}>
            {progress}% — do not close this window while the file is uploading.
            An unfinished upload is refused and can be started again.
          </div>
        )}
      </div>

      <div className="v3-card">
        <h2>Documents ({documents.length})</h2>
        <DataTable
          caption="Organisation documents"
          columns={documentColumns}
          rows={documents}
          clientPaginate
          defaultPageSize={10}
          resetKey={org?.id}
          emptyLabel="No documents uploaded yet."
        />

        {docEmissionsError && (
          <div className="v3-muted" style={{ marginTop: 12 }}>{docEmissionsError}</div>
        )}

        {docEmissions && (
          <div className="v3-result-card" style={{ marginTop: 12 }}>
            <h3>Emissions derived from {docEmissions.document_name}</h3>
            {docEmissions.emissions?.length === 0 ? (
              <p className="v3-empty">No emissions have been calculated from this document yet.</p>
            ) : (
              <table className="v3-table" style={{ marginTop: 8 }}>
                <thead>
                  <tr><th>Period</th><th>Activity</th><th>Scope</th><th>kg CO₂e</th><th>Snapshot</th></tr>
                </thead>
                <tbody>
                  {docEmissions.emissions.map((e) => (
                    <tr key={e.id}>
                      <td>{e.start_date || '—'}</td>
                      <td>{e.activity || e.source_file || '—'}</td>
                      <td>{e.scope || '—'}</td>
                      <td>{e.calculated_kg_co2e ?? '—'}</td>
                      <td className="v3-muted">{e.snapshot_id || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      <div className="v3-card">
        <h2>Upload batches ({batches.length})</h2>
        <DataTable
          caption="Upload batches"
          columns={batchColumns}
          rows={batches}
          clientPaginate
          defaultPageSize={10}
          resetKey={org?.id}
          emptyLabel="No upload batches yet."
        />
      </div>
    </div>
  );
}
