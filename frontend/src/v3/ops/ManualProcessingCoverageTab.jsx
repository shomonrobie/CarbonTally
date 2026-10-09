// frontend/src/v3/ops/ManualProcessingCoverageTab.jsx
// CT-MP-SUB-004 — Manual Processing COMMERCIAL COVERAGE (Platform Admin).
//
// CT-UX-MP-SUB-003 §2/§8 require the Internal Operations experience to make the
// distinction visible:
//
//   [ Commercial Coverage ]  <- THIS tab: who purchased what, who is covered
//   [ Manual Processing   ]  <- the existing tab: governance -> configured PE
//
// Commercial entitlement, FIN-06 governance and Processing Entity configuration
// are three SEPARATE concepts (§1) and are never collapsed into one status here.
//
// This component only WIRES the already-approved CT-MP-SUB-003 Admin endpoints
// (`backend/api/manual_processing_admin.py`). No pricing, capacity tier, plan
// name or commercial rule is invented: every value shown is the server's own
// projection, and every write is re-checked server-side — a hidden or disabled
// control is never the security boundary.
import React, { useCallback, useEffect, useState } from 'react';
import {
  allocateAdminManualProcessingClient,
  getAdminManualProcessingClientState,
  getAdminManualProcessingCoverage,
  releaseAdminManualProcessingAllocation,
  searchAdminManualProcessingOrganizations,
} from '../api';
import Badge from '../components/ui/Badge';
import Alert from '../components/ui/Alert';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/StateViews';

const MODE_LABEL = {
  SELECTED_CLIENTS: 'SELECTED CLIENTS',
  ALL_ELIGIBLE_CLIENTS: 'ALL ELIGIBLE CLIENTS',
};

const modeLabel = (mode) => MODE_LABEL[mode] || mode || '—';

// Spec §7 — Admin empty state for an organisation with no consultant coverage.
const NO_COVERAGE_COPY = (
  <>
    <p style={{ margin: 0 }}>No consultant coverage configured for this organization.</p>
    <p style={{ margin: '6px 0 0' }}>
      Configure the firm&apos;s commercial coverage first (the firm&apos;s own
      organisation subscription plan carries the coverage).
    </p>
  </>
);

// Spec §7 — allocation failure copy. It must never reveal whether another
// organisation&apos;s records exist.
const ALLOCATION_ERROR_COPY = (
  <>
    <p style={{ margin: 0 }}>Unable to allocate this client.</p>
    <p style={{ margin: '6px 0 0' }}>Possible reasons:</p>
    <ul style={{ margin: '4px 0 0 18px' }}>
      <li>the client is not eligible;</li>
      <li>allocation capacity is exhausted;</li>
      <li>coverage is no longer active.</li>
    </ul>
    <p style={{ margin: '6px 0 0' }}>Refresh the coverage state and try again.</p>
  </>
);

function Meter({ allocated, capacity }) {
  if (capacity === null || capacity === undefined || capacity === 0) return null;
  const pct = Math.min(100, Math.round((allocated / capacity) * 100));
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 6 }}>
      <div
        role="progressbar"
        aria-valuenow={allocated}
        aria-valuemin={0}
        aria-valuemax={capacity}
        aria-label="Selected-client capacity used"
        style={{
          flex: '0 0 180px',
          height: 10,
          borderRadius: 999,
          background: 'var(--ct-color-border)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            background: pct >= 100 ? '#c53030' : 'var(--ct-color-primary)',
          }}
        />
      </div>
      <span className="ops-muted">{pct}%</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// F-11 — searchable client-organisation selector
// ---------------------------------------------------------------------------
// Operators must not type raw organisation UUIDs. This combobox searches by
// NAME through the read-only admin lookup; the internal id stays
// backend-controlled. Choosing a result performs NO state change (the caller
// must press an explicit action button afterwards), and the server re-validates
// whatever id is ultimately submitted.

