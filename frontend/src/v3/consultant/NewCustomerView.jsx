// frontend/src/v3/consultant/NewCustomerView.jsx
// CON-1 / PO Decision 3 — a consultant can onboard a NEW customer organisation.
// POST /api/v3/consultants/me/customers provisions the owner identity + org and
// links the firm as an active client (all server-authoritative).
import React, { useState } from 'react';
import { createConsultantCustomer } from '../api';

export default function NewCustomerView({ onCreated, onCancel }) {
  const [form, setForm] = useState({
    name: '',
    owner_email: '',
    owner_name: '',
    client_name: '',
    country: 'GB',
  });
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [saving, setSaving] = useState(false);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const submit = async () => {
    setError('');
    setNotice('');
    setSaving(true);
    try {
      const result = await createConsultantCustomer({
        name: form.name,
        owner_email: form.owner_email,
        owner_name: form.owner_name || null,
        client_name: form.client_name || null,
        country: form.country,
      });
      setNotice(
        `Customer “${result.organization?.name || form.name}” created — ` +
        `owner ${result.owner_email} provisioned and the firm is linked as active client.`
      );
      setForm({ name: '', owner_email: '', owner_name: '', client_name: '', country: 'GB' });
      if (onCreated) onCreated();
    } catch (e) {
      setError(e.message || 'Failed to create customer');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="v3-admin-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>New customer organisation</h2>
        <button className="v3-btn v3-btn-sm" onClick={onCancel}>← Back</button>
      </div>
      <p className="v3-muted">
        Creates a real organisation, provisions the owner identity and links your firm
        as the managing consultant (active client grant).
      </p>
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}
      <div className="workspace-grid">
        <div className="workspace-field">
          <label>Organisation name *</label>
          <input value={form.name} onChange={set('name')} placeholder="e.g. Northstar Logistics" />
        </div>
        <div className="workspace-field">
          <label>Owner email *</label>
          <input value={form.owner_email} onChange={set('owner_email')} placeholder="owner@customer.example" />
        </div>
        <div className="workspace-field">
          <label>Owner name</label>
          <input value={form.owner_name} onChange={set('owner_name')} placeholder="e.g. Alex Owner" />
        </div>
        <div className="workspace-field">
          <label>Client label (your list)</label>
          <input value={form.client_name} onChange={set('client_name')} placeholder="Defaults to org name" />
        </div>
        <div className="workspace-field">
          <label>Country</label>
          <input value={form.country} onChange={set('country')} placeholder="GB" maxLength={2} />
        </div>
      </div>
      <div className="workspace-actions">
        <button className="v3-btn primary" onClick={submit} disabled={saving || !form.name.trim() || !form.owner_email.trim()}>
          {saving ? 'Creating…' : 'Create customer'}
        </button>
      </div>
    </div>
  );
}
