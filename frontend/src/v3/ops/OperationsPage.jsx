// frontend/src/v3/ops/OperationsPage.jsx
// CarbonTally V3 Internal Operations hub — role-aware tabs over the real
// /api/v3/ops/* surface. Every screen reads live server data; the frontend
// never fabricates numbers.
import React, { useEffect, useState } from 'react';
import { getOpsMe } from '../api';
import EntityExtractionWorkspace from './EntityExtractionWorkspace';
import OpsDashboard from './OpsDashboard';
import OperatorQueue from './OperatorQueue';
import ProcessingEntitiesTab from './ProcessingEntitiesTab';
import ReviewQueue from './ReviewQueue';
import QcQueue from './QcQueue';
import SlaTab from './SlaTab';
import StaffRoster from './StaffRoster';
import StaffRolesTab from './StaffRolesTab';
import CommercialTab from './CommercialTab';
import './ops.css';

const BASE_TABS = [
  { id: 'dashboard', label: 'Dashboard', component: OpsDashboard },
  { id: 'data-entry', label: 'Data entry', component: OperatorQueue },
  { id: 'review', label: 'Review', component: ReviewQueue },
  { id: 'qc', label: 'QC', component: QcQueue },
  { id: 'staff', label: 'Staff', component: StaffRoster },
  { id: 'roles', label: 'Roles', component: StaffRolesTab },
];

export default function OperationsPage() {
  const [tab, setTab] = useState('dashboard');
  const [me, setMe] = useState(null);
  const [error] = useState('');

  useEffect(() => {
    getOpsMe()
      .then(setMe)
      .catch(() => setMe(null));
  }, []);

  // D22: Processing Entity staff never see the CarbonTally-internal tabs — they
  // get the entity-scoped extraction workspace for their own entity.
  if (me?.profile?.entity_id) {
    return <EntityExtractionWorkspace entityId={me.profile.entity_id} />;
  }

  const canManageStaff = !!(me?.permissions?.can_manage_staff);
  const canManageBilling = !!(me?.permissions?.can_manage_billing);
  const TABS = canManageStaff
    ? BASE_TABS.concat([
        { id: 'entities', label: 'Entities', component: ProcessingEntitiesTab },
        { id: 'sla', label: 'SLA', component: SlaTab },
      ])
    : BASE_TABS;
  if (canManageBilling) {
    // D37-0 — the Commercial surface requires the real can_manage_billing
    // staff permission (server-side enforced; this tab is the entry point).
    TABS.push({ id: 'commercial', label: 'Commercial', component: CommercialTab });
  }

  const Active = TABS.find((t) => t.id === tab).component;

  return (
    <div className="v3-ops-page">
      <div className="v3-ops-header">
        <div>
          <h1>Internal Operations</h1>
          <div className="subtitle">
            {me ? `${me.profile?.first_name} ${me.profile?.last_name} · ${me.profile?.role_name || 'staff'}` : 'CarbonTally workforce'}
          </div>
        </div>
      </div>
      {error && <div className="v3-ops-error">{error}</div>}
      <div className="v3-ops-tabs">
        {TABS.map((t) => (
          <button key={t.id} className={`v3-ops-tab${tab === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>
      <Active canManage={canManageStaff} />
    </div>
  );
}
