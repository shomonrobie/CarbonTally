// frontend/src/v3/customer/ExistingDataDiscoveryPage.jsx
// D27 / D19 — Customer-initiated direct onboarding: existing-data discovery.
import React, { useEffect, useState } from 'react';
import {
  chooseDiscoveryAdoption,
  createDiscoveryRequest,
  discoveryLookup,
  getDiscoveryRequest,
  listDiscoveryRequests,
  resolveV3Organization,
  verifyDiscoveryRequest,
} from '../api';
import { ErrorState } from '../components/StateViews';

const CATEGORY_LABELS = {
  documents: 'Documents',
  suppliers: 'Suppliers',
  extraction_records: 'Extraction records',
  mappings: 'Mappings',
  calculations: 'Calculations',
  reports: 'Reports',
  report_versions: 'Report versions',
  processing_history: 'Processing history',
};

const STATUS_LABELS = {
  pending_verification: 'Pending verification',
  verified: 'Verified',
  adopted: 'Adopted',
  discarded: 'Discarded',
  expired: 'Expired',
  rejected: 'Rejected',
};

export default function ExistingDataDiscoveryPage() {
  const [org, setOrg] = useState(null);
  const [signals, setSignals] = useState({ name: '', company_number: '', email_domain: '', contact_email: '' });
  const [candidates, setCandidates] = useState([]);
  const [requests, setRequests] = useState([]);
  const [activeRequest, setActiveRequest] = useState(null);
  const [code, setCode] = useState('');
  const [choice, setChoice] = useState('');
  const [partialCategories, setPartialCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const load = async (organizationId) => {
    const result = await listDiscoveryRequests(organizationId).catch(() => ({ requests: [] }));
    setRequests(result.requests || []);
  };

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
        setError(e.message || 'Failed to load discovery requests');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [retryCount]);

  const onLookup = async () => {
    if (!org) return;
    setSearching(true);
    setError('');
    setNotice('');
    try {
      const result = await discoveryLookup(org.id, signals);
      setCandidates(result.candidates || []);
      setNotice(result.disclaimer || '');
    } catch (e) {
      setError(e.message || 'Discovery lookup failed');
    } finally {
      setSearching(false);
    }
  };

  const onRequest = async (candidate) => {
    setError('');
    setNotice('');
    try {
      const result = await createDiscoveryRequest(org.id, candidate.organization_id, 'email');
      setActiveRequest(result.request);
      setNotice(
        result.verification_delivered
          ? 'A verification code was emailed to the registered contact of the existing organisation.'
          : (result.delivery_note || 'Verification email could not be delivered — ask a CarbonTally administrator to mediate.')
      );
      await load(org.id);
    } catch (e) {
      setError(e.message || 'Failed to create the discovery request');
    }
  };

  const onVerify = async () => {
    if (!activeRequest) return;
    setError('');
    try {
      await verifyDiscoveryRequest(activeRequest.id, org.id, code);
      setNotice('Verified. You can now choose how to proceed with the existing data.');
      const refreshed = await getDiscoveryRequest(activeRequest.id, org.id);
      setActiveRequest(refreshed.request);
    } catch (e) {
      setError(e.message || 'Verification failed');
    }
  };

  const toggleCategory = (category) => {
    setPartialCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    );
  };

  const onChoose = async () => {
    if (!activeRequest || !choice) return;
    setError('');
    setNotice('');
    try {
      const scope = choice === 'partial' ? { categories: partialCategories } : {};
      const result = await chooseDiscoveryAdoption(activeRequest.id, org.id, choice, scope);
      setNotice(
        choice === 'discard'
          ? 'You chose to start fresh. No data was deleted — the existing organisation stays untouched.'
          : `Adoption complete. ${result.note || ''}`
      );
      setActiveRequest(result.request || null);
      setCandidates([]);
      setChoice('');
      setPartialCategories([]);
      await load(org.id);
    } catch (e) {
      setError(e.message || 'Failed to record your choice');
    }
  };

  if (loading) return <div className="v3-loading"><div className="spinner" />Loading…</div>;
  if (error && !org) return <ErrorState message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  const verified = activeRequest && activeRequest.status === 'verified';

  return (
    <div className="v3-page">
      <div className="v3-page-header">
        <h1>Existing data</h1>
        <p className="v3-subtitle">
          Check whether CarbonTally already holds data that may belong to your organisation
        </p>
      </div>

      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note" style={{ marginBottom: 14 }}>{notice}</div>}

      <div className="v3-card">
        <h2>1. Find existing data</h2>
        <p className="v3-muted">
          Matches are <strong>candidates only</strong> — never treated as ownership.
          Adoption always requires secure verification and your explicit choice.
        </p>
        <div className="v3-form-grid">
          <label>
            Organisation name
            <input value={signals.name} onChange={(e) => setSignals((s) => ({ ...s, name: e.target.value }))} placeholder="e.g. ACME Ltd" />
          </label>
          <label>
            Company number
            <input value={signals.company_number} onChange={(e) => setSignals((s) => ({ ...s, company_number: e.target.value }))} placeholder="Optional" />
          </label>
          <label>
            Email domain
            <input value={signals.email_domain} onChange={(e) => setSignals((s) => ({ ...s, email_domain: e.target.value }))} placeholder="e.g. acme.com" />
          </label>
          <label>
            Contact email
            <input value={signals.contact_email} onChange={(e) => setSignals((s) => ({ ...s, contact_email: e.target.value }))} placeholder="Optional" />
          </label>
        </div>
        <div className="v3-actions">
          <button className="v3-btn v3-btn-primary" onClick={onLookup} disabled={searching}>
            {searching ? 'Searching…' : 'Search'}
          </button>
        </div>

        {candidates.length > 0 && (
          <table className="v3-table" style={{ marginTop: 16 }}>
            <thead>
              <tr><th>Organisation</th><th>Country</th><th>Data found</th><th /></tr>
            </thead>
            <tbody>
              {candidates.map((candidate) => (
                <tr key={candidate.organization_id}>
                  <td>{candidate.name}</td>
                  <td>{candidate.country || '—'}</td>
                  <td className="v3-muted">
                    {Object.entries(candidate.data_summary || {})
                      .filter(([, count]) => count > 0)
                      .map(([key, count]) => `${count} ${key.replace(/_/g, ' ')}`)
                      .join(', ') || 'No records detected'}
                  </td>
                  <td>
                    <button className="v3-btn v3-btn-sm" onClick={() => onRequest(candidate)}>
                      I believe this is my organisation
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {candidates.length === 0 && searching && (
          <div className="v3-empty">No candidate matches found.</div>
        )}
      </div>

      {activeRequest && activeRequest.status === 'pending_verification' && (
        <div className="v3-card">
          <h2>2. Verify access</h2>
          <p className="v3-muted">
            A verification code was sent to the registered contact of the existing
            organisation. Enter it below to prove you may act on its behalf.
          </p>
          <label>
            Verification code
            <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="Enter the emailed code" />
          </label>
          <div className="v3-actions">
            <button className="v3-btn v3-btn-primary" onClick={onVerify} disabled={!code.trim()}>
              Verify
            </button>
          </div>
        </div>
      )}

      {activeRequest && verified && (
        <div className="v3-card">
          <h2>3. Your choice</h2>
          <p className="v3-muted">
            Existing data may already be available for your organisation. You decide
            what happens. <strong>Choosing to start fresh never deletes the existing data</strong>.
          </p>
          <div className="v3-choice-grid" style={{ display: 'grid', gap: 10, marginBottom: 14 }}>
            <label style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <input type="radio" name="choice" checked={choice === 'use_all'} onChange={() => setChoice('use_all')} />
              <span><strong>Use all</strong> — adopt all eligible existing organizational data in place.</span>
            </label>
            <label style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <input type="radio" name="choice" checked={choice === 'partial'} onChange={() => setChoice('partial')} />
              <span><strong>Use selected / partial</strong> — choose which categories to carry forward.</span>
            </label>
            <label style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <input type="radio" name="choice" checked={choice === 'discard'} onChange={() => setChoice('discard')} />
              <span><strong>Start fresh</strong> — do not use the discovered historical data.</span>
            </label>
          </div>
          {choice === 'partial' && (
            <div className="v3-form-grid">
              {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                <label key={key} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <input
                    type="checkbox"
                    checked={partialCategories.includes(key)}
                    onChange={() => toggleCategory(key)}
                  />
                  {label}
                </label>
              ))}
            </div>
          )}
          <div className="v3-actions">
            <button className="v3-btn v3-btn-primary" onClick={onChoose} disabled={!choice}>
              Confirm choice
            </button>
          </div>
        </div>
      )}

      {activeRequest && activeRequest.status === 'adopted' && (
        <div className="v3-card">
          <h2>4. Adoption complete</h2>
          <p>
            You are now a Direct CarbonTally Customer for the adopted organisation.
            Historical data was preserved in place under the same organisation id.
          </p>
        </div>
      )}
      {activeRequest && activeRequest.status === 'discarded' && (
        <div className="v3-card">
          <h2>4. Start fresh</h2>
          <p>
            Your choice was recorded. No data was deleted — the existing organisation
            remains untouched. A formal deletion is always a separate process.
          </p>
        </div>
      )}

      {requests.length > 0 && (
        <div className="v3-card">
          <h2>Discovery requests</h2>
          <table className="v3-table">
            <thead>
              <tr><th>Candidate</th><th>Status</th><th>Choice</th><th>Created</th></tr>
            </thead>
            <tbody>
              {requests.map((request) => (
                <tr key={request.id}>
                  <td className="v3-muted">{request.candidate_organization_id}</td>
                  <td><span className={`v3-status ${request.status}`}>{STATUS_LABELS[request.status] || request.status}</span></td>
                  <td>{request.adoption_choice || '—'}</td>
                  <td className="v3-muted">{request.created_at ? new Date(request.created_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
