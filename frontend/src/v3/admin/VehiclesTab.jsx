// frontend/src/v3/admin/VehiclesTab.jsx
// D17/G-P1-2 — organisation-scoped fleet master data. Real V3 backend over
// /api/v3/vehicles (table migration 20260825000000_v3m7_vehicles.sql; RLS
// org-scoped deny-by-default). Writes are org-admin gated server-side.
import React, { useCallback, useEffect, useState } from 'react';
import {
  createVehicle,
  listVehicles,
  removeVehicle,
  updateVehicle,
} from '../api';
import { LoadingState, Alert, Button, TextInput, SelectInput, ConfirmationDialog } from '../components/ui';
import DataTable from '../components/ui/DataTable';

const EMPTY = { name: '', registration: '', make: '', model: '', fuel_type: 'Diesel', vehicle_type: '', capacity: '', capacity_unit: 'tonnes' };

export default function VehiclesTab({ organization, isAdmin }) {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ ...EMPTY });
  const [busy, setBusy] = useState(false);
  const [confirmRemove, setConfirmRemove] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await listVehicles(organization.id);
      setVehicles(result.vehicles || []);
    } catch (e) {
      setError(e.message || 'Failed to load vehicles');
    } finally {
      setLoading(false);
    }
  }, [organization.id]);

  useEffect(() => { load(); }, [load]);

  const flash = (message) => {
    setNotice(message);
    setTimeout(() => setNotice(''), 5000);
  };

  const onSave = async () => {
    setBusy(true);
    setError('');
    const payload = {
      name: form.name,
      registration: form.registration || null,
      make: form.make || null,
      model: form.model || null,
      fuel_type: form.fuel_type || null,
      vehicle_type: form.vehicle_type || null,
      capacity: form.capacity === '' ? null : Number(form.capacity),
      capacity_unit: form.capacity_unit || null,
    };
    try {
      if (editing) {
        await updateVehicle(editing, payload);
        flash('Vehicle updated.');
      } else {
        await createVehicle({ organization_id: organization.id, ...payload });
        flash('Vehicle added.');
      }
      setShowForm(false);
      setEditing(null);
      setForm({ ...EMPTY });
      await load();
    } catch (e) {
      setError(e.message || 'Failed to save vehicle');
    } finally {
      setBusy(false);
    }
  };

  const onRemove = async () => {
    if (!confirmRemove) return;
    setBusy(true);
    setError('');
    try {
      await removeVehicle(confirmRemove);
      setConfirmRemove(null);
      flash('Vehicle removed.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to remove vehicle');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <LoadingState label="Loading vehicles…" />;

  const columns = [
    { key: 'name', header: 'Name', accessor: 'name', render: (row) => <strong>{row.name}</strong>, isHeader: true },
    { key: 'registration', header: 'Registration', accessor: 'registration', render: (row) => row.registration || '—' },
    {
      key: 'vehicle',
      header: 'Make / model',
      accessor: 'id',
      render: (row) => [row.make, row.model].filter(Boolean).join(' ') || '—',
    },
    { key: 'fuel_type', header: 'Fuel', accessor: 'fuel_type', render: (row) => row.fuel_type || '—' },
    {
      key: 'capacity',
      header: 'Capacity',
      accessor: 'capacity',
      render: (row) => (row.capacity != null ? `${row.capacity} ${row.capacity_unit || ''}` : '—'),
    },
    {
      key: 'status',
      header: 'Status',
      accessor: 'is_active',
      render: (row) => (row.is_active ? 'Active' : 'Inactive'),
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (row) => (
        <div style={{ display: 'flex', gap: 6 }}>
          {isAdmin && (
            <Button
              variant="secondary"
              size="sm"
              icon="edit"
              onClick={() => {
                setEditing(row.id);
                setForm({
                  name: row.name || '',
                  registration: row.registration || '',
                  make: row.make || '',
                  model: row.model || '',
                  fuel_type: row.fuel_type || 'Diesel',
                  vehicle_type: row.vehicle_type || '',
                  capacity: row.capacity != null ? String(row.capacity) : '',
                  capacity_unit: row.capacity_unit || 'tonnes',
                });
                setShowForm(true);
              }}
            >
              Edit
            </Button>
          )}
          {isAdmin && (
            <Button variant="danger" size="sm" icon="trash" onClick={() => setConfirmRemove(row.id)}>
              Remove
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

      {isAdmin && (
        <div className="v3-actions">
          <Button variant="primary" icon="plus" onClick={() => { setEditing(null); setForm({ ...EMPTY }); setShowForm((s) => !s); }}>
            {showForm ? 'Hide form' : 'Add vehicle'}
          </Button>
        </div>
      )}

      {showForm && isAdmin && (
        <div className="v3-card" style={{ marginTop: 16 }}>
          <h2>{editing ? 'Edit vehicle' : 'Add a vehicle'}</h2>
          <div className="v3-form-grid">
            <TextInput label="Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} hint="e.g. Site van 01" />
            <TextInput label="Registration" value={form.registration} onChange={(e) => setForm({ ...form, registration: e.target.value })} />
            <TextInput label="Make" value={form.make} onChange={(e) => setForm({ ...form, make: e.target.value })} />
            <TextInput label="Model" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
            <SelectInput label="Fuel type" value={form.fuel_type} onChange={(e) => setForm({ ...form, fuel_type: e.target.value })}>
              <option>Diesel</option><option>Petrol</option><option>Electric</option><option>Hybrid</option><option>Other</option>
            </SelectInput>
            <TextInput label="Vehicle type" value={form.vehicle_type} onChange={(e) => setForm({ ...form, vehicle_type: e.target.value })} hint="e.g. car, van, HGV" />
            <TextInput label="Capacity" value={form.capacity} onChange={(e) => setForm({ ...form, capacity: e.target.value })} />
            <TextInput label="Capacity unit" value={form.capacity_unit} onChange={(e) => setForm({ ...form, capacity_unit: e.target.value })} />
          </div>
          <div className="v3-actions">
            <Button variant="primary" icon="save" loading={busy} onClick={onSave}>{editing ? 'Save changes' : 'Add vehicle'}</Button>
            <Button variant="secondary" onClick={() => { setShowForm(false); setEditing(null); }}>Cancel</Button>
          </div>
        </div>
      )}

      {vehicles.length === 0 ? (
        <p className="v3-muted" style={{ marginTop: 16 }}>
          No vehicles yet. Vehicles are organisation master data (D17) and never block processing.
        </p>
      ) : (
        <div style={{ marginTop: 16 }}>
          <DataTable caption="Organisation vehicles" columns={columns} rows={vehicles} rowKey="id" />
        </div>
      )}

      {confirmRemove && (
        <ConfirmationDialog
          open
          title="Remove this vehicle?"
          message="The vehicle is removed from organisation master data."
          confirmLabel="Remove"
          tone="danger"
          busy={busy}
          onClose={() => setConfirmRemove(null)}
          onConfirm={onRemove}
        />
      )}
    </div>
  );
}

