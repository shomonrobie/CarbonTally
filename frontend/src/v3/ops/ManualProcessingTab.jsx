// frontend/src/v3/ops/ManualProcessingTab.jsx
// FIN-06 / Manual Processing — CarbonTally Admin control plane.
//
// SUBSCRIPTION IS THE FIRST GATE (PO decision): a customer must be subscribed to
// a plan that includes Manual Processing before it can be enabled or have a
// Processing Entity configured. Everything shown here is the real server-side
// answer (/api/v3/admin/manual-processing/state); every rule is enforced
// server-side, so these controls are convenience only — a hidden or disabled
// control is never the security boundary.
import React, { useCallback, useEffect, useState } from 'react';
import {
  deleteManualProcessingProcessor,
  getManualProcessingState,
  listProcessingEntities,
  setManualProcessingGrant,
  setManualProcessingProcessor,
} from '../api';

const SCOPE_TYPES = [
  { value: 'organization', label: 'Organisation' },
  { value: 'consultant_firm', label: 'Consultant firm' },
  { value: 'consultant_client', label: 'Consultant client' },
];

const OUTCOME_COPY = {
  routable:
    'Automatic extraction failures will be routed to the configured Processing Entity.',
  no_processor_configured:
    'Manual Processing is enabled, but no Processing Entity is configured — failures are NOT routed.',
  not_enabled:
    'Manual Processing is not enabled for this scope. Extraction failures follow the normal path.',
  not_entitled:
    "This customer's subscribed plan does not include Manual Processing.",
};

