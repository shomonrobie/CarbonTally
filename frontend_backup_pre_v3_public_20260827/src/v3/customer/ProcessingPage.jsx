// frontend/src/v3/customer/ProcessingPage.jsx
// Customer processing — manual-extraction batches and items over the V3 surface
// (/api/v3/manual-extraction/*). Real org-scoped backend data.
import React, { useCallback, useEffect, useState } from 'react';
import {
  resolveV3Organization,
  v3CreateExtractionBatch,
  v3CreateExtractionItem,
  v3ListExtractionBatches,
  v3ListExtractionItems,
} from '../api';
import { ErrorState } from '../components/StateViews';

const EMPTY_BATCH = { batch_name: '', total_documents: 0, total_pages: 0 };
const EMPTY_ITEM = { file_name: '', file_url: '', page_count: 1, document_type: '' };

export default function ProcessingPage() {
  const [org, setOrg] = useState(null);
  const [batches, setBatches] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [items, setItems] = useState({});
  const [batchForm, setBatchForm] = useState({ ...EMPTY_BATCH });
  const [itemForm, setItemForm] = useState({ ...EMPTY_ITEM });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async (organizationId) => {
    try {
      const result = await v3ListExtractionBatches(organizationId);
      setBatches(result.batches || []);
    } catch (e) {
      setError(e.message || 'Failed to load processing batches');
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

  const onCreateBatch = async () => {
    setError('');
    setNotice('');
    try {
      await v3CreateExtractionBatch(org.id, {
        batch_name: batchForm.batch_name,
        total_documents: Number(batchForm.total_documents) || 0,
        total_pages: Number(batchForm.total_pages) || 0,
      });
      setBatchForm({ ...EMPTY_BATCH });
      setNotice('Batch created.');
      await load(org.id);
    } catch (e) {
      setError(e.message || 'Failed to create batch');
    }
  };

  const toggleBatch = async (batchId) => {
    if (expanded === batchId) { setExpanded(null); return; }
    try {
      const result = await v3ListExtractionItems(batchId);
      setItems((prev) => ({ ...prev, [batchId]: result.items || [] }));
      setExpanded(batchId);
    } catch (e) {
      setError(e.message || 'Failed to load batch items');
    }
  };

  const onCreateItem = async (batchId) => {
    setError('');
    setNotice('');
    try {
      await v3CreateExtractionItem(batchId, {
        file_name: itemForm.file_name,
        file_url: itemForm.file_url,
        page_count: Number(itemForm.page_count) || 1,
        document_type: itemForm.document_type || null,
      });
      setItemForm({ ...EMPTY_ITEM });
      setNotice('Item added to batch.');
      const result = await v3ListExtractionItems(batchId);
      setItems((prev) => ({ ...prev, [batchId]: result.items || [] }));
      // Keep the batch list count authoritative (the API now returns item_count).
      setBatches((prev) =>
        prev.map((x) =>
          x.id === batchId ? { ...x, item_count: (x.item_count ?? 0) + 1 } : x
        )
      );
    } catch (e) {
      setError(e.message || 'Failed to add item');
    }
  };

  if (loading) return <div className="v3-loading"><div className="spinner" />Loading processing…</div>;
  if (error && !org) return <ErrorState message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  return (
    <div className="v3-page">
      <div className="v3-page-header">
        <h1>Processing</h1>
        <p className="v3-subtitle">Manual-extraction batches and items (org-scoped V3 surface).</p>
      </div>

      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note">{notice}</div>}

      <div className="v3-card">
        <h2>Batches ({batches.length})</h2>
        {batches.length === 0 ? (
          <div className="v3-empty">No processing batches yet.</div>
        ) : (
          <table className="v3-table">
            <thead>
              <tr><th>Batch</th><th>Status</th><th>Items</th><th>Created</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {batches.map((b) => (
                <React.Fragment key={b.id}>
                  <tr>
                    <td>{b.batch_name || b.id}</td>
                    <td>{b.status || '—'}</td>
                    <td>{b.item_count != null ? b.item_count : (items[b.id] || []).length}</td>
                    <td className="v3-muted">{b.created_at || '—'}</td>
                    <td>
                      <button className="v3-btn v3-btn-sm" onClick={() => toggleBatch(b.id)}>
                        {expanded === b.id ? 'Close' : 'Items'}
                      </button>
                    </td>
                  </tr>
                  {expanded === b.id && (
                    <tr>
                      <td colSpan={5}>
                        <div className="v3-inline-card">
                          <div className="v3-actions" style={{ marginTop: 0, marginBottom: 12 }}>
                            <input className="v3-input" placeholder="File name" value={itemForm.file_name} onChange={(e) => setItemForm({ ...itemForm, file_name: e.target.value })} />
                            <input className="v3-input" placeholder="File URL" value={itemForm.file_url} onChange={(e) => setItemForm({ ...itemForm, file_url: e.target.value })} />
                            <input className="v3-input" type="number" min="1" placeholder="Pages" value={itemForm.page_count} onChange={(e) => setItemForm({ ...itemForm, page_count: e.target.value })} />
                            <button className="v3-btn v3-btn-sm" onClick={() => onCreateItem(b.id)} disabled={!itemForm.file_name.trim()}>
                              Add item
                            </button>
                          </div>
                          {(items[b.id] || []).length === 0 ? (
                            <div className="v3-empty">No items in this batch.</div>
                          ) : (
                            <table className="v3-table">
                              <thead>
                                <tr><th>File</th><th>Status</th><th>Type</th></tr>
                              </thead>
                              <tbody>
                                {(items[b.id] || []).map((it) => (
                                  <tr key={it.id}>
                                    <td>{it.file_name}</td>
                                    <td>{it.status}</td>
                                    <td className="v3-muted">{it.document_type || '—'}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
