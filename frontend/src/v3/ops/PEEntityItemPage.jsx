// frontend/src/v3/ops/PEEntityItemPage.jsx
// Phase G (G5) — dedicated routed workspace for a Processing Entity item.
// List page (entity workspace) → /pe/items/:entityId/:itemId → Back to
// entity work. Deep-linkable, refresh-safe, Previous/Next over the entity's
// batch items. All data flows through the entity-scoped endpoints (own entity
// only, server-enforced); the D20 no-download boundary is untouched.
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  entityCalculateItem,
  entityClarifyItem,
  entityExtractItem,
  entityMapItem,
  entityStartItem,
  getEntityExtractionBatchItems,
  getEntityExtractionBatches,
  getEntityExtractionItem,
  getEntityMappingOptions,
} from '../api';
import ExtractionPanel from './ExtractionPanel';
import { Button, LoadingState, ErrorState } from '../components/ui';
import './ops.css';

const ENTITY_API = (entityId) => ({
  startItem: (itemId, stage) => entityStartItem(entityId, itemId, stage),
  extractItem: (itemId, data) => entityExtractItem(entityId, itemId, data),
  mapItem: (itemId, payload) => entityMapItem(entityId, itemId, payload),
  calculateItem: (itemId, payload) => entityCalculateItem(entityId, itemId, payload),
  getMappingOptions: (itemId, params) => getEntityMappingOptions(entityId, itemId, params),
});

export default function PEEntityItemPage() {
  const { entityId, itemId } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [items, setItems] = useState([]);
  const [suggestions, setSuggestions] = useState(null);
  const [validation, setValidation] = useState([]);
  const [clarify, setClarify] = useState('');
  const [clarifyError, setClarifyError] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async (id) => {
    setLoading(true);
    setError('');
    try {
      const body = await getEntityExtractionItem(entityId, id);
      setItem(body.item);
      setSuggestions(body.suggestions || null);
      setValidation(body.validation?.findings || []);
      // Resolve the item's batch for the Previous/Next item list.
      const batchId = body.item?.batch_id;
      if (batchId) {
        const batchBody = await getEntityExtractionBatchItems(entityId, batchId);
        setItems(batchBody.items || []);
      } else {
        const batches = await getEntityExtractionBatches(entityId);
        const batch = (batches.batches || []).find((b) => b.id === body.item?.batch_id);
        if (batch) {
          const batchBody = await getEntityExtractionBatchItems(entityId, batch.id);
          setItems(batchBody.items || []);
        }
      }
    } catch (e) {
      setError(e.message || 'Failed to open item workspace');
    } finally {
      setLoading(false);
    }
  }, [entityId]);

  useEffect(() => {
    if (itemId) load(itemId);
  }, [itemId, load]);

  const onNavigate = useCallback((nextId) => {
    navigate(`/pe/items/${encodeURIComponent(entityId)}/${encodeURIComponent(nextId)}`);
  }, [entityId, navigate]);

  const onClarify = async () => {
    if (!item || !clarify.trim()) return;
    setClarifyError('');
    try {
      await entityClarifyItem(entityId, item.id, { title: clarify.trim() });
      setClarify('');
    } catch (e) {
      setClarifyError(e.message || 'Clarification request failed');
    }
  };

  if (loading) return <LoadingState label="Loading entity item workspace…" />;
  if (error) return <ErrorState message={error} onRetry={() => load(itemId)} />;
  if (!item) return <ErrorState message="Item not found." onRetry={() => load(itemId)} />;

  return (
    <div className="v3-ops-page">
      <div className="v3-ops-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h1>Entity item workspace</h1>
          <div className="subtitle">
            {item.file_name || '—'} · {item.status || 'pending'}
          </div>
        </div>
        <Button variant="secondary" size="sm" onClick={() => navigate(`/ops?tab=entity`)}>
          ← Back to entity work
        </Button>
      </div>

      <div className="workspace-pane" style={{ marginBottom: 12 }}>
        <h3>Mediated clarification (to CarbonTally — never the customer)</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <input
            value={clarify}
            onChange={(e) => setClarify(e.target.value)}
            placeholder="What needs clarification?"
            style={{ flex: 1, minWidth: 220 }}
          />
          <button className="v3-btn" onClick={onClarify} disabled={!clarify.trim()}>Request clarification</button>
        </div>
      </div>

      <ExtractionPanel
        item={item}
        items={items}
        api={ENTITY_API(entityId)}
        onItemChange={onNavigate}
        mode="entity"
        suggestions={suggestions}
        validation={validation}
      />
    </div>
  );
}