export default function ManualProcessingTab({ canManage }) {
  const [scopeType, setScopeType] = useState('organization');
  const [scopeId, setScopeId] = useState('');
  const [state, setState] = useState(null);
  const [entities, setEntities] = useState([]);
  const [selectedEntity, setSelectedEntity] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listProcessingEntities(100, 0, 'active')
      .then((r) => setEntities((r && r.entities) || []))
      .catch(() => setEntities([]));
  }, []);

  const load = useCallback(async () => {
    if (!scopeType || !scopeId.trim()) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const data = await getManualProcessingState(scopeType, scopeId.trim());
      setState(data);
      const current = data.scope_processor && data.scope_processor.processing_entity_id;
      setSelectedEntity(current || '');
    } catch (e) {
      setState(null);
      setError(e.message || 'Unable to load Manual Processing state.');
    } finally {
      setBusy(false);
    }
  }, [scopeType, scopeId]);

  const entitled = !!(state && state.entitlement && state.entitlement.entitled);
  const enabled = !!(state && state.governance && state.governance.enabled);
  const effective = state && state.effective ? state.effective.outcome : null;

  const run = async (action, successMessage) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await action();
      setNotice(successMessage);
      await load();
    } catch (e) {
      setError(e.message || 'The change could not be saved.');
    } finally {
      setBusy(false);
    }
  };

  const toggleEnabled = () =>
    run(
      () =>
        setManualProcessingGrant({
          scope_type: scopeType,
          scope_id: scopeId.trim(),
          enabled: !enabled,
        }),
      enabled ? 'Manual Processing disabled.' : 'Manual Processing enabled.',
    );

  const assignProcessor = () =>
    run(
      () =>
        setManualProcessingProcessor({
          scope_type: scopeType,
          scope_id: scopeId.trim(),
          processing_entity_id: selectedEntity,
        }),
      'Processing Entity configured.',
    );

  const removeProcessor = () =>
    run(
      () => deleteManualProcessingProcessor(scopeType, scopeId.trim()),
      'Processor configuration removed.',
    );

  return (
    <div>
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Manual Processing — subscription to routing</h3>
        <div className="workspace-grid">
          <div className="workspace-field">
            <label htmlFor="mp-scope-type">Scope</label>
            <select
              id="mp-scope-type"
              value={scopeType}
              onChange={(e) => setScopeType(e.target.value)}
            >
              {SCOPE_TYPES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
          <div className="workspace-field">
            <label htmlFor="mp-scope-id">
              {SCOPE_TYPES.find((s) => s.value === scopeType)?.label} id
            </label>
            <input
              id="mp-scope-id"
              type="text"
              value={scopeId}
              placeholder="UUID / organisation id"
              onChange={(e) => setScopeId(e.target.value)}
            />
          </div>
          <div className="workspace-actions">
            <button
              className="v3-btn primary"
              onClick={load}
              disabled={busy || !scopeId.trim()}
            >
              {busy ? 'Loading…' : 'Load state'}
            </button>
          </div>
        </div>
      </div>

      {state && (
        <>
          {!entitled && (
            <div className="v3-ops-error">
              This customer is <strong>not entitled</strong> to Manual Processing. It
              requires a subscription plan that includes the capability. If the plan
              already includes it, verify the customer has an ACTIVE subscription.
            </div>
          )}

          <div className="workspace-pane" style={{ marginBottom: 16 }}>
            <h3>Subscription entitlement</h3>
            <table className="v3-ops-table">
              <tbody>
                <tr><td>Entitled</td><td>{entitled ? 'Yes' : 'No'}</td></tr>
                <tr>
                  <td>Organisations in scope</td>
                  <td>{(state.organizations || []).join(', ') || '—'}</td>
                </tr>
                <tr>
                  <td>Not entitled</td>
                  <td>
                    {(state.entitlement.organizations_not_entitled || []).join(', ') || '—'}
                  </td>
                </tr>
                <tr>
                  <td>Plans</td>
                  <td>
                    {Object.entries(state.entitlement.plan_codes || {})
                      .map(([org, code]) => `${org}: ${code || 'no active plan'}`)
                      .join(' · ') || '—'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="workspace-pane" style={{ marginBottom: 16 }}>
            <h3>Manual Processing activation</h3>
            <table className="v3-ops-table">
              <tbody>
                <tr><td>Enabled</td><td>{enabled ? 'Yes' : 'No'}</td></tr>
                <tr>
                  <td>Deciding scope</td>
                  <td>
                    {state.governance.source_level === 'explicit'
                      ? `${state.governance.source_scope_type} (${state.governance.source_scope_id})`
                      : 'platform default (OFF)'}
                  </td>
                </tr>
                <tr>
                  <td>Effective outcome</td>
                  <td>{effective} — {OUTCOME_COPY[effective] || ''}</td>
                </tr>
              </tbody>
            </table>
            <div className="workspace-actions" style={{ marginTop: 8 }}>
              <button
                className="v3-btn primary"
                onClick={toggleEnabled}
                disabled={!canManage || busy || !entitled}
                title={
                  !entitled
                    ? 'Requires a subscription plan that includes Manual Processing'
                    : undefined
                }
              >
                {enabled ? 'Disable Manual Processing' : 'Enable Manual Processing'}
              </button>
            </div>
          </div>

          <div className="workspace-pane">
            <h3>Configured Processing Entity</h3>
            <table className="v3-ops-table">
              <tbody>
                <tr>
                  <td>Configured at this scope</td>
                  <td>
                    {state.scope_processor
                      ? `${state.scope_processor.processing_entity_id}${
                          state.scope_processor.active ? '' : ' (inactive)'
                        }`
                      : 'None'}
                  </td>
                </tr>
                <tr>
                  <td>Effective processor</td>
                  <td>
                    {state.effective && state.effective.processing_entity_id
                      ? state.effective.processing_entity_id
                      : 'None — failure routing is blocked'}
                  </td>
                </tr>
              </tbody>
            </table>
            <div className="workspace-grid" style={{ marginTop: 8 }}>
              <div className="workspace-field">
                <label htmlFor="mp-entity">Processing Entity</label>
                <select
                  id="mp-entity"
                  value={selectedEntity}
                  disabled={!canManage || !entitled || busy}
                  onChange={(e) => setSelectedEntity(e.target.value)}
                >
                  <option value="">Select an active Processing Entity…</option>
                  {entities.map((e) => (
                    <option key={e.id} value={e.id}>{e.name || e.id}</option>
                  ))}
                </select>
              </div>
              <div className="workspace-actions">
                <button
                  className="v3-btn primary"
                  onClick={assignProcessor}
                  disabled={!canManage || !entitled || busy || !selectedEntity}
                >
                  Save processor
                </button>
                <button
                  className="v3-btn"
                  onClick={removeProcessor}
                  disabled={!canManage || !entitled || busy || !state.scope_processor}
                >
                  Remove processor
                </button>
              </div>
            </div>
            <p className="muted" style={{ marginTop: 8 }}>
              Configuring a processor does not enable Manual Processing — enablement is
              the separate step above. No Processing Entity is assumed unless it is
              configured here.
            </p>
          </div>
        </>
      )}

      {!state && !error && (
        <div className="workspace-pane">
          <p className="muted">
            Choose a scope and enter its id to see the customer&apos;s Manual Processing
            entitlement, activation state and configured Processing Entity.
          </p>
        </div>
      )}
    </div>
  );
}
