// frontend/src/v3/admin/CustomFactorsTab.jsx
// D9/G-P0-3 — Customer-owned emission factors: full lifecycle surface.
//   * create draft (org member)
//   * edit draft (org member; approved factors change only via a new version)
//   * approve (org admin/owner only, no self-approval — server-enforced)
//   * deactivate (soft; org admin/owner)
// Precedence note is displayed: approved customer factor → CarbonTally factor
// (D-cf-5). The backend remains the authoritative factor store.
import React, { useCallback, useEffect, useState } from 'react';
import {
  approveCustomerFactor,
  createCustomerFactor,
  deactivateCustomerFactor,
  listCustomerFactors,
  updateCustomerFactor,
} from '../api';
import { LoadingState, Alert, Button, StatusBadge, TextInput, SelectInput, TextArea, ConfirmationDialog } from '../components/ui';
import DataTable from '../components/ui/DataTable';

const EMPTY = {
  name: '',
  activity_type: '',
  co2e_multiplier: '',
  unit: 'kgCO2e',
  scope: 'Scope 1',
  country: 'GB',
  reporting_year: String(new Date().getFullYear()),
  description: '',
};

export default function CustomFactorsTab({ organization, isAdmin }) {
  const [factors, setFactors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ ...EMPTY });
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(null); // {action:'approve'|'deactivate', factor}
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await listCustomerFactors(organization.id);
      setFactors(result.factors || []);
    } catch (e) {
      setError(e.message || 'Failed to load custom factors');
    } finally {
      setLoading(false);
    }
  }, [organization.id]);

  useEffect(() => { load(); }, [load, retryCount]);

  const flash = (message) => {
    setNotice(message);
    setTimeout(() => setNotice(''), 5000);
  };

  const onSave = async () => {
    setBusy(true);
    setError('');
    const payload = {
      organization_id: organization.id,
      name: form.name,
      activity_type: form.activity_type,
      co2e_multiplier: form.co2e_multiplier,
      unit: form.unit,
      scope: form.scope,
      country: form.country,
      reporting_year: Number(form.reporting_year),
      description: form.description || null,
    };
    try {
      if (editing) {
        await updateCustomerFactor(editing, payload);
        flash('Factor updated.');
      } else {
        await createCustomerFactor(payload);
        flash('Factor draft created. As the organisation owner you can approve it; an admin can also approve it.');
      }
      setShowForm(false);
      setEditing(null);
      setForm({ ...EMPTY });
      await load();
    } catch (e) {
      setError(e.message || 'Failed to save factor');
    } finally {
      setBusy(false);
    }
  };

  const onConfirmAction = async () => {
    if (!confirm) return;
    setBusy(true);
    setError('');
    try {
      if (confirm.action === 'approve') {
        await approveCustomerFactor(confirm.factor.id);
        flash('Factor approved and active.');
      } else {
        await deactivateCustomerFactor(confirm.factor.id);
        flash('Factor deactivated.');
      }
      setConfirm(null);
      await load();
    } catch (e) {
      setError(e.message || 'Failed to update factor status');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <LoadingState label="Loading custom factors…" />;

  const columns = [
    { key: 'name', header: 'Factor', accessor: 'name', render: (row) => <strong>{row.name}</strong>, isHeader: true },
    { key: 'activity_type', header: 'Activity', accessor: 'activity_type' },
    {
      key: 'value',
      header: 'Value',
      accessor: 'co2e_multiplier',
      render: (row) => `${row.co2e_multiplier} ${row.unit || ''}`,
    },
    { key: 'reporting_year', header: 'Year', accessor: 'reporting_year' },
    { key: 'status', header: 'Status', accessor: 'status', render: (row) => <StatusBadge status={row.status} /> },
    {
      key: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (row) => (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {row.status === 'draft' && isAdmin && (
            <Button variant="approve" size="sm" icon="check" onClick={() => setConfirm({ action: 'approve', factor: row })}>
              Approve
            </Button>
          )}
          {row.status === 'active' && isAdmin && (
            <Button variant="danger" size="sm" icon="x" onClick={() => setConfirm({ action: 'deactivate', factor: row })}>
              Deactivate
            </Button>
          )}
          {row.status === 'draft' && (
            <Button
              variant="secondary"
              size="sm"
              icon="edit"
              onClick={() => {
                setEditing(row.id);
                setForm({
                  name: row.name || '',
                  activity_type: row.activity_type || '',
                  co2e_multiplier: String(row.co2e_multiplier ?? ''),
                  unit: row.unit || 'kgCO2e',
                  scope: row.scope || 'Scope 1',
                  country: row.country || 'GB',
                  reporting_year: String(row.reporting_year || new Date().getFullYear()),
                  description: row.description || '',
                });
                setShowForm(true);
              }}
            >
              Edit
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      {notice && <Alert tone="success" title="Updated">{notice}</Alert>}
      {error && <Alert tone="error" title="Action failed">{error}</Alert>}

      <Alert tone="info" title="Precedence">
        Approved customer factors take precedence over CarbonTally factors for matching. Drafts are not used in
        calculations. Editing is limited to drafts — approved factors change only via a new version.
      </Alert>

      <div className="v3-actions">
        <Button variant="primary" icon="plus" onClick={() => { setEditing(null); setForm({ ...EMPTY }); setShowForm((s) => !s); }}>
          {showForm ? 'Hide form' : 'New factor'}
        </Button>
      </div>

      {showForm && (
        <div className="v3-card" style={{ marginTop: 16 }}>
          <h2>{editing ? 'Edit factor draft' : 'Create a custom factor (draft)'}</h2>
          <div className="v3-form-grid">
            <TextInput label="Factor name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <TextInput label="Activity type" required value={form.activity_type} onChange={(e) => setForm({ ...form, activity_type: e.target.value })} hint="e.g. Natural gas, Diesel" />
            <TextInput label="CO₂e multiplier" required value={form.co2e_multiplier} onChange={(e) => setForm({ ...form, co2e_multiplier: e.target.value })} hint="The value per unit (decimal)" />
            <SelectInput label="Unit" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })}>
              <option>kgCO2e</option><option>kgCO2e/L</option><option>kgCO2e/kWh</option><option>kgCO2e/kg</option><option>kgCO2e/m³</option>
            </SelectInput>
            <SelectInput label="Scope" value={form.scope} onChange={(e) => setForm({ ...form, scope: e.target.value })}>
              <option>Scope 1</option><option>Scope 2</option><option>Scope 3</option>
            </SelectInput>
            <SelectInput label="Country" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })}>
              <option value="GB">GB</option><option value="IE">IE</option>
            </SelectInput>
            <TextInput label="Reporting year" required value={form.reporting_year} onChange={(e) => setForm({ ...form, reporting_year: e.target.value })} />
          </div>
          <TextArea label="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <div className="v3-actions">
            <Button variant="primary" icon="save" loading={busy} onClick={onSave}>{editing ? 'Save changes' : 'Create draft'}</Button>
            <Button variant="secondary" onClick={() => { setShowForm(false); setEditing(null); }}>Cancel</Button>
          </div>
        </div>
      )}

      {factors.length === 0 ? (
        <p className="v3-muted" style={{ marginTop: 16 }}>No custom factors yet — create a draft above.</p>
      ) : (
        <div style={{ marginTop: 16 }}>
          <DataTable caption="Customer-owned emission factors" columns={columns} rows={factors} rowKey="id" />
        </div>
      )}

      {confirm && (
        <ConfirmationDialog
          open
          title={confirm.action === 'approve' ? 'Approve this factor?' : 'Deactivate this factor?'}
          message={
            confirm.action === 'approve'
              ? 'Approval activates the factor for matching (approved customer factor takes precedence). As the organisation owner you may approve your own factor; other actors may not self-approve — the backend enforces this.'
              : 'Deactivation is a soft disable; the factor and its history are preserved.'
          }
          confirmLabel={confirm.action === 'approve' ? 'Approve' : 'Deactivate'}
          tone={confirm.action === 'approve' ? 'approve' : 'danger'}
          busy={busy}
          onClose={() => setConfirm(null)}
          onConfirm={onConfirmAction}
        />
      )}
    </div>
  );
}