function ClientPicker({ onSelect, selected, disabled }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState('idle'); // idle | loading | ready | error
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const term = query.trim();
    // Do not re-search for the name we just selected (that would immediately
    // reopen the list); the input simply displays the chosen organisation.
    if (selected && term && term === (selected.name || '')) {
      setResults([]);
      setStatus('idle');
      setOpen(false);
      return undefined;
    }
    if (term.length < 2) {
      setResults([]);
      setStatus('idle');
      setError('');
      setOpen(false);
      return undefined;
    }
    let cancelled = false;
    setStatus('loading');
    const timer = setTimeout(async () => {
      try {
        const data = await searchAdminManualProcessingOrganizations(term, {
          limit: 20,
        });
        if (cancelled) return;
        setResults(data.organizations || []);
        setStatus('ready');
        setOpen(true);
      } catch (e) {
        if (cancelled) return;
        setResults([]);
        setError(e.message || 'Unable to search organisations.');
        setStatus('error');
        setOpen(false);
      }
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, selected]);

  return (
    <div className="workspace-field">
      <label htmlFor="mp-cov-org-search">Organisation</label>
      <input
        id="mp-cov-org-search"
        type="text"
        role="combobox"
        autoComplete="off"
        aria-expanded={open}
        aria-controls="mp-cov-org-results"
        aria-describedby="mp-cov-org-help"
        placeholder="Search by organisation name…"
        value={query}
        disabled={disabled}
        onChange={(e) => setQuery(e.target.value)}
      />
      <p id="mp-cov-org-help" className="ops-muted" style={{ margin: '4px 0 0' }}>
        Search by name. The internal organisation id is resolved and validated
        server-side; selecting a client performs no change.
      </p>

      {status === 'loading' && (
        <p className="ops-muted" role="status">
          Searching organisations…
        </p>
      )}
      {status === 'error' && (
        <div className="v3-ops-error" role="alert">
          {error}
        </div>
      )}
      {open && status === 'ready' && results.length === 0 && (
        <p className="ops-muted" role="status">
          No organisations match “{query.trim()}”.
        </p>
      )}
      {open && results.length > 0 && (
        <ul
          id="mp-cov-org-results"
          role="listbox"
          aria-label="Organisation search results"
          style={{
            listStyle: 'none',
            margin: '8px 0 0',
            padding: 0,
            maxHeight: 220,
            overflowY: 'auto',
            border: '1px solid var(--ct-color-border)',
            borderRadius: 6,
          }}
        >
          {results.map((o) => (
            <li
              key={o.id}
              role="option"
              aria-selected={selected && selected.id === o.id}
              style={{ margin: 0 }}
            >
              <button
                type="button"
                className="v3-btn"
                style={{
                  display: 'block',
                  width: '100%',
                  textAlign: 'left',
                  border: 0,
                  borderRadius: 0,
                }}
                onClick={() => {
                  onSelect(o);
                  setQuery(o.name || '');
                  setOpen(false);
                }}
              >
                {o.name || 'Unnamed organisation'}
                <span className="ops-muted"> · {o.id}</span>
                {o.is_active === false && (
                  <span className="ops-muted"> · inactive</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}

      {selected && (
        <p className="ops-muted" data-testid="mp-cov-org-selected" style={{ margin: '6px 0 0' }}>
          Selected: <strong>{selected.name || 'Unnamed organisation'}</strong>
        </p>
      )}
    </div>
  );
}


function StateRow({ label, children }) {
  return (
    <tr>
      <th scope="row">{label}</th>
      <td>{children}</td>
    </tr>
  );
}


// ---------------------------------------------------------------------------
// Admin — consultant firm commercial coverage (§2, §5)
// ---------------------------------------------------------------------------


function FirmCoveragePanel({
  coverage,
  busy,
  onRelease,
  onInspectClient,
  clientNames = {},
  pendingRelease = '',
  onAskRelease,
  onCancelRelease,
}) {
  if (!coverage) return null;
  const mode = coverage.mode;
  const selected = mode === 'SELECTED_CLIENTS';
  const allocated = coverage.allocated || 0;
  const capacity = coverage.capacity;
  const unallocated = coverage.unallocated_eligible_clients || [];
  const allocations = coverage.allocations || [];
  const activeAllocations = allocations.filter((a) => a.state === 'active');
  // F-11 — prefer the server-resolved human name, fall back to the id only when
  // no name is available (never fabricate one).
  const label = (id) => (clientNames[id] ? `${clientNames[id]} · ${id}` : id);

  if (!coverage.enabled) {
    return (
      <Card title="Consultant coverage">
        <EmptyState title="No coverage configured">{NO_COVERAGE_COPY}</EmptyState>
      </Card>
    );
  }

  return (
    <Card
      title="Consultant coverage"
      actions={
        <Badge tone={selected ? 'info' : 'primary'}>{modeLabel(mode)}</Badge>
      }
    >
      <table className="v3-ops-table">
        <tbody>
          <StateRow label="Coverage mode">{modeLabel(mode)}</StateRow>
          {selected ? (
            <>
              <StateRow label="Purchased capacity">
                {capacity === null || capacity === undefined
                  ? 'Not configured'
                  : `${capacity} clients`}
              </StateRow>
              <StateRow label="Allocated">
                {allocated} / {capacity === null || capacity === undefined ? '—' : capacity}
              </StateRow>
              <StateRow label="Available">
                {coverage.available === null || coverage.available === undefined
                  ? '—'
                  : coverage.available}
              </StateRow>
            </>
          ) : (
            <>
              <StateRow label="Eligible clients">
                {(coverage.eligible_clients || []).length}
              </StateRow>
              <StateRow label="Covered automatically">
                {(coverage.eligible_clients || []).length}
              </StateRow>
              <StateRow label="Future eligible clients">Automatically covered</StateRow>
              <StateRow label="Eligibility source">
                Active consultant-client relationship
              </StateRow>
            </>
          )}
          <StateRow label="Plan">
            {coverage.plan_code || '—'}
            {coverage.plan_version ? ` · v${coverage.plan_version}` : ''}
          </StateRow>
        </tbody>
      </table>

      {selected && <Meter allocated={allocated} capacity={capacity} />}

      {selected && coverage.over_allocated && (
        <Alert tone="warning" title="Over-allocated">
          More clients hold an active allocation than the purchased capacity.
          Release allocations or increase purchased capacity.
        </Alert>
      )}

      <h3 style={{ marginTop: 18 }}>Covered clients</h3>
      {activeAllocations.length === 0 ? (
        <EmptyState title="No clients covered yet">
          {selected
            ? 'Select an eligible client below to allocate selected-client capacity.'
            : 'Eligible clients are covered automatically under ALL ELIGIBLE CLIENTS coverage.'}
        </EmptyState>
      ) : (
        <div className="ops-table-wrap">
          <table className="ops-table">
            <thead>
              <tr>
                <th scope="col">Client</th>
                <th scope="col">Coverage</th>
                <th scope="col">Allocated</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              {activeAllocations.map((a) => (
                <tr key={a.id}>
                  <td>{label(a.organization_id)}</td>
                  <td><Badge tone="success">Active</Badge></td>
                  <td>{a.allocated_at ? String(a.allocated_at).slice(0, 10) : '—'}</td>
                  <td style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      className="v3-btn"
                      onClick={() => onInspectClient(a.organization_id)}
                    >
                      View client state
                    </button>
                    {pendingRelease === a.id ? (
                      <>
                        <button
                          type="button"
                          className="v3-btn danger"
                          disabled={busy}
                          onClick={() => onRelease(a.id)}
                        >
                          Confirm release
                        </button>
                        <button
                          type="button"
                          className="v3-btn"
                          disabled={busy}
                          onClick={onCancelRelease}
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        className="v3-btn danger"
                        disabled={busy}
                        onClick={() => onAskRelease(a.id)}
                      >
                        Release
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selected && unallocated.length > 0 && (
        <>
          <h3 style={{ marginTop: 18 }}>Eligible clients awaiting allocation</h3>
          <p className="ops-muted">
            Only eligible consultant-client organisations may be allocated. A client
            already holding an active allocation is shown in the table above.
          </p>
          <ul style={{ margin: '8px 0 0 18px' }}>
            {unallocated.map((id) => (
              <li key={id}>{label(id)}</li>
            ))}
          </ul>
        </>
      )}
    </Card>
  );
}


// ---------------------------------------------------------------------------
// Admin — effective entitlement for ONE organisation (§2 "effective entitlement")
// ---------------------------------------------------------------------------


function ClientStatePanel({ state }) {
  if (!state) return null;
  const direct = state.direct || {};
  const sponsored = state.sponsored || null;
  const effective = state.effective_entitlement || {};
  const governance = state.governance || null;
  const routing = state.effective || {};
  const relationship = state.relationship || {};

  return (
    <Card title="Effective Manual Processing entitlement">
      <table className="v3-ops-table">
        <tbody>
          <StateRow label="Organisation">{state.organization_id}</StateRow>
          <StateRow label="Direct customer subscription">
            {direct.entitled ? 'YES' : 'NO'}
          </StateRow>
          <StateRow label="Consultant-sponsored coverage">
            {sponsored && sponsored.entitled ? 'YES' : 'NO'}
          </StateRow>
          <StateRow label="Effective entitlement">
            {effective.entitled ? 'YES' : 'NO'}
            {effective.source ? ` (${effective.source})` : ''}
          </StateRow>
          <StateRow label="FIN-06 governance">
            {governance ? (governance.enabled ? 'ENABLED' : 'DISABLED') : '—'}
          </StateRow>
          <StateRow label="Processing Entity">
            {routing.configured ? 'CONFIGURED' : 'NONE'}
          </StateRow>
          <StateRow label="Operational routing outcome">
            {routing.processing_entity_id || routing.outcome || '—'}
          </StateRow>
          {(relationship.consultant_firm_id || relationship.consultant_client_id) && (
            <StateRow label="Consultant relationship">
              {relationship.consultant_firm_id || '—'}
              {relationship.consultant_client_id
                ? ` · grant ${relationship.consultant_client_id}`
                : ''}
            </StateRow>
          )}
        </tbody>
      </table>

      {sponsored && sponsored.entitled && (
        <>
          <h3 style={{ marginTop: 16 }}>Sponsored coverage detail</h3>
          <table className="v3-ops-table">
            <tbody>
              <StateRow label="Consultant firm">{sponsored.firm_id || '—'}</StateRow>
              <StateRow label="Mode">{modeLabel(sponsored.mode)}</StateRow>
              <StateRow label="Reason">{sponsored.reason || '—'}</StateRow>
              <StateRow label="Allocated">
                {sponsored.allocated === null || sponsored.allocated === undefined
                  ? '—'
                  : sponsored.allocated}
              </StateRow>
              <StateRow label="Available">
                {sponsored.available === null || sponsored.available === undefined
                  ? '—'
                  : sponsored.available}
              </StateRow>
            </tbody>
          </table>
        </>
      )}

      <p className="ops-muted" style={{ marginTop: 12 }}>
        Direct and consultant-sponsored coverage never imply two separate
        operational services, and commercial entitlement is not the same thing as
        FIN-06 governance or a configured Processing Entity.
      </p>
    </Card>
  );
}


export default function ManualProcessingCoverageTab({ canManage }) {
  const [firmId, setFirmId] = useState('');
  const [firm, setFirm] = useState(null);
  const [orgId, setOrgId] = useState('');
  const [orgSelected, setOrgSelected] = useState(null);
  const [clientState, setClientState] = useState(null);
  const [allocationTarget, setAllocationTarget] = useState('');
  const [allocationReason, setAllocationReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [errorKind, setErrorKind] = useState('load');
  const [notice, setNotice] = useState('');
  const [pendingRelease, setPendingRelease] = useState('');

  // F-11 — selecting a search result only RECORDS the choice; it performs no
  // server mutation. The admin must press an explicit action afterwards, and
  // the server re-validates the id on that action.
  const selectClient = useCallback((org) => {
    setOrgSelected(org);
    setOrgId(org.id);
    setError('');
    setNotice('');
  }, []);

  const loadFirm = useCallback(async (id) => {
    const target = (id || '').trim();
    if (!target) return;
    setBusy(true);
    setError('');
    setErrorKind('load');
    setNotice('');
    try {
      const data = await getAdminManualProcessingCoverage(target);
      setFirm(data);
      setAllocationTarget('');
    } catch (e) {
      setFirm(null);
      setError(e.message || 'Unable to load consultant coverage.');
    } finally {
      setBusy(false);
    }
  }, []);

  const loadClient = useCallback(async (id) => {
    const target = (id || '').trim();
    if (!target) return;
    setBusy(true);
    setError('');
    setErrorKind('load');
    setNotice('');
    try {
      const data = await getAdminManualProcessingClientState(target);
      setClientState(data);
      setOrgId(target);
    } catch (e) {
      setClientState(null);
      setError(e.message || 'Unable to load this client’s Manual Processing state.');
    } finally {
      setBusy(false);
    }
  }, []);

  const allocate = async () => {
    if (!firm || !allocationTarget) return;
    setBusy(true);
    setError('');
    setErrorKind('write');
    setNotice('');
    try {
      await allocateAdminManualProcessingClient({
        consultant_id: firm.consultant_id,
        organization_id: allocationTarget,
        reason: allocationReason.trim() || null,
      });
      setNotice('Client allocated.');
      setAllocationReason('');
      await loadFirm(firm.consultant_id);
    } catch (e) {
      setError(e.message || 'Unable to allocate this client.');
    } finally {
      setBusy(false);
    }
  };

  const release = async (allocationId) => {
    setBusy(true);
    setError('');
    setErrorKind('write');
    setNotice('');
    try {
      await releaseAdminManualProcessingAllocation(allocationId);
      setNotice('Allocation released — its capacity unit is available again.');
      setPendingRelease('');
      await loadFirm(firm.consultant_id);
    } catch (e) {
      setError(e.message || 'Unable to release this allocation.');
    } finally {
      setBusy(false);
    }
  };

  // F-11 — releasing returns a capacity unit and is not reversible, so the row
  // asks for an explicit confirmation before the write is issued.
  const askRelease = (allocationId) => {
    setError('');
    setNotice('');
    setPendingRelease(allocationId);
  };
  const cancelRelease = () => setPendingRelease('');

  const coverage = firm && firm.coverage ? firm.coverage : null;
  const clientNames = firm && firm.client_names ? firm.client_names : {};
  // F-11 — show the human name when the server resolved one; fall back to the id.
  const clientLabel = (id) => (clientNames[id] ? `${clientNames[id]} · ${id}` : id);
  const isSelected = coverage && coverage.mode === 'SELECTED_CLIENTS';
  const unallocated = coverage ? coverage.unallocated_eligible_clients || [] : [];
  const capacityExhausted =
    isSelected &&
    coverage.available !== null &&
    coverage.available !== undefined &&
    coverage.available <= 0;

  return (
    <div>
      {error && errorKind === 'write' && (
        <Alert tone="error" title="Allocation not completed">
          {ALLOCATION_ERROR_COPY}
        </Alert>
      )}
      {error && errorKind !== 'write' && (
        <div className="v3-ops-error" role="alert">{error}</div>
      )}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Commercial coverage</h3>
        <p className="ops-muted">
          Who purchased what, and which clients are covered. This is deliberately
          separate from the operational routing view: buying coverage does not
          enable processing, and a configured Processing Entity does not create
          commercial entitlement.
        </p>
        <div className="workspace-grid">
          <div className="workspace-field">
            <label htmlFor="mp-cov-firm">Consultant firm id</label>
            <input
              id="mp-cov-firm"
              type="text"
              value={firmId}
              placeholder="consultant_profiles.id"
              onChange={(e) => setFirmId(e.target.value)}
            />
          </div>
          <div className="workspace-actions">
            <button
              type="button"
              className="v3-btn primary"
              onClick={() => loadFirm(firmId)}
              disabled={busy || !firmId.trim()}
            >
              {busy ? 'Loading…' : 'Load coverage'}
            </button>
          </div>
        </div>
      </div>

      {firm && <FirmCoveragePanel
        coverage={coverage}
        busy={busy}
        onRelease={release}
        onInspectClient={loadClient}
        clientNames={clientNames}
        pendingRelease={pendingRelease}
        onAskRelease={askRelease}
        onCancelRelease={cancelRelease}
      />}

      {firm && coverage && coverage.enabled && isSelected && (
        <Card title="Allocate an eligible client">
          <p className="ops-muted">
            Only eligible consultant-client organisations may be selected. Capacity
            and eligibility are enforced server-side.
          </p>
          {capacityExhausted ? (
            <Alert tone="warning" title="No allocation capacity remains">
              A newly eligible client cannot receive sponsored coverage until
              capacity is increased or an allocation is released.
            </Alert>
          ) : unallocated.length === 0 ? (
            <EmptyState title="No eligible client awaiting allocation">
              Every eligible client already holds an active allocation, or the firm
              has no active consultant-client relationships.
            </EmptyState>
          ) : (
            <div className="workspace-grid">
              <div className="workspace-field">
                <label htmlFor="mp-cov-target">Eligible client</label>
                <select
                  id="mp-cov-target"
                  value={allocationTarget}
                  disabled={!canManage || busy}
                  onChange={(e) => setAllocationTarget(e.target.value)}
                >
                  <option value="">Select an eligible client…</option>
                  {unallocated.map((id) => (
                    <option key={id} value={id}>{clientLabel(id)}</option>
                  ))}
                </select>
              </div>
              <div className="workspace-field">
                <label htmlFor="mp-cov-reason">Reason (optional)</label>
                <input
                  id="mp-cov-reason"
                  type="text"
                  value={allocationReason}
                  maxLength={500}
                  disabled={!canManage || busy}
                  onChange={(e) => setAllocationReason(e.target.value)}
                />
              </div>
              <div className="workspace-actions">
                <button
                  type="button"
                  className="v3-btn primary"
                  onClick={allocate}
                  disabled={!canManage || busy || !allocationTarget}
                >
                  Allocate
                </button>
              </div>
            </div>
          )}
          {!canManage && (
            <p className="ops-muted">
              Allocation requires the admin coverage capability; this control is
              disabled for your role, and the server would refuse it regardless.
            </p>
          )}
        </Card>
      )}

      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Effective entitlement for one organisation</h3>
        <div className="workspace-grid">
          <ClientPicker
            onSelect={selectClient}
            selected={orgSelected}
            disabled={busy}
          />
          <div className="workspace-actions">
            <button
              type="button"
              className="v3-btn primary"
              onClick={() => loadClient(orgId)}
              disabled={busy || !orgId}
            >
              Load client state
            </button>
          </div>
        </div>
      </div>

      <ClientStatePanel state={clientState} />

      {!firm && !clientState && (
        <div className="workspace-pane">
          <p className="ops-muted">
            Enter a consultant firm id to see its purchased coverage and
            allocations, or search for a client organisation by name to see that
            client&apos;s full commercial + operational Manual Processing state.
          </p>
        </div>
      )}
    </div>
  );
}



