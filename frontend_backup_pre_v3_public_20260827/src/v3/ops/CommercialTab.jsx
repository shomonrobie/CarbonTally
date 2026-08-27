// frontend/src/v3/ops/CommercialTab.jsx
// D37-0 — Commercial (billing) configuration for CarbonTally platform admins.
// Reads/writes the trusted /api/v3/commercial/* surface. Every change publishes
// a NEW version (history is never rewritten). The browser is NEVER authoritative
// for billing state — the backend enforces staff + can_manage_billing + audit.
import React, { useEffect, useState } from 'react';
import {
  getCommercialOverview,
  getCommercialPlan,
  updateCommercialConfig,
  updateCommercialPlan,
  createCommercialPlan,
  getCreditLedger,
  listCommercialOrganizations,
  listSubscriptions,
  activateSubscription,
  changeSubscriptionStatus,
  listAdminOrders,
  completeAdminOrder,
  listAdminStorage,
  adminGrantCredits,
  adminAdjustCredits,
  adminReverseCredits,
  adminRefundCredits,
  adminRolloverCredits,
} from '../api';

const CONFIG_LABELS = {
  default_billing_mode: 'Default billing mode (new customers)',
  credit_rules: 'Automated credit rules',
  structured_data_bands: 'Structured data processing bands',
  storage: 'Storage allowance & rate',
  assisted_pricing: 'Assisted Processing price book',
  credit_policy: 'Credit policy (rollover / emergency)',
  standard_allowance: 'STANDARD mode allowance',
};

const prettyJson = (value) => JSON.stringify(value, null, 2);

