// frontend/src/v3/consultant/ConsultantItemPage.jsx
// CON-3 / Phase G — dedicated routed processing workspace for a consultant's
// client item. The shared /api/v3/processing/* surface is consultant-authorized
// (active consultant_clients grant), so the same ExtractionPanel drives the
// real durable pipeline: extract → map → validate → calculate → evidence.
// Route: /consultant/items/:clientId/:itemId
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  calculateItem,
  extractItem,
  getClientProcessingItems,
  getItemWorkspace,
  getMappingOptions,
  mapItem,
  startItem,
} from '../api';
import ExtractionPanel from '../ops/ExtractionPanel';
import { Button, LoadingState, ErrorState } from '../components/ui';

const INTERNAL_API = {
  startItem,
  extractItem,
  mapItem,
  calculateItem,
  getMappingOptions,
};

export default function ConsultantItemPage() {
  const { clientId, itemId } = useParams();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async (id) => {
    setLoading(true);
    setError('');
    try {
      const ws = await getItemWorkspace(id);
      setWorkspace(ws);
      const list = await getClientProcessingItems(clientId);
      setItems(list.items || []);
    } catch (e) {
      setError(e.message || 'Failed to open item workspace');
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => {
    if (itemId) load(itemId);
  }, [itemId, load]);

  const onNavigate = useCallback((nextId) => {
    navigate(`/consultant/items/${encodeURIComponent(clientId)}/${encodeURIComponent(nextId)}`);
  }, [clientId, navigate]);

  if (loading) return <LoadingState label="Loading item workspace…" />;
  if (error) return <ErrorState message={error} onRetry={() => load(itemId)} />;
  if (!workspace) return <ErrorState message="Item not found." onRetry={() => load(itemId)} />;

  return (
    <div className="v3-ops-page">
      <div className="v3-ops-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h1>Client item workspace</h1>
          <div className="subtitle">
            {workspace.organization?.name ? `${workspace.organization.name} · ` : ''}
            {workspace.item?.file_name || '—'} · {workspace.item?.status || ''}
          </div>
        </div>
        <Button variant="secondary" size="sm" onClick={() => navigate(`/consultant?client=${encodeURIComponent(clientId)}&view=workspace`)}>
          ← Back to client workspace
        </Button>
      </div>

      <ExtractionPanel
        item={workspace.item}
        items={items}
        api={INTERNAL_API}
        onItemChange={onNavigate}
        mode="staff"
        suggestions={workspace.source?.ocr_suggestions || null}
        validation={(workspace.validation && workspace.validation.findings) || []}
      />
    </div>
  );
}
