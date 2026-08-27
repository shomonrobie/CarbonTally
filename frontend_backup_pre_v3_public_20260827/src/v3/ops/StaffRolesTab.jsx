// frontend/src/v3/ops/StaffRolesTab.jsx
// D25 — read-only staff role/permission reference. `staff_roles` remains the
// authoritative staff-permission source; this page only renders it. The legacy
// `roles` table is shown for reference only and must never become staff
// authorization. Processing Entity staff never gain authority here.
import React, { useEffect, useState } from 'react';
import { listStaffRoles } from '../api';

export default function StaffRolesTab() {
  const [roles, setRoles] = useState([]);
  const [error, setError] = useState('');
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    listStaffRoles()
      .then((data) => setRoles(data.staff_roles || []))
      .catch((e) => setError(e.message || 'Failed to load staff roles'))
      .finally(() => setLoaded(true));
  }, []);

  if (!loaded) return <div className="v3-loading"><div className="spinner" />Loading roles…</div>;
  if (error) return <div className="v3-ops-error">{error}</div>;

  return (
    <div>
      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Staff roles — read-only reference</h3>
        <p className="muted">
          Permissions are the real <code>staff_roles.permissions</code> flags used by the backend.
          This page cannot change authorization.
        </p>
        <table className="v3-ops-table">
          <thead>
            <tr><th>Role</th><th>Scope</th><th>Permissions</th></tr>
          </thead>
          <tbody>
            {roles.map((role) => (
              <tr key={role.id || role.name}>
                <td>{role.name}</td>
                <td>{role.entity_id ? 'Processing entity' : 'CarbonTally internal'}</td>
                <td>{Object.entries(role.permissions || {})
                  .filter(([, value]) => value)
                  .map(([key]) => key)
                  .join(', ') || '—'}</td>
              </tr>
            ))}
            {roles.length === 0 && (
              <tr><td colSpan={3}>No staff roles found.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