export default function CommercialTab({ canManage = false }) {
  const [overview, setOverview] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const [modeDraft, setModeDraft] = useState('CREDIT');
  const [configDrafts, setConfigDrafts] = useState({});
  const [configReasons, setConfigReasons] = useState({});
  const [saving, setSaving] = useState('');

  const [newPlan, setNewPlan] = useState(null);
  const [planEdits, setPlanEdits] = useState({});

  const [orgs, setOrgs] = useState([]);
  const [orgFilter, setOrgFilter] = useState('');
  const [ledgerOrg, setLedgerOrg] = useState('');
  const [ledger, setLedger] = useState(null);

  // D37 admin billing state.
  const [subscriptions, setSubscriptions] = useState(null);
  const [adminOrders, setAdminOrders] = useState(null);
  const [adminStorage, setAdminStorage] = useState(null);
  const [activateForm, setActivateForm] = useState({ organization_id: '', plan_code: 'starter', billing_mode: '', lifecycle_status: 'active', idempotency_key: '' });
  const [creditOps, setCreditOps] = useState({ organization_id: '', amount: '', delta: '', reason: '', original_external_reference: '', idempotency_key: '' });

  const load = async () => {
    try {
      const data = await getCommercialOverview();
      setOverview(data);
      setModeDraft(data.default_billing_mode || 'CREDIT');
      const drafts = {};
      Object.values(data.config || {}).forEach((c) => {
        drafts[c.config_key] = prettyJson(c.config_value);
      });
      setConfigDrafts(drafts);
    } catch (e) {
      setError(e.message || 'Failed to load commercial configuration');
    }
  };

  const loadOrgs = async () => {
    try {
      const data = await listCommercialOrganizations(orgFilter || undefined);
      setOrgs(data.organizations || []);
    } catch (_e) {
      /* org list is secondary — do not block the tab */
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);
  useEffect(() => { loadOrgs(); /* eslint-disable-next-line */ }, [orgFilter]);

  const loadAdmin = async () => {
    try {
      const [subs, ords, storage] = await Promise.all([
        listSubscriptions(), listAdminOrders(), listAdminStorage(),
      ]);
      setSubscriptions(subs.subscriptions || []);
      setAdminOrders(ords.orders || []);
      setAdminStorage(storage.organizations || []);
    } catch (_e) { /* secondary panel */ }
  };
  useEffect(() => { if (canManage) loadAdmin(); /* eslint-disable-next-line */ }, []);

  if (!overview) {
    return error ? <div className="v3-ops-error">{error}</div> : <div className="v3-loading"><div className="spinner" />Loading commercial configuration…</div>;
  }

  const canEdit = canManage;

  const onSaveMode = async () => {
    setSaving('mode');
    setError('');
    setNotice('');
    try {
      await updateCommercialConfig('default_billing_mode', { mode: modeDraft }, 'Default billing mode change (D37-0)');
      setNotice('Default billing mode updated. Applies to NEW customers only — existing customers keep their mode.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to update default billing mode');
    } finally {
      setSaving('');
    }
  };

  const onSaveConfig = async (key) => {
    let parsed;
    try {
      parsed = JSON.parse(configDrafts[key] || '{}');
    } catch (_e) {
      setError(`"${key}" is not valid JSON — nothing was changed.`);
      return;
    }
    setSaving(key);
    setError('');
    setNotice('');
    try {
      await updateCommercialConfig(key, parsed, configReasons[key] || `${key} update (D37-0)`);
      setNotice(`"${key}" v${(overview.config[key]?.version || 0) + 1} published — previous version preserved.`);
      setConfigReasons((r) => ({ ...r, [key]: '' }));
      await load();
    } catch (e) {
      setError(e.message || `Failed to update "${key}"`);
    } finally {
      setSaving('');
    }
  };

  const onOpenPlan = async (planCode) => {
    setSaving(`plan-${planCode}`);
    setError('');
    try {
      const data = await getCommercialPlan(planCode);
      setPlanEdits((edits) => ({
        ...edits,
        [planCode]: {
          name: data.current.name,
          price: String(data.current.price),
          included_credits: String(data.current.included_credits),
          reason: '',
          history: (data.history || []).length,
        },
      }));
    } catch (e) {
      setError(e.message || 'Failed to load plan');
    } finally {
      setSaving('');
    }
  };

  const onPublishPlanVersion = async (planCode) => {
    const edit = planEdits[planCode] || {};
    const fields = {};
    if (edit.name !== undefined && edit.name.trim()) fields.name = edit.name.trim();
    if (edit.price !== undefined && edit.price !== '') fields.price = Number(edit.price);
    if (edit.included_credits !== undefined && edit.included_credits !== '') {
      fields.included_credits = Number(edit.included_credits);
    }
    if (!Object.keys(fields).length) {
      setError('No plan changes supplied.');
      return;
    }
    setSaving(`publish-${planCode}`);
    setError('');
    setNotice('');
    try {
      await updateCommercialPlan(planCode, { ...fields, reason: edit.reason || 'Plan version update (D37-0)' });
      setNotice(`Plan "${planCode}" v${(overview.plans.find((p) => p.plan_code === planCode)?.version || 0) + 1} published — existing commercial records keep the old terms.`);
      await load();
    } catch (e) {
      setError(e.message || 'Failed to publish plan version');
    } finally {
      setSaving('');
    }
  };

  const onCreatePlan = async () => {
    const plan = newPlan;
    if (!plan || !plan.plan_code || !plan.name) {
      setError('A plan code and name are required.');
      return;
    }
    setSaving('create-plan');
    setError('');
    setNotice('');
    try {
      await createCommercialPlan({
        plan_code: plan.plan_code,
        name: plan.name,
        description: plan.description || null,
        price: Number(plan.price || 0),
        currency: plan.currency || 'GBP',
        billing_interval: plan.billing_interval || 'month',
        included_credits: Number(plan.included_credits || 0),
        included_storage_bytes: Number(plan.included_storage_gb || 0) * 1073741824,
        team_member_limit: plan.team_member_limit ? Number(plan.team_member_limit) : null,
        billing_mode: plan.billing_mode || null,
        assisted_processing_available: !!plan.assisted_processing_available,
        managed_processing_available: !!plan.managed_processing_available,
        api_access: !!plan.api_access,
        is_active: plan.is_active !== false,
      });
      setNotice(`Plan "${plan.plan_code}" v1 created.`);
      setNewPlan(null);
      await load();
    } catch (e) {
      setError(e.message || 'Failed to create plan');
    } finally {
      setSaving('');
    }
  };

  const onLoadLedger = async () => {
    if (!ledgerOrg) return;
    setSaving('ledger');
    setError('');
    try {
      setLedger(await getCreditLedger(ledgerOrg));
    } catch (e) {
      setError(e.message || 'Failed to load credit ledger');
    } finally {
      setSaving('');
    }
  };

  const config = overview.config || {};

  return (
    <div>
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      {/* ---- Default billing mode --------------------------------------------- */}
      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Default billing mode — new customers</h3>
        <p className="muted" style={{ marginTop: 4 }}>
          Every new organisation is assigned this mode at creation (versioned).
          Changing it here NEVER silently changes existing customers.
        </p>
        <div className="workspace-grid">
          <div className="workspace-field">
            <label>Mode</label>
            <select
              value={modeDraft}
              disabled={!canEdit}
              onChange={(e) => setModeDraft(e.target.value)}
            >
              {(overview.billing_modes || ['CREDIT', 'STANDARD']).map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          {canEdit && (
            <div className="workspace-actions">
              <button className="v3-btn primary" onClick={onSaveMode} disabled={saving === 'mode'}>
                {saving === 'mode' ? 'Saving…' : `Publish v${(config.default_billing_mode?.version || 0) + 1}`}
              </button>
            </div>
          )}
        </div>
        <p className="muted" style={{ marginTop: 8 }}>
          Current version {config.default_billing_mode?.version || '—'} · effective{' '}
          {config.default_billing_mode?.effective_from ? new Date(config.default_billing_mode.effective_from).toLocaleString() : 'now'}
        </p>
      </div>

      {/* ---- Versioned commercial rules ---------------------------------------- */}
      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Commercial rules (versioned)</h3>
        <p className="muted" style={{ marginTop: 4 }}>
          Each rule publishes a NEW version. Historical versions are never rewritten.
        </p>
        {Object.entries(CONFIG_LABELS).map(([key, label]) => {
          const current = config[key];
          if (!current) return null;
          return (
            <div key={key} style={{ marginBottom: 14 }}>
              <strong>{label}</strong> <span className="muted">· v{current.version}</span>
              {current.effective_from ? (
                <span className="muted"> · since {new Date(current.effective_from).toLocaleDateString()}</span>
              ) : null}
              <textarea
                className="commercial-json"
                rows={Math.min(10, 4 + (configDrafts[key] || '').split('\n').length)}
                value={configDrafts[key] || ''}
                disabled={!canEdit}
                onChange={(e) => setConfigDrafts((d) => ({ ...d, [key]: e.target.value }))}
              />
              {canEdit && (
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 4 }}>
                  <input
                    className="commercial-reason"
                    placeholder="Reason for this change (audited)"
                    value={configReasons[key] || ''}
                    onChange={(e) => setConfigReasons((r) => ({ ...r, [key]: e.target.value }))}
                  />
                  <button
                    className="v3-btn primary"
                    onClick={() => onSaveConfig(key)}
                    disabled={saving === key}
                  >
                    {saving === key ? 'Publishing…' : `Publish v${(current.version || 0) + 1}`}
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>


      {/* ---- Plans -------------------------------------------------------------- */}
      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Plans (versioned catalogue)</h3>
        <p className="muted" style={{ marginTop: 4 }}>
          Starter / Professional / Business / Enterprise — prices are provisional and
          configurable. Publishing a new version keeps historical terms intact.
        </p>
        <table className="v3-table">
          <thead>
            <tr>
              <th>Code</th><th>Name</th><th>Version</th><th>Price</th><th>Credits</th>
              <th>Storage</th><th>Mode</th><th>Assisted</th><th>Managed</th><th>API</th><th>Status</th><th />
            </tr>
          </thead>
          <tbody>
            {(overview.plans || []).map((plan) => {
              const edit = planEdits[plan.plan_code];
              return (
                <tr key={`${plan.plan_code}-v${plan.version}`}>
                  <td>{plan.plan_code}</td>
                  <td>{edit ? <input value={edit.name || ''} onChange={(e) => setPlanEdits((x) => ({ ...x, [plan.plan_code]: { ...x[plan.plan_code], name: e.target.value } }))} /> : plan.name}</td>
                  <td>{plan.version}</td>
                  <td>
                    {edit
                      ? <input type="number" value={edit.price} onChange={(e) => setPlanEdits((x) => ({ ...x, [plan.plan_code]: { ...x[plan.plan_code], price: e.target.value } }))} />
                      : `${plan.price} ${plan.currency}`}
                  </td>
                  <td>
                    {edit
                      ? <input type="number" value={edit.included_credits} onChange={(e) => setPlanEdits((x) => ({ ...x, [plan.plan_code]: { ...x[plan.plan_code], included_credits: e.target.value } }))} />
                      : plan.included_credits}
                  </td>
                  <td>{plan.included_storage_bytes ? `${(plan.included_storage_bytes / 1073741824).toFixed(1)} GB` : '—'}</td>
                  <td>{plan.billing_mode || 'both'}</td>
                  <td>{plan.assisted_processing_available ? 'yes' : 'no'}</td>
                  <td>{plan.managed_processing_available ? 'yes' : 'no'}</td>
                  <td>{plan.api_access ? 'yes' : 'no'}</td>
                  <td>{plan.is_active ? 'active' : 'inactive'}</td>
                  <td>
                    {!edit ? (
                      <button className="v3-btn" onClick={() => onOpenPlan(plan.plan_code)} disabled={saving === `plan-${plan.plan_code}`}>
                        {saving === `plan-${plan.plan_code}` ? '…' : 'Edit / version'}
                      </button>
                    ) : (
                      <div style={{ display: 'flex', gap: 6 }}>
                        <input className="commercial-reason" placeholder="Reason (audited)" value={edit.reason || ''} onChange={(e) => setPlanEdits((x) => ({ ...x, [plan.plan_code]: { ...x[plan.plan_code], reason: e.target.value } }))} />
                        <button className="v3-btn primary" onClick={() => onPublishPlanVersion(plan.plan_code)} disabled={saving === `publish-${plan.plan_code}`}>
                          {saving === `publish-${plan.plan_code}` ? '…' : `Publish v${(plan.version || 0) + 1}`}
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {canEdit && (
          <div style={{ marginTop: 12 }}>
            <h4>New plan</h4>
            {!newPlan ? (
              <button className="v3-btn" onClick={() => setNewPlan({})}>Create plan</button>
            ) : (
              <div className="workspace-grid">
                <div className="workspace-field">
                  <label>Plan code</label>
                  <input value={newPlan.plan_code || ''} onChange={(e) => setNewPlan({ ...newPlan, plan_code: e.target.value })} />
                </div>
                <div className="workspace-field">
                  <label>Name</label>
                  <input value={newPlan.name || ''} onChange={(e) => setNewPlan({ ...newPlan, name: e.target.value })} />
                </div>
                <div className="workspace-field">
                  <label>Price</label>
                  <input type="number" value={newPlan.price || 0} onChange={(e) => setNewPlan({ ...newPlan, price: e.target.value })} />
                </div>
                <div className="workspace-field">
                  <label>Included credits</label>
                  <input type="number" value={newPlan.included_credits || 0} onChange={(e) => setNewPlan({ ...newPlan, included_credits: e.target.value })} />
                </div>
                <div className="workspace-field">
                  <label>Storage (GB)</label>
                  <input type="number" value={newPlan.included_storage_gb || 0} onChange={(e) => setNewPlan({ ...newPlan, included_storage_gb: e.target.value })} />
                </div>
                <div className="workspace-field">
                  <label>Billing mode</label>
                  <select value={newPlan.billing_mode || ''} onChange={(e) => setNewPlan({ ...newPlan, billing_mode: e.target.value || null })}>
                    <option value="">Both</option>
                    <option value="CREDIT">CREDIT</option>
                    <option value="STANDARD">STANDARD</option>
                  </select>
                </div>
                <div className="workspace-actions">
                  <button className="v3-btn primary" onClick={onCreatePlan} disabled={saving === 'create-plan'}>
                    {saving === 'create-plan' ? 'Creating…' : 'Create plan (v1)'}
                  </button>
                  <button className="v3-btn" onClick={() => setNewPlan(null)}>Cancel</button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>


      {/* ---- Customer billing modes + credit ledger ------------------------------ */}
      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Customers — billing mode & credit ledger</h3>
        <p className="muted" style={{ marginTop: 4 }}>
          Read-only overview. Billing state is authoritative server-side; this surface
          never mutates it.
        </p>
        <div className="workspace-grid">
          <div className="workspace-field">
            <label>Filter by billing mode</label>
            <select value={orgFilter} onChange={(e) => setOrgFilter(e.target.value)}>
              <option value="">All</option>
              <option value="CREDIT">CREDIT</option>
              <option value="STANDARD">STANDARD</option>
            </select>
          </div>
        </div>
        <table className="v3-table" style={{ marginTop: 8 }}>
          <thead>
            <tr><th>Organisation</th><th>Mode</th><th>Country</th><th>Status</th><th>Ledger</th></tr>
          </thead>
          <tbody>
            {(orgs || []).map((org) => (
              <tr key={org.id}>
                <td>{org.name}</td>
                <td>{org.billing_mode || '—'}</td>
                <td>{org.country || '—'}</td>
                <td>{org.is_active ? 'active' : 'inactive'}</td>
                <td>
                  <button className="v3-btn" onClick={() => { setLedgerOrg(org.id); setLedger(null); }}>
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {ledgerOrg && (
          <div style={{ marginTop: 12 }}>
            <strong>Credit ledger — {ledgerOrg}</strong>{' '}
            <button className="v3-btn" onClick={onLoadLedger} disabled={saving === 'ledger'}>
              {saving === 'ledger' ? 'Loading…' : 'Load'}
            </button>
            {ledger && (
              <div>
                <p><strong>Derived balance:</strong> {ledger.balance} credits</p>
                <table className="v3-table">
                  <thead>
                    <tr><th>When</th><th>Type</th><th>Delta</th><th>Source</th><th>Reason</th><th>Plan</th><th>Ref</th></tr>
                  </thead>
                  <tbody>
                    {(ledger.entries || []).map((entry) => (
                      <tr key={entry.id}>
                        <td>{entry.created_at ? new Date(entry.created_at).toLocaleString() : '—'}</td>
                        <td>{entry.entry_type}</td>
                        <td>{entry.credit_delta > 0 ? `+${entry.credit_delta}` : entry.credit_delta}</td>
                        <td>{entry.source}</td>
                        <td>{entry.reason || '—'}</td>
                        <td>{entry.plan_code ? `${entry.plan_code} v${entry.plan_version}` : '—'}</td>
                        <td>{entry.external_reference || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!(ledger.entries || []).length && <p className="muted">No ledger entries yet.</p>}
              </div>
            )}
          </div>
        )}
      </div>
      {/* ---- D37: subscriptions -------------------------------------------------- */}
      {canManage && (
        <div className="workspace-pane" style={{ marginBottom: 16 }}>
          <h3>Subscriptions (commercial relationships)</h3>
          <table className="v3-table">
            <thead><tr><th>Organisation</th><th>Plan</th><th>Version</th><th>Mode</th><th>Status</th><th>Period end</th><th /></tr></thead>
            <tbody>
              {(subscriptions || []).map((s) => (
                <tr key={s.id}>
                  <td>{s.organization_id}</td>
                  <td>{s.plan_code}</td><td>{s.plan_version}</td><td>{s.billing_mode}</td>
                  <td>{s.lifecycle_status}</td>
                  <td>{s.current_period_end ? new Date(s.current_period_end).toLocaleDateString() : '—'}</td>
                  <td>
                    <select defaultValue="" onChange={(e) => {
                      if (e.target.value) changeSubscriptionStatus(s.id, e.target.value).then(loadAdmin).catch((err) => setError(err.message));
                    }}>
                      <option value="" disabled>change</option>
                      {['active', 'past_due', 'suspended', 'cancelled', 'expired', 'trial', 'pending'].map((st) => (
                        <option key={st} value={st}>{st}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <h4 style={{ marginTop: 10 }}>Activate / renew a subscription</h4>
          <div className="workspace-grid">
            <div className="workspace-field"><label>Organisation id</label>
              <input value={activateForm.organization_id} onChange={(e) => setActivateForm({ ...activateForm, organization_id: e.target.value })} /></div>
            <div className="workspace-field"><label>Plan</label>
              <select value={activateForm.plan_code} onChange={(e) => setActivateForm({ ...activateForm, plan_code: e.target.value })}>
                <option value="starter">Starter</option><option value="professional">Professional</option>
                <option value="business">Business</option><option value="enterprise">Enterprise</option>
              </select></div>
            <div className="workspace-field"><label>Billing mode</label>
              <select value={activateForm.billing_mode} onChange={(e) => setActivateForm({ ...activateForm, billing_mode: e.target.value })}>
                <option value="">Org default</option><option value="CREDIT">CREDIT</option><option value="STANDARD">STANDARD</option>
              </select></div>
            <div className="workspace-actions">
              <button className="v3-btn primary" onClick={() => {
                const key = activateForm.idempotency_key || `sub-${Date.now()}`;
                activateSubscription({ ...activateForm, billing_mode: activateForm.billing_mode || null, idempotency_key: key })
                  .then(() => { setNotice('Subscription activated (history preserved).'); loadAdmin(); })
                  .catch((e) => setError(e.message || 'Failed to activate subscription'));
              }}>Activate (new version)</button>
            </div>
          </div>
        </div>
      )}

      {/* ---- D37: orders ---------------------------------------------------------- */}
      {canManage && (
        <div className="workspace-pane" style={{ marginBottom: 16 }}>
          <h3>Orders</h3>
          <table className="v3-table">
            <thead><tr><th>Created</th><th>Type</th><th>Status</th><th>Total</th><th>Org</th><th>Title</th><th /></tr></thead>
            <tbody>
              {(adminOrders || []).map((o) => (
                <tr key={o.id}>
                  <td>{o.created_at ? new Date(o.created_at).toLocaleString() : '—'}</td>
                  <td>{o.order_type}</td><td>{o.status}</td><td>{o.total_amount} {o.currency}</td>
                  <td>{o.organization_id}</td><td>{o.title}</td>
                  <td>
                    {['approved', 'processing', 'awaiting_qc', 'queued'].includes(o.status) && (
                      <button className="v3-btn" onClick={() =>
                        completeAdminOrder(o.id).then(() => { setNotice('Order completed (immutable).'); loadAdmin(); }).catch((e) => setError(e.message))}>
                        Complete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!(adminOrders || []).length && <p className="muted">No orders.</p>}
        </div>
      )}

      {/* ---- D37: credit operations (admin) ---------------------------------------- */}
      {canManage && (
        <div className="workspace-pane" style={{ marginBottom: 16 }}>
          <h3>Credit operations (authoritative, idempotent, audited)</h3>
          <div className="workspace-grid">
            <div className="workspace-field"><label>Organisation id</label>
              <input value={creditOps.organization_id} onChange={(e) => setCreditOps({ ...creditOps, organization_id: e.target.value })} /></div>
            <div className="workspace-field"><label>Amount</label>
              <input type="number" value={creditOps.amount} onChange={(e) => setCreditOps({ ...creditOps, amount: e.target.value })} /></div>
            <div className="workspace-field"><label>Adjustment delta (±)</label>
              <input type="number" value={creditOps.delta} onChange={(e) => setCreditOps({ ...creditOps, delta: e.target.value })} /></div>
            <div className="workspace-field"><label>Reason</label>
              <input value={creditOps.reason} onChange={(e) => setCreditOps({ ...creditOps, reason: e.target.value })} /></div>
            <div className="workspace-field"><label>Original external reference (reverse)</label>
              <input value={creditOps.original_external_reference} onChange={(e) => setCreditOps({ ...creditOps, original_external_reference: e.target.value })} /></div>
          </div>
          <div className="workspace-actions">
            <button className="v3-btn primary" onClick={() => {
              const key = creditOps.idempotency_key || `op-${Date.now()}`;
              adminGrantCredits({ organization_id: creditOps.organization_id, amount: Number(creditOps.amount), reason: creditOps.reason || 'admin grant', idempotency_key: key })
                .then(() => { setNotice('Credits granted.'); }).catch((e) => setError(e.message));
            }}>Grant</button>
            <button className="v3-btn" onClick={() => {
              adminAdjustCredits({ organization_id: creditOps.organization_id, delta: Number(creditOps.delta), reason: creditOps.reason || 'admin adjustment', idempotency_key: `adj-${Date.now()}` })
                .then(() => { setNotice('Adjustment recorded.'); }).catch((e) => setError(e.message));
            }}>Adjust</button>
            <button className="v3-btn" onClick={() => {
              adminReverseCredits({ organization_id: creditOps.organization_id, original_external_reference: creditOps.original_external_reference, reason: creditOps.reason || 'reversal', idempotency_key: `rev-${Date.now()}` })
                .then(() => { setNotice('Reversal recorded.'); }).catch((e) => setError(e.message));
            }}>Reverse</button>
            <button className="v3-btn" onClick={() => {
              adminRefundCredits({ organization_id: creditOps.organization_id, amount: Number(creditOps.amount), reason: creditOps.reason || 'refund', idempotency_key: `ref-${Date.now()}` })
                .then(() => { setNotice('Refund recorded.'); }).catch((e) => setError(e.message));
            }}>Refund</button>
            <button className="v3-btn" onClick={() => {
              adminRolloverCredits({ organization_id: creditOps.organization_id, eligible_credits: Number(creditOps.amount), idempotency_key: `rol-${Date.now()}` })
                .then(() => { setNotice('Rollover recorded (ledger-visible).'); }).catch((e) => setError(e.message));
            }}>Rollover</button>
          </div>
        </div>
      )}

      {/* ---- D37: storage metering (admin) ----------------------------------------- */}
      {canManage && (
        <div className="workspace-pane" style={{ marginBottom: 16 }}>
          <h3>Storage metering (server-measured)</h3>
          <table className="v3-table">
            <thead><tr><th>Organisation</th><th>Usage</th><th>Included</th><th>Additional</th><th>Measured</th></tr></thead>
            <tbody>
              {(adminStorage || []).map((s) => (
                <tr key={s.organization_id}>
                  <td>{s.organization_id}</td>
                  <td>{(s.usage_bytes / 1073741824).toFixed(2)} GB</td>
                  <td>{(s.included_bytes / 1073741824).toFixed(2)} GB</td>
                  <td>{(s.additional_bytes / 1073741824).toFixed(2)} GB</td>
                  <td>{s.measured_at ? new Date(s.measured_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!(adminStorage || []).length && <p className="muted">No storage snapshots yet.</p>}
        </div>
      )}

    </div>

  );
}

