// frontend/src/v3/admin/AdminPage.jsx
// CarbonTally V3 — Customer Administration hub. All data is real V3 backend
// data (org-scoped); the security tab uses the existing Supabase Auth client.
import React, { useCallback, useEffect, useState } from 'react';
import { listOrgRoles, resolveV3Organization } from '../api';
import { ErrorState } from '../components/StateViews';
import ProfileTab from './ProfileTab';
import MembersTab from './MembersTab';
import SuppliersTab from './SuppliersTab';
import FacilitiesTab from './FacilitiesTab';
import SecurityTab from './SecurityTab';
import './admin.css';

const TABS = [
  { id: 'profile', label: 'Profile & Settings' },
  { id: 'members', label: 'Members & Invitations' },
  { id: 'suppliers', label: 'Suppliers' },
  { id: 'facilities', label: 'Facilities & Assets' },
  { id: 'security', label: 'Security' },
];

export default function AdminPage() {
  const [organization, setOrganization] = useState(null);
  const [roles, setRoles] = useState([]);
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const org = await resolveV3Organization();
      if (!org) {
        setError('No organization is linked to this account.');
        setLoading(false);
        return;
      }
      setOrganization(org);
      const roleResult = await listOrgRoles(org.id).catch(() => ({ roles: [] }));
      setRoles(roleResult.roles || []);
    } catch (e) {
      setError(e.message || 'Failed to load organization');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load, retryCount]);

  if (loading) {
    return (
      <div className="v3-admin-page">
        <div className="v3-loading"><div className="spinner" />Loading organization…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="v3-admin-page">
        <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />
      </div>
    );
  }

  return (
    <div className="v3-admin-page">
      <div className="v3-admin-header">
        <div>
          <h1>Organization administration</h1>
          <p className="subtitle">{organization.name} · V3 customer administration</p>
        </div>
      </div>

      <div className="v3-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`v3-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'profile' && <ProfileTab organization={organization} />}
      {activeTab === 'members' && (
        <MembersTab organization={organization} roles={roles} />
      )}
      {activeTab === 'suppliers' && <SuppliersTab organization={organization} />}
      {activeTab === 'facilities' && <FacilitiesTab organization={organization} />}
      {activeTab === 'security' && <SecurityTab />}
    </div>
  );
}
