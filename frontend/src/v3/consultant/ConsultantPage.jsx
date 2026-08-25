// frontend/src/v3/consultant/ConsultantPage.jsx
// CarbonTally V3 — Consultant / Multi-client hub.
//
// Critical UX: the active client context is explicit everywhere. The switcher
// sets the active client; every workspace request carries the client id and the
// backend re-authorizes it server-side (client A/B allowed, C denied). The UI
// never relies on hiding links — a denied client request surfaces as an error.
import React, { useCallback, useEffect, useState } from 'react';
import {
  getClientDashboard,
  getClientIssues,
  getClientProcessingStatus,
  getClientReports,
  getConsultantBranding,
  getConsultantBrandingContext,
  getConsultantClientDetail,
  getConsultantDashboard,
  getConsultantPortfolio,
  getConsultantProfile,
  listConsultantClients,
  updateConsultantBranding,
  updateConsultantClientStatus,
  endConsultantClient,
  reactivateConsultantClient,
  suspendConsultantClient,
} from '../api';
import WhiteLabelTab from './WhiteLabelTab';
import ClientMessagingTab from './ClientMessagingTab';
import { ErrorState } from '../components/StateViews';
import './consultant.css';

const YEAR = new Date().getFullYear();

function LoadingBlock({ label }) {
  return <div className="v3-loading"><div className="spinner" />{label}</div>;
}

function ErrorBlock({ message }) {
  return <div className="v3-error">{message}</div>;
}

