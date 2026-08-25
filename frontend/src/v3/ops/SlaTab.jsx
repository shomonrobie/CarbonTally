// frontend/src/v3/ops/SlaTab.jsx
// D25 — SLA settings. Reads the real /api/v3/ops/sla/settings (queue_settings)
// and allows staff administrators to update the review SLA default hours only.
// Capacity automation is deliberately NOT part of this surface.
import React, { useEffect, useState } from 'react';
import { getSlaSettings, updateSlaSettings } from '../api';

export default function SlaTab({ canManage }) {
  const [settings, setSettings] = useState(null);
  const [slaHours, setSlaHours] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [saving, setSaving] = useState(false);

  const load = () => {
    getSlaSettings()
      .then((data) => {
        setSettings(data);
        setSlaHours(data.sla_hours != null ? String(data.sla_hours) : '');
      })
      .catch((e) => setError(e.message || 'Failed to load SLA settings'));
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const onSave = async () => {
    const hours = Number(slaHours);
    if (!Number.isInteger(hours) || hours < 1) {
      setError('SLA hours must be a whole number of at least 1.');
      return;
    }
    setSaving(true);
    setError('');
    setNotice('');
    try {
      await updateSlaSettings({ sla_hours: hours });
      setNotice('SLA default updated.');
      load();
    } catch (e) {
      setError(e.message || 'Failed to update SLA settings');
    } finally {
      setSaving(false);
    }
  };

  if (!settings) {
    return error ? <div className="v3-ops-error">{error}</div> : <div className="v3-loading"><div className="spinner" />Loading SLA…</div>;
  }

  return (
    <div>
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      <div className="workspace-pane" style={{ marginBottom: 16 }}>
        <h3>Review SLA defaults</h3>
        <div className="workspace-grid">
          <div className="workspace-field">
            <label htmlFor="d25-sla-hours">Target hours for review</label>
            <input
              id="d25-sla-hours"
              type="number"
              min="1"
              value={slaHours}
              disabled={!canManage}
              onChange={(e) => setSlaHours(e.target.value)}
            />
          </div>
          {canManage && (
            <div className="workspace-actions">
              <button className="v3-btn primary" onClick={onSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save SLA default'}
              </button>
            </div>
          )}
        </div>
        <p className="muted" style={{ marginTop: 8 }}>
          Only the review SLA default hours are configurable from this surface.
          Capacity automation and escalation weights are not exposed here.
        </p>
      </div>

      <div className="workspace-pane">
        <h3>Current settings</h3>
        <table className="v3-ops-table">
          <tbody>
            <tr><td>Max reviews per staff</td><td>{settings.max_reviews_per_staff ?? '—'}</td></tr>
            <tr><td>SLA hours</td><td>{settings.sla_hours ?? '—'}</td></tr>
            <tr><td>Auto assign enabled</td><td>{settings.auto_assign_enabled === true ? 'Yes' : (settings.auto_assign_enabled === false ? 'No' : '—')}</td></tr>
            <tr><td>Escalation hours</td><td>{settings.escalation_hours ?? '—'}</td></tr>
            <tr><td>Last updated</td><td>{settings.updated_at ? new Date(settings.updated_at).toLocaleString() : '—'}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
