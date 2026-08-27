// frontend/src/v3/ops/StaffRoster.jsx
// Staff roster + roles (CarbonTally internal ops). List + create over the real
// /api/v3/ops/staff and /staff-roles surfaces. Staff admins can also assign a
// staff profile to a Processing Entity (entity_id) so entity staff land in the
// entity-scoped extraction workspace (D22).
import React, { useEffect, useState } from 'react';
import {
  createOpsStaff,
  listOpsStaff,
  listProcessingEntities,
  listStaffRoles,
  updateOpsStaff,
} from '../api';

export default function StaffRoster({ canManage }) {
  const [staff, setStaff] = useState([]);
  const [roles, setRoles] = useState([]);
  const [entities, setEntities] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({ user_id: '', first_name: '', last_name: '', email: '', role_id: '', entity_id: '' });
  const [entityFor, setEntityFor] = useState({ profileId: '', entityId: '' });

  const load = async () => {
    try {
      const [list, roleList] = await Promise.all([listOpsStaff(), listStaffRoles()]);
      setStaff(list.staff || []);
      setRoles((roleList.roles || []).concat(roleList.staff_roles || []));
    } catch (e) {
      setError(e.message || 'Failed to load staff');
    }
  };

  useEffect(() => {
    load();
    listProcessingEntities()
      .then((result) => setEntities(result.entities || []))
      .catch(() => setEntities([]));
  }, []);

  const create = async () => {
    setError('');
    setNotice('');
    try {
      await createOpsStaff({
        user_id: form.user_id.trim(),
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        role_id: form.role_id || null,
        entity_id: form.entity_id || null,
      });
      setNotice('Staff profile created.');
      setForm({ user_id: '', first_name: '', last_name: '', email: '', role_id: '', entity_id: '' });
      await load();
    } catch (e) {
      setError(e.message || 'Failed to create staff profile');
    }
  };

  const saveEntity = async (profile) => {
    setError('');
    setNotice('');
    try {
      await updateOpsStaff(profile.id, { entity_id: entityFor.entityId || null });
      setNotice('Staff entity assignment updated.');
      setEntityFor({ profileId: '', entityId: '' });
      await load();
    } catch (e) {
      setError(e.message || 'Failed to update staff entity');
    }
  };

  return (
    <div>
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Create staff profile</h3>
        <div className="workspace-grid">
          <div className="workspace-field">
            <label>User ID</label>
            <input value={form.user_id} onChange={(e) => setForm({ ...form, user_id: e.target.value })} />
          </div>
          <div className="workspace-field">
            <label>Email</label>
            <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div className="workspace-field">
            <label>First name</label>
            <input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
          </div>
          <div className="workspace-field">
            <label>Last name</label>
            <input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
          </div>
          <div className="workspace-field">
            <label>Role</label>
            <select value={form.role_id} onChange={(e) => setForm({ ...form, role_id: e.target.value })}>
              <option value="">Select role</option>
              {roles.map((r) => <option key={r.id || r.name} value={r.id || r.name}>{r.name}</option>)}
            </select>
          </div>
          <div className="workspace-field">
            <label>Processing entity (optional — entity staff scope)</label>
            <select value={form.entity_id} onChange={(e) => setForm({ ...form, entity_id: e.target.value })}>
              <option value="">CarbonTally internal</option>
              {entities.map((entity) => (
                <option key={entity.id} value={entity.id}>{entity.name}</option>
              ))}
            </select>
          </div>
          <div className="workspace-actions">
            <button className="v3-btn primary" onClick={create}>Create</button>
          </div>
        </div>
      </div>

      <div className="workspace-pane">
        <h3>Staff roster ({staff.length})</h3>
        <table className="v3-ops-table">
          <thead>
            <tr><th>Name</th><th>Email</th><th>Role</th><th>Type</th><th>Active</th>{canManage && <th>Entity</th>}</tr>
          </thead>
          <tbody>
            {staff.map((p) => (
              <tr key={p.id}>
                <td>{p.first_name} {p.last_name}</td>
                <td>{p.email}</td>
                <td>{p.role_name || p.role_id || '—'}</td>
                <td>{p.entity_id ? 'Processing entity' : 'CarbonTally internal'}</td>
                <td>{p.is_active ? 'Yes' : 'No'}</td>
                {canManage && (
                  <td>
                    {entityFor.profileId === p.id ? (
                      <span>
                        <select
                          value={entityFor.entityId}
                          onChange={(e) => setEntityFor({ ...entityFor, entityId: e.target.value })}
                        >
                          <option value="">CarbonTally internal</option>
                          {entities.map((entity) => (
                            <option key={entity.id} value={entity.id}>{entity.name}</option>
                          ))}
                        </select>
                        <button className="v3-btn v3-btn-sm" onClick={() => saveEntity(p)}>Save</button>
                        <button className="v3-btn v3-btn-sm" onClick={() => setEntityFor({ profileId: '', entityId: '' })}>Cancel</button>
                      </span>
                    ) : (
                      <button
                        className="v3-btn v3-btn-sm"
                        onClick={() => setEntityFor({ profileId: p.id, entityId: p.entity_id || '' })}
                      >
                        {p.entity_id ? 'Change' : 'Assign'}
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
