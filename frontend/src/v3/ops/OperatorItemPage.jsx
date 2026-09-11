// frontend/src/v3/ops/OperatorItemPage.jsx
// CL-59 — dedicated routed item workspace for the operator queue.
// List page (/ops) -> dedicated route (/ops/items/:itemId) -> Back to queue.
// Browser history, refresh, deep links and the shared ExtractionPanel (with
// Previous/Next over the server-authorised batch item list) all work because
// the workspace is a first-class route, not inline state under the queue.
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  calculateItem,
  extractItem,
  getItemWorkspace,
  getMappingOptions,
  getOpsBatchItems,
  mapItem,
  startItem,
} from '../api';
import ExtractionPanel from './ExtractionPanel';
import { Button, LoadingState, ErrorState } from '../components/ui';

const INTERNAL_API = {
  startItem,
  extractItem,
  mapItem,
  calculateItem,
  getMappingOptions,
};

export default function OperatorItemPage() {
  const { itemId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [workspace, setWorkspace] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  // CL-59 + WS4D — queue-state restoration: the Assignments surface deep-links
  // here with ?tab=assignments so "Back to queue" returns to the tab the item
  // was opened from (default data entry).
  const backTab = searchParams.get('tab') || 'data-entry';

  const load = useCallback(async (id) => {
    setLoading(true);
    setError('');
    try {
      const ws = await getItemWorkspace(id);
      setWorkspace(ws);
      if (ws.batch?.id) {
        const batchItems = await getOpsBatchItems(ws.batch.id);
        setItems(batchItems.items || []);
      } else {
        setItems([]);
      }
    } catch (e) {
      setError(e.message || 'Failed to open item workspace');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (itemId) load(itemId);
  }, [itemId, load]);

  const onNavigate = useCallback((nextId) => {
    navigate(`/ops/items/${encodeURIComponent(nextId)}`);
  }, [navigate]);

  if (loading) return <LoadingState label="Loading item workspace…" />;
  if (error) return <ErrorState message={error} onRetry={() => load(itemId)} />;
  if (!workspace) return <ErrorState message="Item not found." onRetry={() => load(itemId)} />;

  return (
    <div className="v3-ops-page">
      <div className="v3-ops-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h1>Item workspace</h1>
          <div className="subtitle">
            {workspace.organization?.name ? `${workspace.organization.name} · ` : ''}
            {workspace.item?.file_name || '—'} · {workspace.item?.status || ''}
          </div>
        </div>
        <Button variant="secondary" size="sm" onClick={() => navigate(`/ops?tab=${backTab}`)}>
          ← Back to queue
        </Button>
      </div>

      <ExtractionPanel
        item={workspace.item}
        items={items}
        api={INTERNAL_API}
        onItemChange={onNavigate}
        onSaved={() => load(itemId)}
        mode="staff"
        suggestions={workspace.source?.ocr_suggestions || null}
        validation={(workspace.validation && workspace.validation.findings) || []}
      />
    </div>
  );
}
