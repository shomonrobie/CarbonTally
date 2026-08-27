// frontend/src/v3/admin/AdminPage.jsx
// CarbonTally V3 — Customer Administration hub. All data is real V3 backend
// data (org-scoped); the security tab uses the existing Supabase Auth client.
// Navigation model (D18/R2): Overview, Locations, Facilities, Assets, Vehicles,
// Suppliers, Members, Custom Factors, Security.
import React, { useCallback, useEffect, useState } from 'react';
import { listOrgRoles, resolveV3Membership, resolveV3Organization } from '../api';
import { ErrorState } from '../components/StateViews';
import ProfileTab from './ProfileTab';
import MembersTab from './MembersTab';
import SuppliersTab from './SuppliersTab';
import FacilitiesTab from './FacilitiesTab';
import LocationsTab from './LocationsTab';
import VehiclesTab from './VehiclesTab';
import CustomFactorsTab from './CustomFactorsTab';
import ActivityTab from './ActivityTab';
import SecurityTab from './SecurityTab';
import './admin.css';

const TABS = [
  { id: 'profile', label: 'Overview & Settings' },
  { id: 'locations', label: 'Locations' },
  { id: 'facilities', label: 'Facilities & Assets' },
  { id: 'vehicles', label: 'Vehicles' },
  { id: 'suppliers', label: 'Suppliers' },
  { id: 'members', label: 'Members & Invitations' },
  { id: 'factors', label: 'Custom Factors' },
  { id: 'activity', label: 'Activity' },
  { id: 'security', label: 'Security' },
];

export default function AdminPage() {
  const [organization, setOrganization] = useState(null);
  const [roles, setRoles] = useState([]);
  const [myRole, setMyRole] = useState(null);
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
      const membership = await resolveV3Membership().catch(() => null);
      setMyRole(membership?.role || null);
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

  const isAdmin = ['owner', 'admin'].includes(myRole);

  return (
    <div className="v3-admin-page">
      <div className="v3-admin-header">
        <div>
          <h1>Organisation administration</h1>
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
      {activeTab === 'locations' && <LocationsTab organization={organization} />}
      {activeTab === 'vehicles' && <VehiclesTab organization={organization} isAdmin={isAdmin} />}
      {activeTab === 'factors' && <CustomFactorsTab organization={organization} isAdmin={isAdmin} />}
      {activeTab === 'activity' && <ActivityTab organization={organization} />}
      {activeTab === 'security' && <SecurityTab />}
    </div>
  );
}