function DashboardView({ dashboard }) {
  const [portfolio, setPortfolio] = useState(null);
  const [portfolioError, setPortfolioError] = useState('');
  const [activeClient, setActiveClient] = useState(null);
  const [clientDetail, setClientDetail] = useState(null);
  const [clientDetailError, setClientDetailError] = useState('');

  useEffect(() => {
    getConsultantPortfolio()
      .then(setPortfolio)
      .catch((e) => setPortfolioError(e.message || 'Portfolio reporting unavailable'));
  }, []);

  const openClient = (clientId) => {
    setActiveClient(clientId);
    setClientDetail(null);
    setClientDetailError('');
    getConsultantClientDetail(clientId)
      .then(setClientDetail)
      .catch((e) => setClientDetailError(e.message || 'Client reporting unavailable'));
  };

  if (activeClient && (clientDetail || clientDetailError)) {
    return (
      <div>
        <button className="v3-btn" onClick={() => setActiveClient(null)}>← Back to portfolio</button>
        {clientDetailError ? (
          <div className="v3-muted" style={{ marginTop: 12 }}>{clientDetailError}</div>
        ) : clientDetail ? (
          <div className="v3-admin-card" style={{ marginTop: 12 }}>
            <h2>{clientDetail.client_name} — reporting</h2>
            <div className="v3-consultant-grid">
              <div className="v3-summary-card"><div className="label">Documents</div><div className="value">{clientDetail.documents}</div></div>
              <div className="v3-summary-card"><div className="label">Items total</div><div className="value">{clientDetail.items?.total}</div></div>
              <div className="v3-summary-card"><div className="label">Items completed</div><div className="value completed">{clientDetail.items?.completed}</div></div>
              <div className="v3-summary-card"><div className="label">Open issues</div><div className="value failed">{clientDetail.issues?.open}</div></div>
              <div className="v3-summary-card"><div className="label">Ready reports</div><div className="value completed">{clientDetail.reports?.ready}</div></div>
              <div className="v3-summary-card"><div className="label">Emissions</div><div className="value">{((clientDetail.emissions?.total_kg ?? 0) / 1000) > 0 ? `${((clientDetail.emissions?.total_kg ?? 0) / 1000).toFixed(2)} tCO₂e` : 'No data'}</div></div>
            </div>
            <h3 style={{ marginTop: 12 }}>Processing stage breakdown</h3>
            <table className="v3-table" style={{ marginTop: 8 }}>
              <thead><tr><th>Stage</th><th>Items</th></tr></thead>
              <tbody>
                {Object.entries(clientDetail.items?.by_stage || {})
                  .filter(([, n]) => n > 0)
                  .map(([stage, n]) => <tr key={stage}><td>{stage}</td><td>{n}</td></tr>)}
              </tbody>
            </table>
            {clientDetail.emissions?.by_scope?.length > 0 && (
              <>
                <h3 style={{ marginTop: 12 }}>Emissions by scope</h3>
                <table className="v3-table" style={{ marginTop: 8 }}>
                  <thead><tr><th>Scope</th><th>tCO₂e</th><th>Rows</th></tr></thead>
                  <tbody>
                    {clientDetail.emissions.by_scope.map((s) => (
                      <tr key={s.scope}><td>{s.scope}</td><td>{(s.kg / 1000).toFixed(2)}</td><td>{s.rows}</td></tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </div>
        ) : (
          <div className="v3-loading" style={{ marginTop: 12 }}><div className="spinner" />Loading client reporting…</div>
        )}
      </div>
    );
  }

  return (
    <div>
      <div className="v3-consultant-grid">
        <div className="v3-summary-card"><div className="label">Clients</div><div className="value">{dashboard.client_count}</div></div>
        <div className="v3-summary-card"><div className="label">Active clients</div><div className="value completed">{dashboard.active_client_count}</div></div>
        <div className="v3-summary-card"><div className="label">Pending reviews</div><div className="value pending">{dashboard.pending_reviews}</div></div>
        <div className="v3-summary-card"><div className="label">Open issues</div><div className="value failed">{dashboard.open_issues}</div></div>
        <div className="v3-summary-card"><div className="label">Ready reports</div><div className="value completed">{dashboard.ready_reports}</div></div>
      </div>

      {portfolioError ? (
        <div className="v3-card"><div className="v3-muted">{portfolioError}</div></div>
      ) : portfolio ? (
        <div className="v3-admin-card">
          <h2>Portfolio health</h2>
          <div className="v3-consultant-grid">
            <div className="v3-summary-card"><div className="label">Active</div><div className="value completed">{portfolio.portfolio?.active ?? 0}</div></div>
            <div className="v3-summary-card"><div className="label">Suspended</div><div className="value pending">{portfolio.portfolio?.suspended ?? 0}</div></div>
            <div className="v3-summary-card"><div className="label">Ended</div><div className="value failed">{portfolio.portfolio?.ended ?? 0}</div></div>
            <div className="v3-summary-card"><div className="label">Clients in detail</div><div className="value">{portfolio.clients?.length ?? 0}</div></div>
          </div>
          {portfolio.clients?.length > 0 ? (
            <table className="v3-table" style={{ marginTop: 12 }}>
              <thead>
                <tr><th>Client</th><th>Documents</th><th>Items</th><th>Open issues</th><th>Ready reports</th><th></th></tr>
              </thead>
              <tbody>
                {portfolio.clients.map((c) => (
                  <tr key={c.client_id}>
                    <td>{c.client_name}</td>
                    <td>{c.documents}</td>
                    <td>{c.items}</td>
                    <td>{c.open_issues}</td>
                    <td>{c.ready_reports}</td>
                    <td>
                      <button className="v3-btn v3-btn-sm" onClick={() => openClient(c.client_id)}>
                        Reporting →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="v3-empty" style={{ marginTop: 12 }}>No active client grants.</p>
          )}
        </div>
      ) : (
        <div className="v3-loading"><div className="spinner" />Loading portfolio…</div>
      )}
    </div>
  );
}

function ClientWorkspace({ client, clientId }) {
  const [reports, setReports] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [processing, setProcessing] = useState(null);
  const [issues, setIssues] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const [rep, dash, proc, iss] = await Promise.all([
          getClientReports(clientId),
          getClientDashboard(clientId, `${YEAR}-01-01`, `${YEAR}-12-31`),
          getClientProcessingStatus(clientId),
          getClientIssues(clientId),
        ]);
        setReports(rep);
        setDashboard(dash);
        setProcessing(proc);
        setIssues(iss);
      } catch (e) {
        setError(e.message || 'Failed to load client workspace');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [clientId]);

  if (loading) return <LoadingBlock label="Loading client workspace…" />;
  if (error) return <ErrorBlock message={error} />;

  const processingStatus = processing?.status || {};
  const stageCounts = Object.entries(processingStatus)
    .filter(([, value]) => typeof value === 'number')
    .map(([stage, count]) => ({ stage, count }));

  return (
    <div>
      <div className="v3-workspace-banner">
        ⚠ You are working on: <strong>{client?.client_name}</strong> — every action here applies to this client only.
      </div>

      <div className="v3-consultant-grid">
        <div className="v3-summary-card"><div className="label">Total CO2e ({YEAR})</div><div className="value completed">{dashboard?.total_co2e_kg || '0'}</div></div>
        <div className="v3-summary-card"><div className="label">Rows</div><div className="value">{dashboard?.total_rows || 0}</div></div>
        <div className="v3-summary-card"><div className="label">Open issues</div><div className="value failed">{issues?.issues?.filter((i) => i.status === 'open').length || 0}</div></div>
        <div className="v3-summary-card"><div className="label">Reports</div><div className="value">{reports?.reports?.length || 0}</div></div>
      </div>

      <div className="v3-admin-card">
        <h2>Processing status</h2>
        {stageCounts.length === 0 ? (
          <div className="v3-empty" style={{ padding: 20 }}>No processing stages active.</div>
        ) : (
          <table className="v3-table">
            <thead><tr><th>Stage</th><th>Count</th></tr></thead>
            <tbody>
              {stageCounts.map((row) => (
                <tr key={row.stage}><td>{row.stage}</td><td>{row.count}</td></tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="v3-admin-card">
        <h2>Reports</h2>
        {reports?.reports?.length === 0 ? (
          <div className="v3-empty" style={{ padding: 20 }}>No reports yet.</div>
        ) : (
          <table className="v3-table">
            <thead><tr><th>Report</th><th>Period</th><th>Status</th></tr></thead>
            <tbody>
              {(reports?.reports || []).map((report) => (
                <tr key={report.id}>
                  <td>{report.report_name || `${report.report_type} ${report.reporting_year}`}</td>
                  <td>{report.reporting_year}</td>
                  <td><span className={`v3-status ${report.status}`}><span className="dot" />{report.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

const MODE_LABELS = {
  carbon_tally: 'CarbonTally (default)',
  consultant: 'White-label — consultant brand only',
  co_branded: 'Co-branded — consultant + CarbonTally',
};

const EMPTY_TEXT_KEYS = [
  'logo_url', 'footer_text', 'email_from', 'website',
  'support_email', 'support_phone', 'support_hours', 'client_portal_url',
];

function BrandingView() {
  const [data, setData] = useState(null);
  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const branding = await getConsultantBranding();
        const b = branding.branding || {};
        setData(branding);
        setForm({
          brand_name: b.brand_name || '',
          logo_url: b.logo_url || '',
          primary_color: b.primary_color || '#0f766e',
          secondary_color: b.secondary_color || '#0e7490',
          footer_text: b.footer_text || '',
          email_from: b.email_from || '',
          website: b.website || '',
          support_email: b.support_email || '',
          support_phone: b.support_phone || '',
          support_hours: b.support_hours || '',
          client_portal_url: b.client_portal_url || '',
          white_label_enabled: !!b.white_label_enabled,
          co_branding_enabled: !!b.co_branding_enabled,
        });
      } catch (e) {
        setError(e.message || 'Failed to load branding');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <LoadingBlock label="Loading branding…" />;
  if (error && !data) return <ErrorBlock message={error} />;
  if (!data || !form) return null;

  const canManage = !!data.can_manage_branding;
  const context = data.brand_context || {};
  const fieldError = (key) => (fieldErrors[key] ? <div className="v3-form-error">{fieldErrors[key]}</div> : null);

  const onSave = async () => {
    setSaving(true);
    setSuccess('');
    setError('');
    setFieldErrors({});
    try {
      const payload = { ...form };
      EMPTY_TEXT_KEYS.forEach((k) => {
        if (!payload[k]) payload[k] = null;
      });
      if (!payload.brand_name) payload.brand_name = null;
      const updated = await updateConsultantBranding(payload);
      const b = updated.branding || {};
      setData(updated);
      setForm((f) => ({
        ...f,
        brand_name: b.brand_name || '',
        logo_url: b.logo_url || '',
        primary_color: b.primary_color || f.primary_color,
        secondary_color: b.secondary_color || f.secondary_color,
        footer_text: b.footer_text || '',
        email_from: b.email_from || '',
        website: b.website || '',
        support_email: b.support_email || '',
        support_phone: b.support_phone || '',
        support_hours: b.support_hours || '',
        client_portal_url: b.client_portal_url || '',
        white_label_enabled: !!b.white_label_enabled,
        co_branding_enabled: !!b.co_branding_enabled,
      }));
      setSuccess('Branding saved.');
    } catch (e) {
      const detail = e.raw;
      if (Array.isArray(detail)) {
        const errs = {};
        detail.forEach((item) => {
          if (item && item.loc && item.loc.length > 1) {
            errs[item.loc[item.loc.length - 1]] = item.msg;
          }
        });
        setFieldErrors(errs);
        setError('Please fix the highlighted fields.');
      } else {
        setError(e.message || String(detail || 'Failed to save branding'));
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="v3-admin-card">
        <h2>Brand preview</h2>
        <div className="v3-brand-preview" style={{ borderTopColor: context.primary_color }}>
          <div className="v3-brand-preview-row">
            {context.logo_url && <img className="v3-brand-logo" src={context.logo_url} alt="brand logo" />}
            <div>
              <div className="v3-brand-name">{context.display_name || 'CarbonTally'}</div>
              <div className="v3-brand-mode">{MODE_LABELS[context.kind] || context.kind}</div>
            </div>
          </div>
          {context.co_branded_with_carbontally && (
            <div className="v3-brand-cobrand">+ CarbonTally</div>
          )}
        </div>
      </div>

      <div className="v3-admin-card">
        <h2>Firm branding</h2>
        {!canManage && (
          <p className="v3-muted">
            Only the firm owner or a member with team-management permission can
            change branding.
          </p>
        )}
        {error && <ErrorBlock message={error} />}
        {success && <div className="v3-success">{success}</div>}

        <div className="v3-form-grid">
          <label>
            Brand / display name
            <input
              value={form.brand_name}
              disabled={!canManage}
              maxLength={200}
              onChange={(e) => setForm((f) => ({ ...f, brand_name: e.target.value }))}
            />
            {fieldError('brand_name')}
          </label>
          <label>
            Logo URL
            <input
              value={form.logo_url}
              disabled={!canManage}
              placeholder="https://…"
              onChange={(e) => setForm((f) => ({ ...f, logo_url: e.target.value }))}
            />
            {fieldError('logo_url')}
          </label>
          <label>
            Primary colour
            <input
              type="color"
              value={form.primary_color}
              disabled={!canManage}
              onChange={(e) => setForm((f) => ({ ...f, primary_color: e.target.value }))}
            />
            {fieldError('primary_color')}
          </label>
          <label>
            Secondary colour
            <input
              type="color"
              value={form.secondary_color}
              disabled={!canManage}
              onChange={(e) => setForm((f) => ({ ...f, secondary_color: e.target.value }))}
            />
            {fieldError('secondary_color')}
          </label>
          <label>
            Footer text
            <textarea
              value={form.footer_text}
              disabled={!canManage}
              maxLength={2000}
              rows={2}
              onChange={(e) => setForm((f) => ({ ...f, footer_text: e.target.value }))}
            />
            {fieldError('footer_text')}
          </label>
          <label>
            Sender email (email_from)
            <input
              value={form.email_from}
              disabled={!canManage}
              placeholder="hello@yourfirm.example"
              onChange={(e) => setForm((f) => ({ ...f, email_from: e.target.value }))}
            />
            {fieldError('email_from')}
          </label>
          <label>
            Website
            <input
              value={form.website}
              disabled={!canManage}
              placeholder="https://…"
              onChange={(e) => setForm((f) => ({ ...f, website: e.target.value }))}
            />
            {fieldError('website')}
          </label>
          <label>
            Client portal URL
            <input
              value={form.client_portal_url}
              disabled={!canManage}
              placeholder="https://…"
              onChange={(e) => setForm((f) => ({ ...f, client_portal_url: e.target.value }))}
            />
            {fieldError('client_portal_url')}
          </label>
          <label>
            Support email
            <input
              value={form.support_email}
              disabled={!canManage}
              onChange={(e) => setForm((f) => ({ ...f, support_email: e.target.value }))}
            />
            {fieldError('support_email')}
          </label>
          <label>
            Support phone
            <input
              value={form.support_phone}
              disabled={!canManage}
              onChange={(e) => setForm((f) => ({ ...f, support_phone: e.target.value }))}
            />
            {fieldError('support_phone')}
          </label>
          <label>
            Support hours
            <input
              value={form.support_hours}
              disabled={!canManage}
              onChange={(e) => setForm((f) => ({ ...f, support_hours: e.target.value }))}
            />
            {fieldError('support_hours')}
          </label>
        </div>

        <div className="v3-form-options">
          <label className="v3-checkbox">
            <input
              type="checkbox"
              checked={form.white_label_enabled}
              disabled={!canManage}
              onChange={(e) => setForm((f) => ({ ...f, white_label_enabled: e.target.checked }))}
            />
            White-label mode — CarbonTally is invisible on supported surfaces
          </label>
          <label className="v3-checkbox">
            <input
              type="checkbox"
              checked={form.co_branding_enabled}
              disabled={!canManage}
              onChange={(e) => setForm((f) => ({ ...f, co_branding_enabled: e.target.checked }))}
            />
            Co-branding — show CarbonTally alongside your brand
          </label>
          {form.white_label_enabled && form.co_branding_enabled && (
            <p className="v3-muted">White-label takes precedence when both are enabled.</p>
          )}
        </div>

        {canManage && (
          <button className="v3-btn v3-btn-primary" disabled={saving} onClick={onSave}>
            {saving ? 'Saving…' : 'Save branding'}
          </button>
        )}
      </div>
    </div>
  );
}

export default function ConsultantPage() {
  const [profile, setProfile] = useState(null);
  const [clients, setClients] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [activeClientId, setActiveClientId] = useState(
    () => localStorage.getItem('v3_consultant_active_client') || ''
  );
  const [view, setView] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [brandContext, setBrandContext] = useState(null);
  const [canManageClients, setCanManageClients] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [prof, clientList, dash] = await Promise.all([
        getConsultantProfile(),
        listConsultantClients(),
        getConsultantDashboard(),
      ]);
      setProfile(prof);
      setCanManageClients(!!prof?.can_manage_clients);
      setClients(clientList.clients || []);
      setDashboard(dash);
      if (!activeClientId && clientList.clients?.length) {
        const first = clientList.clients[0];
        setActiveClientId(first.id);
        localStorage.setItem('v3_consultant_active_client', first.id);
      }
    } catch (e) {
      setError(e.message || 'Failed to load consultant workspace');
    } finally {
      setLoading(false);
    }
  }, [activeClientId]);

  useEffect(() => { load(); }, [load, retryCount]);

  // D21.9: resolve the firm's presentation brand for the shell header without
  // ever blocking the workspace — a branding lookup failure is non-fatal and
  // falls back to the CarbonTally presentation.
  useEffect(() => {
    let cancelled = false;
    getConsultantBrandingContext()
      .then((res) => {
        if (!cancelled && res?.brand_context) setBrandContext(res.brand_context);
      })
      .catch(() => {
        /* non-fatal — CarbonTally fallback */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const activeClient = clients.find((c) => c.id === activeClientId) || null;

  const onSwitchClient = (clientId) => {
    setActiveClientId(clientId);
    localStorage.setItem('v3_consultant_active_client', clientId);
    setView('workspace');
  };

  // D25 — client lifecycle (D15 intact): the backend PUT /clients/{id} enforces
  // can_manage_clients + status vocabulary; this UI only invokes it.
  const onToggleClientStatus = async (client, nextStatus) => {
    if (nextStatus === 'inactive'
      && !window.confirm(`Deactivate client “${client.client_name}”? Access to their data ends immediately.`)) {
      return;
    }
    setError('');
    setNotice('');
    try {
      await updateConsultantClientStatus(client.id, nextStatus);
      setNotice(`Client “${client.client_name}” is now ${nextStatus}.`);
      const refreshed = await listConsultantClients();
      setClients(refreshed.clients || []);
      if (activeClientId === client.id && nextStatus === 'inactive') {
        setActiveClientId('');
        localStorage.removeItem('v3_consultant_active_client');
      }
    } catch (e) {
      setError(e.message || 'Failed to update client status');
    }
  };

  // D27 / D19 §4 — explicit lifecycle transitions (ACTIVE / SUSPENDED / ENDED).
  // SUSPEND and END immediately revoke access at the API and RLS layers.
  const onLifecycleAction = async (client, action) => {
    const labels = {
      suspend: 'suspend',
      end: 'end',
      reactivate: 'reactivate',
    };
    if (action === 'end'
      && !window.confirm(
        `End the relationship with “${client.client_name}”? `
        + 'Consultant access to their data ends immediately. '
        + 'Historical audit/provenance remains; a new relationship requires a new explicit grant.'
      )) {
      return;
    }
    if (action === 'suspend'
      && !window.confirm(`Suspend access to “${client.client_name}”? Their data stays intact but is temporarily inaccessible.`)) {
      return;
    }
    setError('');
    setNotice('');
    try {
      if (action === 'suspend') await suspendConsultantClient(client.id);
      if (action === 'end') await endConsultantClient(client.id);
      if (action === 'reactivate') await reactivateConsultantClient(client.id);
      setNotice(`Client “${client.client_name}” ${labels[action]}d.`);
      const refreshed = await listConsultantClients();
      setClients(refreshed.clients || []);
    } catch (e) {
      setError(e.message || 'Failed to update client lifecycle');
    }
  };

  if (loading) {
    return <div className="v3-consultant-page"><LoadingBlock label="Loading consultant workspace…" /></div>;
  }

  if (error) {
    return (
      <div className="v3-consultant-page">
        <ErrorState
          message={error}
          onRetry={() => setRetryCount((n) => n + 1)}
          title="Consultant workspace unavailable"
        />
        <p className="v3-muted" style={{ marginTop: 12 }}>
          Consultant access requires an active consultant firm profile and membership.
        </p>
      </div>
    );
  }

  return (
    <div className="v3-consultant-page">
      <div className="v3-consultant-header">
        <div>
          <h1>
            {brandContext === null
              ? 'CarbonTally'
              : brandContext && brandContext.kind !== 'carbon_tally'
                ? brandContext.display_name
                : 'Consultant workspace'}
          </h1>
          <p className="subtitle">{profile?.company_name} · multi-client portal</p>
        </div>
        {brandContext && brandContext.kind !== 'carbon_tally' && brandContext.logo_url && (
          <img
            className="v3-brand-logo v3-brand-logo-header"
            src={brandContext.logo_url}
            alt={`${brandContext.display_name} logo`}
          />
        )}
      </div>

      <div className="v3-active-client">
        <div>
          <div className="label">Current organization</div>
          <div className="name">{activeClient ? activeClient.client_name : 'No client selected'}</div>
          {activeClient && (
            <div className="org-id" title={activeClient.organization_id}>{activeClient.client_industry || 'Client'}</div>
          )}
        </div>
        <div className="v3-client-switcher">
          <select
            value={activeClientId}
            onChange={(e) => onSwitchClient(e.target.value)}
            aria-label="Switch active client"
          >
            {clients.map((client) => (
              <option key={client.id} value={client.id}>{client.client_name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="v3-consultant-tabs">
        <button className={`v3-tab ${view === 'dashboard' ? 'active' : ''}`} onClick={() => setView('dashboard')}>
          Consultant dashboard
        </button>
        <button className={`v3-tab ${view === 'workspace' ? 'active' : ''}`} onClick={() => setView('workspace')} disabled={!activeClient}>
          Client workspace
        </button>
        <button className={`v3-tab ${view === 'branding' ? 'active' : ''}`} onClick={() => setView('branding')}>
          Firm branding
        </button>
        <button className={`v3-tab ${view === 'whitelabel' ? 'active' : ''}`} onClick={() => setView('whitelabel')}>
          White-label
        </button>
        <button className={`v3-tab ${view === 'messaging' ? 'active' : ''}`} onClick={() => setView('messaging')} disabled={!activeClient}>
          Client messages
        </button>
      </div>

      {view === 'branding' ? (
        <BrandingView />
      ) : view === 'whitelabel' ? (
        <WhiteLabelTab />
      ) : view === 'messaging' ? (
        <ClientMessagingTab client={activeClient} />
      ) : view === 'dashboard' || !activeClient ? (
        <DashboardView dashboard={dashboard} />
      ) : (
        <ClientWorkspace client={activeClient} clientId={activeClient.id} />
      )}

      {clients.length > 0 && (
        <div className="v3-admin-card">
          <h2>Clients</h2>
          {notice && <div className="v3-note" style={{ marginBottom: 10 }}>{notice}</div>}
          {clients.map((client) => (
            <div
              key={client.id}
              className={`v3-client-list-item ${client.id === activeClientId ? 'active' : ''}`}
              onClick={() => onSwitchClient(client.id)}
            >
              <div>
                <div className="primary">{client.client_name}</div>
                <div className="secondary" title={client.organization_id}>{client.client_industry || 'Client'} · {client.status || 'active'}</div>
              </div>
              <span className={`v3-badge ${client.status === 'active' ? 'active' : 'inactive'}`}>
                {(client.status || 'active').toUpperCase()}
              </span>
              {canManageClients && (
                <span style={{ display: 'inline-flex', gap: 6, flexWrap: 'wrap' }}>
                  {client.status === 'active' && (
                    <>
                      <button className="v3-btn v3-btn-sm" onClick={(e) => { e.stopPropagation(); onLifecycleAction(client, 'suspend'); }}>
                        Suspend
                      </button>
                      <button className="v3-btn v3-btn-sm" onClick={(e) => { e.stopPropagation(); onLifecycleAction(client, 'end'); }}>
                        End
                      </button>
                    </>
                  )}
                  {client.status === 'suspended' && (
                    <>
                      <button className="v3-btn v3-btn-sm" onClick={(e) => { e.stopPropagation(); onLifecycleAction(client, 'reactivate'); }}>
                        Reactivate
                      </button>
                      <button className="v3-btn v3-btn-sm" onClick={(e) => { e.stopPropagation(); onLifecycleAction(client, 'end'); }}>
                        End
                      </button>
                    </>
                  )}
                  {client.status === 'ended' && (
                    <button className="v3-btn v3-btn-sm" onClick={(e) => { e.stopPropagation(); onLifecycleAction(client, 'reactivate'); }}>
                      Reactivate
                    </button>
                  )}
                  {client.status === 'active' && (
                    <button className="v3-btn v3-btn-sm" onClick={(e) => { e.stopPropagation(); onToggleClientStatus(client, 'inactive'); }}>
                      Deactivate
                    </button>
                  )}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

