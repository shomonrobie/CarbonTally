// frontend/src/v3/ops/OperationsPage.jsx
// CarbonTally V3 Internal Operations hub — role-aware tabs over the real
// /api/v3/ops/* surface. Every screen reads live server data; the frontend
// never fabricates numbers.
import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getOpsMe } from '../api';
import { LoadingState } from '../components/ui';
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
import SettingsTab from './SettingsTab';
import IssuesTriageTab from './IssuesTriageTab';
import AuditConsoleTab from './AuditConsoleTab';
import OpsMessagingTab from './OpsMessagingTab';
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

  // D22: Processing Entity staff never see the CarbonTally-internal tabs — they
  // get the entity-scoped extraction workspace for their own entity.
  if (me?.profile?.entity_id) {
    return <EntityExtractionWorkspace entityId={me.profile.entity_id} />;
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
  if (p.can_process) TABS.push({ id: 'data-entry', label: 'Data entry', component: OperatorQueue });
  if (p.can_review) TABS.push({ id: 'review', label: 'Review', component: ReviewQueue });
  if (isGlobalAdmin) TABS.push({ id: 'qc', label: 'QC', component: QcQueue });
  if (p.can_manage_staff) {
    TABS.push(
      { id: 'staff', label: 'Staff', component: StaffRoster },
      { id: 'roles', label: 'Roles', component: StaffRolesTab },
      { id: 'entities', label: 'Entities', component: ProcessingEntitiesTab },
      { id: 'sla', label: 'SLA', component: SlaTab },
      { id: 'messaging', label: 'Messaging', component: OpsMessagingTab },
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
