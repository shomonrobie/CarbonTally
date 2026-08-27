// frontend/src/v3/customer/BillingPage.jsx
// D37 — customer billing visibility + Assisted/Managed order requests.
// Reads/writes the org-scoped /api/v3/billing/* surface only; the browser is
// never authoritative for commercial state (the backend enforces everything).
import React, { useCallback, useEffect, useState } from 'react';
import {
  getMyBilling,
  getMyCreditHistory,
  listMyOrders,
  listMyPayments,
  refreshMyStorage,
  createAssistedEstimate,
  approveBillingOrder,
  cancelBillingOrder,
  createManagedOrder,
} from '../api';
import { ErrorState } from '../components/StateViews';

const fmtBytes = (bytes) => {
  const gb = (bytes || 0) / 1073741824;
  if (gb >= 1) return `${gb.toFixed(2)} GB`;
  const mb = (bytes || 0) / 1048576;
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${bytes || 0} B`;
};

export default function BillingPage() {
  const [entitlement, setEntitlement] = useState(null);
  const [credits, setCredits] = useState(null);
  const [orders, setOrders] = useState(null);
  const [payments, setPayments] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState('');
  const [assisted, setAssisted] = useState({ title: '', description: '', lines: [{ complexity: 'simple', quantity: 1 }], idempotency_key: '' });
  const [managed, setManaged] = useState({ title: '', description: '', quantity_documents: 1, idempotency_key: '' });

  const load = useCallback(async () => {
    try {
      const [ent, cr, ord, pay] = await Promise.all([
        getMyBilling(), getMyCreditHistory(), listMyOrders(), listMyPayments(),
      ]);
      setEntitlement(ent);
      setCredits(cr);
      setOrders(ord.orders || []);
      setPayments(pay.records || []);
    } catch (e) {
      setError(e.message || 'Failed to load billing');
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (!entitlement) {
    return error ? <ErrorState inline message={error} onRetry={load} /> : <div className="v3-loading"><div className="spinner" />Loading billing…</div>;
  }

  const plan = entitlement.plan || {};
  const sub = entitlement.subscription || {};

  const onRefreshStorage = async () => {
    setBusy('storage');
    setError('');
    try {
      await refreshMyStorage();
      setNotice('Storage usage re-measured.');
      await load();
    } catch (e) { setError(e.message); } finally { setBusy(''); }
  };

  const onAssistedEstimate = async () => {
    setBusy('assisted');
    setError(''); setNotice('');
    try {
      const key = assisted.idempotency_key || `est-${Date.now()}`;
      await createAssistedEstimate({ ...assisted, idempotency_key: key, lines: assisted.lines.filter((l) => l.quantity > 0) });
      setNotice('Estimate created — review and approve below.');
      setAssisted({ title: '', description: '', lines: [{ complexity: 'simple', quantity: 1 }], idempotency_key: '' });
      await load();
    } catch (e) { setError(e.message || 'Failed to create estimate'); } finally { setBusy(''); }
  };

  const onApprove = async (orderId) => {
    setBusy(orderId);
    setError(''); setNotice('');
    try {
      await approveBillingOrder(orderId, `appr-${orderId}-${Date.now()}`);
      setNotice('Order approved — CarbonTally will begin the work.');
      await load();
    } catch (e) { setError(e.message || 'Failed to approve order'); } finally { setBusy(''); }
  };

  const onCancel = async (orderId) => {
    setBusy(orderId);
    setError(''); setNotice('');
    try {
      await cancelBillingOrder(orderId);
      setNotice('Order cancelled.');
      await load();
    } catch (e) { setError(e.message || 'Failed to cancel order'); } finally { setBusy(''); }
  };

  const onManagedSubmit = async () => {
    setBusy('managed');
    setError(''); setNotice('');
    try {
      await createManagedOrder({ ...managed, idempotency_key: managed.idempotency_key || `mng-${Date.now()}` });
      setNotice('Managed Processing request submitted — CarbonTally will quote and confirm.');
      setManaged({ title: '', description: '', quantity_documents: 1, idempotency_key: '' });
      await load();
    } catch (e) { setError(e.message || 'Failed to submit managed request'); } finally { setBusy(''); }
  };

  return (
    <div className="v3-page">
      <div className="v3-page-header">
        <h1>Billing</h1>
        <p className="subtitle">Your commercial plan, credits, storage and orders.</p>
      </div>
      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note" style={{ marginBottom: 14 }}>{notice}</div>}

      <div className="v3-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginBottom: 18 }}>
        <div className="v3-admin-card">
          <h3>Plan</h3>
          <p>{plan.name || 'No active subscription'}</p>
          <p className="muted">v{plan.version || '—'} · {sub.lifecycle_status || '—'}</p>
          {plan.price ? <p>{plan.price} {plan.currency} / {plan.billing_interval}</p> : null}
        </div>
        <div className="v3-admin-card">
          <h3>Billing mode</h3>
          <p>{entitlement.billing_mode}</p>
          <p className="muted">Customer-specific (never silently changed)</p>
        </div>
        <div className="v3-admin-card">
          <h3>Credits</h3>
          <p><strong>{entitlement.credits.balance}</strong> available</p>
          <p className="muted">{entitlement.credits.included_monthly} included monthly</p>
        </div>
        <div className="v3-admin-card">
          <h3>Storage</h3>
          <p>{fmtBytes(entitlement.storage.usage_bytes)} used</p>
          <p className="muted">{fmtBytes(entitlement.storage.included_bytes)} included</p>
          <button className="v3-btn" onClick={onRefreshStorage} disabled={busy === 'storage'}>
            {busy === 'storage' ? 'Measuring…' : 'Re-measure'}
          </button>
        </div>
        {entitlement.billing_mode === 'STANDARD' && (
          <div className="v3-admin-card">
            <h3>STANDARD allowance</h3>
            <p>{entitlement.standard.usage_this_period} / {entitlement.standard.monthly_allowance} used</p>
            <p className="muted">{entitlement.standard.remaining} remaining this period</p>
          </div>
        )}
      </div>

      <div className="v3-admin-card" style={{ marginBottom: 18 }}>
        <h3>Credit history</h3>
        <table className="v3-table">
          <thead><tr><th>When</th><th>Type</th><th>Delta</th><th>Source</th><th>Reason</th></tr></thead>
          <tbody>
            {(credits?.entries || []).slice(0, 20).map((e) => (
              <tr key={e.id}>
                <td>{e.created_at ? new Date(e.created_at).toLocaleString() : '—'}</td>
                <td>{e.entry_type}</td>
                <td>{e.credit_delta > 0 ? `+${e.credit_delta}` : e.credit_delta}</td>
                <td>{e.source}</td>
                <td>{e.reason || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!(credits?.entries || []).length && <p className="muted">No credit activity yet.</p>}
      </div>

      <div className="v3-admin-card" style={{ marginBottom: 18 }}>
        <h3>Assisted Processing estimate</h3>
        <p className="muted">Request human-assisted processing — you review and approve the estimate before any chargeable work begins.</p>
        <div className="v3-form-grid">
          <div className="v3-form-group"><label>Title</label>
            <input value={assisted.title} onChange={(e) => setAssisted({ ...assisted, title: e.target.value })} /></div>
          <div className="v3-form-group"><label>Description</label>
            <input value={assisted.description} onChange={(e) => setAssisted({ ...assisted, description: e.target.value })} /></div>
          {assisted.lines.map((line, i) => (
            <div key={i} className="v3-form-group">
              <label>Line {i + 1}</label>
              <div style={{ display: 'flex', gap: 6 }}>
                <select value={line.complexity}
                  onChange={(e) => setAssisted({ ...assisted, lines: assisted.lines.map((l, j) => j === i ? { ...l, complexity: e.target.value } : l) })}>
                  <option value="simple">Simple</option><option value="standard">Standard</option>
                  <option value="complex">Complex</option><option value="exceptional">Exceptional</option>
                </select>
                <input type="number" min="1" value={line.quantity}
                  onChange={(e) => setAssisted({ ...assisted, lines: assisted.lines.map((l, j) => j === i ? { ...l, quantity: Number(e.target.value) } : l) })} />
                <button className="v3-btn" onClick={() => setAssisted({ ...assisted, lines: assisted.lines.filter((_, j) => j !== i) })}>−</button>
              </div>
            </div>
          ))}
          <button className="v3-btn" onClick={() => setAssisted({ ...assisted, lines: [...assisted.lines, { complexity: 'simple', quantity: 1 }] })}>+ line</button>
        </div>
        <button className="v3-btn primary" style={{ marginTop: 10 }} onClick={onAssistedEstimate} disabled={busy === 'assisted'}>
          {busy === 'assisted' ? 'Creating…' : 'Create estimate'}
        </button>
      </div>

      <div className="v3-admin-card" style={{ marginBottom: 18 }}>
        <h3>Managed Processing</h3>
        <p className="muted">Drop the scope — CarbonTally manages the whole workflow.</p>
        <div className="v3-form-grid">
          <div className="v3-form-group"><label>Title</label>
            <input value={managed.title} onChange={(e) => setManaged({ ...managed, title: e.target.value })} /></div>
          <div className="v3-form-group"><label>Scope / description</label>
            <input value={managed.description} onChange={(e) => setManaged({ ...managed, description: e.target.value })} /></div>
          <div className="v3-form-group"><label>Document count</label>
            <input type="number" min="1" value={managed.quantity_documents}
              onChange={(e) => setManaged({ ...managed, quantity_documents: Number(e.target.value) })} /></div>
        </div>
        <button className="v3-btn primary" style={{ marginTop: 10 }} onClick={onManagedSubmit} disabled={busy === 'managed'}>
          {busy === 'managed' ? 'Submitting…' : 'Submit managed request'}
        </button>
      </div>

      <div className="v3-admin-card" style={{ marginBottom: 18 }}>
        <h3>Orders</h3>
        <table className="v3-table">
          <thead><tr><th>Created</th><th>Type</th><th>Status</th><th>Total</th><th>Title</th><th /></tr></thead>
          <tbody>
            {(orders || []).map((o) => (
              <tr key={o.id}>
                <td>{o.created_at ? new Date(o.created_at).toLocaleString() : '—'}</td>
                <td>{o.order_type}</td>
                <td>{o.status}</td>
                <td>{o.total_amount} {o.currency}</td>
                <td>{o.title}</td>
                <td>
                  {o.status === 'awaiting_customer_approval' && (
                    <button className="v3-btn primary" onClick={() => onApprove(o.id)} disabled={busy === o.id}>Approve</button>
                  )}
                  {['estimated', 'awaiting_customer_approval', 'approved'].includes(o.status) && (
                    <button className="v3-btn" onClick={() => onCancel(o.id)} disabled={busy === o.id}>Cancel</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!(orders || []).length && <p className="muted">No orders yet.</p>}
      </div>

      {(payments || []).length > 0 && (
        <div className="v3-admin-card">
          <h3>Payments</h3>
          <p className="muted">Provider-neutral records — no payment details stored.</p>
          <table className="v3-table">
            <thead><tr><th>Recorded</th><th>Status</th><th>Amount</th><th>Provider</th></tr></thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id}>
                  <td>{p.recorded_at ? new Date(p.recorded_at).toLocaleString() : '—'}</td>
                  <td>{p.status}</td>
                  <td>{p.amount} {p.currency}</td>
                  <td>{p.provider}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
