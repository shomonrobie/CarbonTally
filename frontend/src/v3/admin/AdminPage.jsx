// frontend/src/v3/admin/AdminPage.jsx
// CarbonTally V3 — Customer Administration hub. All data is real V3 backend
// data (org-scoped); the security tab uses the existing Supabase Auth client.
// Navigation model (D18/R2): Overview, Locations, Facilities, Assets, Vehicles,
// Suppliers, Members, Custom Factors, Security.
import React, { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { listOrgRoles, resolveV3Membership, resolveV3Organization } from '../api';
import { ErrorState } from '../components/StateViews';
import ProfileTab from './ProfileTab';
import MembersTab from './MembersTab';
// CT-CONSULTANT-CLIENT-ACCESS-UX-01 — a consultant operating a managed client
// must use the consultant-plane "Client Access" surface (server-gated CT-04
// consultant endpoints), NOT the Organisation-admin Members & Invitations tab
// (which is org-member/org-admin gated and returns 403 for a consultant).
import ClientAccessTab from '../consultant/ClientAccessTab';
import { useConsultantClientContext } from '../consultant/ConsultantClientContext';
import SuppliersTab from './SuppliersTab';
import FacilitiesTab from './FacilitiesTab';
import LocationsTab from './LocationsTab';
import VehiclesTab from './VehiclesTab';
import CustomFactorsTab from './CustomFactorsTab';
import ActivityTab from './ActivityTab';
import SecurityTab from './SecurityTab';
// Phase 7 — Auditor / Assurance: customer audit & evidence surface.
import AuditTab from './AuditTab';
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
  // Owner/admin only (the backend independently enforces this).
  { id: 'audit', label: 'Audit & evidence', adminOnly: true },
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
  const [searchParams] = useSearchParams();

  // CT-CONSULTANT-CLIENT-ACCESS-UX-01 — are we operating a managed client FOR a
  // consultant firm? The id is presentation context only; the backend re-checks
  // every request. Outside the client plane this is inactive and the direct
  // customer Members & Invitations surface is unchanged.
  const consultantCtx = useConsultantClientContext();
  const consultantClientId =
    consultantCtx && consultantCtx.active ? consultantCtx.clientId : null;

  // CL-44/CL-47 — the mapping workspace deep-links to the Custom Factors tab
  // (?tab=factors) when the user chooses the "create a customer factor" path.
  const requestedTab = searchParams.get('tab');
  useEffect(() => {
    if (requestedTab && TABS.some((t) => t.id === requestedTab)) {
      setActiveTab(requestedTab);
    }
  }, [requestedTab]);

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
      // A consultant is not an organisation member, so the org-scoped roles list
      // is not available/needed in the client plane (and probing it would emit a
      // 403). The consultant-plane Client Access tab carries its own role model.
      if (!consultantClientId) {
        const roleResult = await listOrgRoles(org.id).catch(() => ({ roles: [] }));
        setRoles(roleResult.roles || []);
      } else {
        setRoles([]);
      }
    } catch (e) {
      setError(e.message || 'Failed to load organization');
    } finally {
      setLoading(false);
    }
  }, [consultantClientId]);

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

  // CT-CONSULTANT-CLIENT-ACCESS-UX-01 — in the client plane the members surface
  // is presented as the consultant-appropriate "Client Access" (same tab id so
  // ?tab=members deep links keep working).
  const tabs = consultantClientId
    ? TABS.map((tab) => (tab.id === 'members' ? { ...tab, label: 'Client Access' } : tab))
    : TABS;

  return (
    <div className="v3-admin-page">
      <div className="v3-admin-header">
        <div>
          <h1>Organisation administration</h1>
          <p className="subtitle">
            {consultantClientId
              ? `${organization.name} · managed client organisation`
              : `${organization.name} · Customer administration`}
          </p>
        </div>
      </div>

      <div className="v3-tabs">
        {tabs.filter((tab) => !tab.adminOnly || isAdmin).map((tab) => (
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
        consultantClientId ? (
          <ClientAccessTab clientId={consultantClientId} />
        ) : (
          <MembersTab organization={organization} roles={roles} />
        )
      )}
      {activeTab === 'suppliers' && <SuppliersTab organization={organization} />}
      {activeTab === 'facilities' && <FacilitiesTab organization={organization} />}
      {activeTab === 'locations' && <LocationsTab organization={organization} />}
      {activeTab === 'vehicles' && <VehiclesTab organization={organization} isAdmin={isAdmin} />}
      {activeTab === 'factors' && <CustomFactorsTab organization={organization} isAdmin={isAdmin} />}
      {activeTab === 'activity' && <ActivityTab organization={organization} />}
      {activeTab === 'audit' && isAdmin && <AuditTab organization={organization} />}
      {activeTab === 'security' && <SecurityTab />}
    </div>
  );
}

