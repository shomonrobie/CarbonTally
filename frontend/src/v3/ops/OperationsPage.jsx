// frontend/src/v3/ops/OperationsPage.jsx
// CarbonTally V3 Internal Operations hub — role-aware tabs over the real
// /api/v3/ops/* surface. Every screen reads live server data; the frontend
// never fabricates numbers.
import React, { useEffect, useState } from 'react';
import { Navigate, useSearchParams } from 'react-router-dom';
import { getOpsMe } from '../api';
import { LoadingState } from '../components/ui';
import OpsDashboard from './OpsDashboard';
import OperatorQueue from './OperatorQueue';
import ProcessingEntitiesTab from './ProcessingEntitiesTab';
import ReviewQueue from './ReviewQueue';
import CtQcTab from './CtQcTab';
import QcQueue from './QcQueue';
import SlaTab from './SlaTab';
import StaffRoster from './StaffRoster';
import StaffRolesTab from './StaffRolesTab';
import CommercialTab from './CommercialTab';
import SettingsTab from './SettingsTab';
import IssuesTriageTab from './IssuesTriageTab';
import AuditConsoleTab from './AuditConsoleTab';
import OpsMessagingTab from './OpsMessagingTab';
import OpsPeMessagingTab from './OpsPeMessagingTab';
import OpsAssignmentsTab from './OpsAssignmentsTab';
import OperationalHealthTab from './OperationalHealthTab';
import './ops.css';

export default function OperationsPage() {
  const [tab, setTab] = useState('dashboard');
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchParams] = useSearchParams();

  // CL-59 — queue-state restoration: the routed item workspace links back with
  // ?tab=<queue>, so "Back to queue" returns to the correct operational tab.
  const requestedTab = searchParams.get('tab');
  useEffect(() => {
    if (requestedTab) setTab(requestedTab);
  }, [requestedTab]);

  useEffect(() => {
    getOpsMe()
      .then(setMe)
      .catch((e) => { setError(e.message || 'Failed to load staff profile'); setMe(null); })
      .finally(() => setLoading(false));
  }, []);

  // V1.2 FINAL (PEShell) — Processing Entity staff never see the shared
  // Internal Operations hub: /ops redirects to the dedicated PE application
  // (/pe → PEShell). The backend /api/v3/pe/* + /api/v3/me/context surfaces
  // remain authoritative; this is navigation-only defence-in-depth.
  if (me?.profile?.entity_id) {
    return <Navigate to="/pe" replace />;
  }

  // CL-62 — tabs are permission-aware: a tab is only rendered when the API it
  // calls is legitimate for the caller's role (the backend remains the
  // authoritative boundary; this is navigation, never authorization).
  const roleName = me?.profile?.role_name;
  const p = me?.permissions || {};
  // /api/v3/qc/* and /api/v3/issues/admin/open are gated by require_admin()
  // (CarbonTally-internal global admin).
  const isGlobalAdmin = ['admin', 'system_admin'].includes(roleName);

  const TABS = [];
  if (p.can_view_all) TABS.push({ id: 'dashboard', label: 'Dashboard', component: OpsDashboard });
  // Phase 8-X X5 — operational health (read-only view over the X1/X4 endpoints).
  // Gated on the same `can_view_all` permission those endpoints enforce server-side.
  if (p.can_view_all) {
    TABS.push({
      id: 'operational-health',
      label: 'Operational health',
      component: OperationalHealthTab,
    });
  }
  if (p.can_process) TABS.push({ id: 'data-entry', label: 'Data entry', component: OperatorQueue });
  if (p.can_review) TABS.push({ id: 'review', label: 'Review', component: ReviewQueue });
  // WS4 continuation — Operations D38 assignment tab for internal staff with
  // process/review capability.
  if (p.can_process || p.can_review) {
    TABS.push({ id: 'assignments', label: 'Assignments', component: OpsAssignmentsTab });
  }
  // V1.2 — late CarbonTally QC gate: the shared row permission `can_qc`
  // (granted to internal qc_specialist + admin by the V1.2 migration) is the
  // nav gate. Processing Entity staff never reach this code path (the
  // entity_id branch above returns the PE workspace first); the backend
  // require_internal_staff + can_qc checks stay authoritative.
  if (p.can_qc) TABS.push({ id: 'ctqc', label: 'CarbonTally QC', component: CtQcTab });
  if (isGlobalAdmin) TABS.push({ id: 'qc', label: 'QC', component: QcQueue });
  if (p.can_manage_staff) {
    TABS.push(
      { id: 'staff', label: 'Staff', component: StaffRoster },
      { id: 'roles', label: 'Roles', component: StaffRolesTab },
      { id: 'entities', label: 'Entities', component: ProcessingEntitiesTab },
      { id: 'sla', label: 'SLA', component: SlaTab },
      { id: 'messaging', label: 'Messaging', component: OpsMessagingTab },
      { id: 'peops', label: 'PE messages', component: OpsPeMessagingTab },
      { id: 'audit', label: 'Audit', component: AuditConsoleTab },
      { id: 'settings', label: 'Settings', component: SettingsTab },
    );
  }
  if (isGlobalAdmin) TABS.push({ id: 'issues', label: 'Issues', component: IssuesTriageTab });
  if (p.can_manage_billing) {
    // D37-0 — the Commercial surface requires the real can_manage_billing
    // staff permission (server-side enforced; this tab is the entry point).
    TABS.push({ id: 'commercial', label: 'Commercial', component: CommercialTab });
  }
  // Defensive default — if the profile has no resolved permissions yet, show
  // the dashboard tab (its own API enforces the can_view_all gate).
  if (TABS.length === 0) TABS.push({ id: 'dashboard', label: 'Dashboard', component: OpsDashboard });

  const Active = TABS.find((t) => t.id === tab)?.component || TABS[0].component;
  const activeId = TABS.find((t) => t.id === tab) ? tab : TABS[0].id;

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
          <button key={t.id} className={`v3-ops-tab${activeId === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>
      {loading ? <LoadingState label="Loading operations…" /> : <Active canManage={!!p.can_manage_staff} />}
    </div>
  );
}
