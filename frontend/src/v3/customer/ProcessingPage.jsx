// frontend/src/v3/customer/ProcessingPage.jsx
// CL-54 - genuine customer processing workspace:
//   * upload documents (V3 surface - the worker/operator pipeline takes over)
//   * processing status summary (per-stage counts)
//   * every processing item with live status -> deep link into the item workspace
//   * durable automatic-processing jobs (Phase A) with retry/confirm actions
// All reads/writes are org-scoped /api/v3/* endpoints; the staff /api/v3/ops/*
// surface is never used here.
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  confirmProcessingJob,
  getProcessingJobs,
  getProcessingStatus,
  resolveV3Organization,
  retryProcessingJob,
  v3ListExtractionBatches,
  v3ListExtractionItems,
  v3UploadDocument,
} from '../api';
import { formatBytes } from '../utils';
import { Button, EmptyState, ErrorState, LoadingState, StatusBadge } from '../components/ui';

const STAGE_ORDER = ['source', 'extraction', 'mapping', 'validation', 'calculation', 'review', 'approval'];

export default function ProcessingPage() {
  const navigate = useNavigate();
  const [org, setOrg] = useState(null);
  const [status, setStatus] = useState(null);
  const [items, setItems] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [file, setFile] = useState(null);
  const [dataType, setDataType] = useState('utility');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busyJob, setBusyJob] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async (organizationId) => {
    setError('');
    try {
      const [statusResult, jobsResult, batches] = await Promise.all([
        getProcessingStatus(organizationId),
        getProcessingJobs(organizationId, { limit: 200 }).catch(() => ({ jobs: [] })),
        v3ListExtractionBatches(organizationId).catch(() => ({ batches: [] })),
      ]);
      setStatus(statusResult);
      setJobs(jobsResult.jobs || []);
      const batchList = batches.batches || [];
      const rows = [];
      for (const batch of batchList) {
        try {
          const result = await v3ListExtractionItems(batch.id);
          (result.items || []).forEach((it) => rows.push({ ...it, batch_name: batch.batch_name }));
        } catch (_e) {
          /* skip batches that cannot be listed */
        }
      }
      rows.sort((a, b) => (a.created_at > b.created_at ? -1 : 1));
      setItems(rows);
    } catch (e) {
      setError(e.message || 'Failed to load processing');
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
        setError(e.message || 'Failed to load processing');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [load, retryCount]);

  // Light polling while anything is still in flight.
  useEffect(() => {
    if (!org) return undefined;
    const inFlight = items.some(
      (i) => !['approved', 'rejected', 'qc_approved', 'qc_rejected', 'completed', 'failed'].includes(i.status)
    ) || jobs.some(
      (j) => ['enqueued', 'ingesting', 'extracting', 'mapping', 'validating', 'calculating'].includes(j.stage)
    );
    if (!inFlight) return undefined;
    const timer = setInterval(() => { load(org.id); }, 10000);
    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [org, items, jobs]);

  const onUpload = async () => {
    if (!file || !org) return;
    setUploading(true);
    setError('');
    setNotice('');
    try {
      await v3UploadDocument({ organization_id: org.id, data_type: dataType, file });
      setFile(null);
      setNotice('Document uploaded - automatic processing has been enqueued.');
      await load(org.id);
    } catch (e) {
      setError(e.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const onRetryJob = async (jobId) => {
    setBusyJob(jobId);
    setError('');
    try {
      await retryProcessingJob(jobId);
      await load(org.id);
      setNotice('Job re-enqueued.');
    } catch (e) {
      setError(e.message || 'Failed to retry job');
    } finally {
      setBusyJob('');
    }
  };

  const onConfirmJob = async (jobId) => {
    setBusyJob(jobId);
    setError('');
    try {
      await confirmProcessingJob(jobId, { stage: 'enqueued', reset_attempts: true });
      await load(org.id);
      setNotice('Job confirmed - the pipeline will resume it.');
    } catch (e) {
      setError(e.message || 'Failed to confirm job');
    } finally {
      setBusyJob('');
    }
  };

  if (loading) return <LoadingState label="Loading processing..." />;
  if (error && !org) return <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  const pipeline = status?.pipeline || {};
  const totalItems = status?.total_items ?? items.length;
  return (
    <div className="v3-page">
      <header className="v3-page-header">
        <h1>Processing</h1>
        <p className="v3-subtitle">
          Upload a document and follow it through extraction, mapping, validation, calculation and review - or pick up an
          item in flight.
        </p>
      </header>

      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note" style={{ marginBottom: 14 }}>{notice}</div>}

      <div className="v3-card">
        <h2>Upload a document</h2>
        <div className="v3-actions" style={{ marginTop: 0 }}>
          <input
            className="v3-input"
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,.csv,.xlsx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <select className="v3-input" value={dataType} onChange={(e) => setDataType(e.target.value)}>
            <option value="utility">Utility</option>
            <option value="fuel">Fuel</option>
            <option value="scope3">Scope 3</option>
          </select>
          <Button variant="primary" onClick={onUpload} disabled={uploading || !file}>
            {uploading ? 'Uploading...' : 'Upload & process'}
          </Button>
        </div>
        {file && <p className="v3-muted" style={{ margin: '8px 0 0' }}>{file.name} · {formatBytes(file.size)}</p>}
      </div>

      <div className="v3-card">
        <h2>Pipeline status</h2>
        {Object.keys(pipeline).length === 0 ? (
          <div className="v3-empty">No processing activity yet.</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10 }}>
            {STAGE_ORDER.filter((s) => pipeline[s] != null && pipeline[s] !== 0).map((stage) => (
              <div key={stage} className="v3-inline-card" style={{ margin: 0, textAlign: 'center' }}>
                <div style={{ fontWeight: 700, fontSize: 18 }}>{pipeline[stage]}</div>
                <div className="v3-muted" style={{ fontSize: 12, textTransform: 'capitalize' }}>{stage}</div>
              </div>
            ))}
          </div>
        )}
        <p className="v3-muted" style={{ margin: '10px 0 0' }}>
          {totalItems} item{totalItems === 1 ? '' : 's'} · {status?.pct_complete ?? 0}% complete
        </p>
      </div>
      <div className="v3-card">
        <h2>Items ({items.length})</h2>
        {items.length === 0 ? (
          <EmptyState icon="documents" title="No processing items">Upload a document to create the first processing item.</EmptyState>
        ) : (
          <table className="v3-table">
            <thead>
              <tr><th>Item</th><th>Batch</th><th>Status</th><th>Type</th><th>Calculated</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id}>
                  <td><strong>{it.file_name}</strong></td>
                  <td className="v3-muted">{it.batch_name || '—'}</td>
                  <td><StatusBadge status={it.status} /></td>
                  <td className="v3-muted">{it.document_type || '—'}</td>
                  <td>{it.calculated_emissions_kg_co2e != null ? `${it.calculated_emissions_kg_co2e} kg` : '—'}</td>
                  <td>
                    <Button variant="secondary" size="sm" onClick={() => navigate(`/processing/${it.id}`)}>
                      Open workspace
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="v3-card">
        <h2>Automatic processing jobs ({jobs.length})</h2>
        {jobs.length === 0 ? (
          <div className="v3-empty">No automatic-processing jobs yet.</div>
        ) : (
          <table className="v3-table">
            <thead>
              <tr><th>Document</th><th>Stage</th><th>Status</th><th>Attempt</th><th>Detail</th><th></th></tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.id}>
                  <td><strong>{j.file_name}</strong></td>
                  <td>{j.stage_label || j.stage}</td>
                  <td><StatusBadge status={j.status} /></td>
                  <td className="v3-muted">{j.attempt_count}/{j.max_attempts}</td>
                  <td className="v3-muted" style={{ maxWidth: 260 }}>
                    {j.manual_review_reason || (j.completeness != null ? `completeness ${Math.round(j.completeness * 100)}%` : '')}
                  </td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    {(j.stage === 'blocked' || j.stage === 'failed') && (
                      <>
                        <Button variant="secondary" size="sm" onClick={() => onRetryJob(j.id)} disabled={busyJob === j.id}>
                          Retry
                        </Button>{' '}
                        {j.stage === 'blocked' && (
                          <Button variant="secondary" size="sm" onClick={() => onConfirmJob(j.id)} disabled={busyJob === j.id}>
                            Confirm
                          </Button>
                        )}
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
