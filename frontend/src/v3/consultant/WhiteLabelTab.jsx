// frontend/src/v3/consultant/WhiteLabelTab.jsx
// D27 / D19 §11-13 — custom domains + custom email senders.
import React, { useCallback, useEffect, useState } from 'react';
import {
  activateCustomDomain,
  createCustomDomain,
  createCustomSender,
  listCustomDomains,
  listCustomSenders,
  removeCustomDomain,
  removeCustomSender,
  verifyCustomDomain,
  verifyCustomSender,
} from '../api';

const DOMAIN_STATUS_LABELS = {
  pending: 'Pending verification',
  verified: 'Verified',
  active: 'Active',
  removed_suspended: 'Removed / suspended',
};

const SENDER_STATUS_LABELS = {
  pending: 'Pending verification',
  verified: 'Verified',
  removed: 'Removed',
};

export default function WhiteLabelTab() {
  const [domains, setDomains] = useState([]);
  const [senders, setSenders] = useState([]);
  const [newDomain, setNewDomain] = useState('');
  const [newSender, setNewSender] = useState('');
  const [tokenInputs, setTokenInputs] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    try {
      const [domainResult, senderResult] = await Promise.all([
        listCustomDomains(),
        listCustomSenders(),
      ]);
      setDomains(domainResult.domains || []);
      setSenders(senderResult.senders || []);
    } catch (e) {
      setError(e.message || 'Failed to load white-label configuration');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onAddDomain = async () => {
    setError('');
    setNotice('');
    try {
      await createCustomDomain(newDomain.trim());
      setNewDomain('');
      setNotice('Domain registered. Add the TXT record below, then verify.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to add domain');
    }
  };

  const onVerifyDomain = async (domain) => {
    const token = (tokenInputs[domain.id] || '').trim();
    if (!token) {
      setError('Enter the TXT record value to verify.');
      return;
    }
    setError('');
    try {
      await verifyCustomDomain(domain.id, token);
      setNotice(`Domain ${domain.domain} verified.`);
      await load();
    } catch (e) {
      setError(e.message || 'Verification failed');
    }
  };

  const onActivateDomain = async (domain) => {
    setError('');
    try {
      await activateCustomDomain(domain.id);
      setNotice(`Domain ${domain.domain} is now active.`);
      await load();
    } catch (e) {
      setError(e.message || 'Activation failed');
    }
  };

  const onRemoveDomain = async (domain) => {
    if (!window.confirm(`Remove ${domain.domain}? Branding stops presenting on it.`)) return;
    setError('');
    try {
      await removeCustomDomain(domain.id);
      setNotice(`Domain ${domain.domain} removed/suspended.`);
      await load();
    } catch (e) {
      setError(e.message || 'Removal failed');
    }
  };

  const onAddSender = async () => {
    setError('');
    setNotice('');
    try {
      await createCustomSender(newSender.trim());
      setNewSender('');
      setNotice('Sender registered. Complete Resend domain verification, then verify it here.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to add sender');
    }
  };

  const onVerifySender = async (sender) => {
    setError('');
    try {
      await verifyCustomSender(sender.id);
      setNotice(`Sender ${sender.email} verified — it may now be used as a From address.`);
      await load();
    } catch (e) {
      setError(e.message || 'Verification failed');
    }
  };

  const onRemoveSender = async (sender) => {
    if (!window.confirm(`Remove sender ${sender.email}?`)) return;
    setError('');
    try {
      await removeCustomSender(sender.id);
      setNotice(`Sender ${sender.email} removed.`);
      await load();
    } catch (e) {
      setError(e.message || 'Removal failed');
    }
  };

  if (loading) return <div className="v3-loading"><div className="spinner" />Loading white-label…</div>;

  return (
    <div className="v3-admin-card">
      <h2>Custom domains</h2>
      <p className="v3-muted">
        Your firm owns the domain, registrar, DNS and renewal. CarbonTally provides
        the platform + authorized branding. A domain never grants access by itself.
      </p>
      {error && <div className="v3-error" style={{ marginBottom: 12 }}>{error}</div>}
      {notice && <div className="v3-note" style={{ marginBottom: 12 }}>{notice}</div>}

      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <input
          value={newDomain}
          onChange={(e) => setNewDomain(e.target.value)}
          placeholder="portal.your-domain.com"
        />
        <button className="v3-btn v3-btn-primary" onClick={onAddDomain} disabled={!newDomain.trim()}>
          Add domain
        </button>
      </div>

      {domains.length === 0 ? (
        <div className="v3-empty">No custom domains configured.</div>
      ) : (
        <table className="v3-table">
          <thead>
            <tr><th>Domain</th><th>Status</th><th>Verification</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {domains.map((domain) => (
              <tr key={domain.id}>
                <td>{domain.domain}</td>
                <td><span className={`v3-status ${domain.status}`}>{DOMAIN_STATUS_LABELS[domain.status] || domain.status}</span></td>
                <td className="v3-muted" style={{ fontSize: 12 }}>
                  TXT <code>_carbontally.{domain.domain}</code> ={' '}
                  <code>carbon-tally-verify={domain.verification_token}</code>
                </td>
                <td>
                  {domain.status === 'pending' && (
                    <span style={{ display: 'inline-flex', gap: 6 }}>
                      <input
                        placeholder="TXT token"
                        value={tokenInputs[domain.id] || ''}
                        onChange={(e) => setTokenInputs((t) => ({ ...t, [domain.id]: e.target.value }))}
                        style={{ width: 160 }}
                      />
                      <button className="v3-btn v3-btn-sm" onClick={() => onVerifyDomain(domain)}>Verify</button>
                    </span>
                  )}
                  {domain.status === 'verified' && (
                    <button className="v3-btn v3-btn-sm" onClick={() => onActivateDomain(domain)}>Activate</button>
                  )}
                  {domain.status !== 'removed_suspended' && (
                    <button className="v3-btn v3-btn-sm" onClick={() => onRemoveDomain(domain)}>Remove</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2 style={{ marginTop: 24 }}>Custom email senders</h2>
      <p className="v3-muted">
        Optional verified From addresses (e.g. reports@your-domain.com). Only VERIFIED
        senders may be used; arbitrary From addresses are never allowed.
      </p>
      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <input
          value={newSender}
          onChange={(e) => setNewSender(e.target.value)}
          placeholder="reports@your-domain.com"
        />
        <button className="v3-btn v3-btn-primary" onClick={onAddSender} disabled={!newSender.trim()}>
          Add sender
        </button>
      </div>

      {senders.length === 0 ? (
        <div className="v3-empty">No custom senders configured.</div>
      ) : (
        <table className="v3-table">
          <thead>
            <tr><th>Email</th><th>Domain</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {senders.map((sender) => (
              <tr key={sender.id}>
                <td>{sender.email}</td>
                <td className="v3-muted">{sender.domain || '—'}</td>
                <td><span className={`v3-status ${sender.status}`}>{SENDER_STATUS_LABELS[sender.status] || sender.status}</span></td>
                <td>
                  {sender.status === 'pending' && (
                    <button className="v3-btn v3-btn-sm" onClick={() => onVerifySender(sender)}>Verify</button>
                  )}
                  {sender.status !== 'removed' && (
                    <button className="v3-btn v3-btn-sm" onClick={() => onRemoveSender(sender)}>Remove</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
