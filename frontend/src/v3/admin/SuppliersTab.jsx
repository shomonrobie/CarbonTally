// frontend/src/v3/admin/SuppliersTab.jsx
// Supplier management using the V3 org-scoped suppliers surface (real data).
import React, { useCallback, useEffect, useState } from 'react';
import { createSupplier, listSuppliers, removeSupplier } from '../api';

export default function SuppliersTab({ organization }) {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [confirmRemove, setConfirmRemove] = useState(null);
  const [form, setForm] = useState({ name: '', supplier_type: '', contact_name: '', contact_email: '', country: 'GB' });

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (status) params.status = status;
      const result = await listSuppliers(organization.id, params);
      setSuppliers(result.suppliers || []);
    } catch (e) {
      setError(e.message || 'Failed to load suppliers');
    } finally {
      setLoading(false);
    }
  }, [organization.id, search, status]);

  useEffect(() => { load(); }, [load]);

  const onSave = async () => {
    setError('');
    try {
      await createSupplier({ organization_id: organization.id, ...form });
      setShowCreate(false);
      setForm({ name: '', supplier_type: '', contact_name: '', contact_email: '', country: 'GB' });
      setNotice('Supplier created.');
      setTimeout(() => setNotice(''), 5000);
      await load();
    } catch (e) {
      setError(e.message || 'Failed to create supplier');
    }
  };

  const onRemove = async (supplierId) => {
    try {
      await removeSupplier(supplierId);
      setConfirmRemove(null);
      setNotice('Supplier removed.');
      setTimeout(() => setNotice(''), 5000);
      await load();
    } catch (e) {
      setError(e.message || 'Failed to remove supplier');
    }
  };

  return (
    <div>
      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note">{notice}</div>}

      <div className="v3-admin-card">
        <div className="v3-admin-actions" style={{ marginTop: 0 }}>
          <input
            className="v3-search-input"
            placeholder="Search suppliers…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select className="v3-role-select" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          <button className="v3-btn v3-btn-primary" onClick={() => setShowCreate(true)}>+ New supplier</button>
        </div>

        {loading ? (
          <div className="v3-loading"><div className="spinner" />Loading suppliers…</div>
        ) : suppliers.length === 0 ? (
          <div className="v3-empty">No suppliers found.</div>
        ) : (
          <table className="v3-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Contact</th>
                <th>Country</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {suppliers.map((supplier) => (
                <tr key={supplier.id}>
                  <td><div className="v3-report-name">{supplier.name}</div></td>
                  <td className="v3-muted">{supplier.supplier_type || supplier.type || '—'}</td>
                  <td>
                    <div>{supplier.contact_name || '—'}</div>
                    <div className="v3-muted">{supplier.contact_email || ''}</div>
                  </td>
                  <td className="v3-muted">{supplier.country || '—'}</td>
                  <td>
                    <span className={`v3-badge ${supplier.is_active ? 'active' : 'inactive'}`}>
                      {supplier.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <button className="v3-btn v3-btn-sm" onClick={() => setConfirmRemove(supplier)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && (
        <div className="v3-modal-backdrop" onClick={() => setShowCreate(false)}>
          <div className="v3-modal" onClick={(e) => e.stopPropagation()}>
            <h2>New supplier</h2>
            <div className="v3-form-group">
              <label>Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="v3-form-group">
              <label>Supplier type</label>
              <input value={form.supplier_type} onChange={(e) => setForm({ ...form, supplier_type: e.target.value })} />
            </div>
            <div className="v3-form-group">
              <label>Contact name</label>
              <input value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })} />
            </div>
            <div className="v3-form-group">
              <label>Contact email</label>
              <input type="email" value={form.contact_email} onChange={(e) => setForm({ ...form, contact_email: e.target.value })} />
            </div>
            <div className="v3-form-group">
              <label>Country</label>
              <select value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })}>
                <option value="GB">GB</option>
                <option value="IE">IE</option>
              </select>
            </div>
            <div className="v3-modal-actions">
              <button className="v3-btn" onClick={() => setShowCreate(false)}>Cancel</button>
              <button className="v3-btn v3-btn-primary" onClick={onSave} disabled={!form.name.trim()}>
                Create supplier
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmRemove && (
        <div className="v3-modal-backdrop" onClick={() => setConfirmRemove(null)}>
          <div className="v3-modal v3-confirm-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Remove supplier?</h2>
            <p className="v3-muted">{confirmRemove.name} will be marked inactive.</p>
            <div className="v3-modal-actions">
              <button className="v3-btn" onClick={() => setConfirmRemove(null)}>Cancel</button>
              <button className="v3-btn v3-btn-danger" onClick={() => onRemove(confirmRemove.id)}>
                Remove supplier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
