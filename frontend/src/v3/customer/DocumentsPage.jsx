// frontend/src/v3/customer/DocumentsPage.jsx
// Documents — upload to Supabase Storage via the V3 surface (/api/v3/uploads)
// and browse persisted documents (/api/v3/documents) + upload batches
// (/api/v3/batches). All org-scoped, real backend data.
import React, { useCallback, useEffect, useState } from 'react';
import { getDocumentEmissions, resolveV3Organization, v3ListDocuments, v3ListUploadBatches, v3UploadDocument } from '../api';
import { formatBytes } from '../utils';
import { ErrorState } from '../components/StateViews';
import DataTable from '../components/ui/DataTable';

export default function DocumentsPage() {
  const [org, setOrg] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [batches, setBatches] = useState([]);
  const [file, setFile] = useState(null);
  const [dataType, setDataType] = useState('utility');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
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
    setError('');
    setNotice('');
    try {
      await v3UploadDocument({ organization_id: org.id, data_type: dataType, file });
      setFile(null);
      setNotice('Document uploaded.');
      await load(org.id);
    } catch (e) {
      setError(e.message || 'Upload failed');
    } finally {
      setUploading(false);
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
      accessor: 'created_at',
      sortable: true,
      sortValue: (d) => (d.created_at ? new Date(d.created_at).getTime() : -1),
      render: (d) => <span className="v3-muted">{d.created_at || '—'}</span>,
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
            <input type="file" onChange={(e) => setFile(e.target.files[0] || null)} />
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
            {uploading ? 'Uploading…' : 'Upload'}
          </button>
        </div>
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
