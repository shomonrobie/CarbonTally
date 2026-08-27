// frontend/src/v3/ops/SettingsTab.jsx
// N3 — Configurable retention settings (platform control plane). Retention is
// a CONFIGURABLE product capability: the UI renders the configured values and
// lets authorised staff admins update them. No policy duration is invented —
// unset values render as "Not configured". Enforcement is server-side (N3);
// this surface is configuration only.
import React, { useCallback, useEffect, useState } from 'react';
import { getRetentionSettings, updateRetentionSettings } from '../api';
import { LoadingState, ErrorState, Alert, Button, TextInput, ConfirmationDialog } from '../components/ui';

const FIELDS = [
  { key: 'audit_log_retention_days', label: 'Audit log retention (days)' },
  { key: 'data_retention_days', label: 'Data retention (days)' },
  { key: 'document_retention_days', label: 'Document retention (days)' },
  { key: 'backup_retention_days', label: 'Backup retention (days)' },
];

export default function SettingsTab({ canManage }) {
  const [settings, setSettings] = useState(null);
  const [form, setForm] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getRetentionSettings();
      const s = result.settings || {};
      setSettings(s);
      const next = {};
      FIELDS.forEach((f) => { next[f.key] = s[f.key] == null ? '' : String(s[f.key]); });
      setForm(next);
    } catch (e) {
      setError(e.message || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load, retryCount]);

  const onSave = async () => {
    setBusy(true);
    setError('');
    const payload = {};
    FIELDS.forEach((f) => {
      const raw = form[f.key].trim();
      payload[f.key] = raw === '' ? null : Number(raw);
    });
    try {
      const result = await updateRetentionSettings(payload);
      setSettings(result.settings);
      setConfirm(false);
      setNotice('Retention settings saved. Enforcement is applied by the platform.');
      setTimeout(() => setNotice(''), 6000);
    } catch (e) {
      setError(e.message || 'Failed to save settings');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <LoadingState label="Loading settings…" />;
  if (error) return <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  if (!canManage) {
    return (
      <Alert tone="info" title="Settings are admin-managed">
        Platform retention configuration is reserved for staff with staff-admin permissions.
      </Alert>
    );
  }

  return (
    <div>
      {notice && <Alert tone="success" title="Saved">{notice}</Alert>}
      {error && <Alert tone="error" title="Not saved">{error}</Alert>}

      <Alert tone="warning" title="Configurable retention (N3)">
        Retention is a configurable platform capability. Values shown are the currently configured policy. Unset
        values mean "no platform-configured duration" — they are not defaults invented by the UI. Enforcement is
        server-side.
      </Alert>

      <div className="v3-card">
        <h2>Data retention policy</h2>
        <div className="v3-form-grid">
          {FIELDS.map((f) => (
            <TextInput
              key={f.key}
              label={f.label}
              value={form[f.key]}
              onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
              hint={settings[f.key] == null ? 'Not configured' : 'Configured'}
            />
          ))}
        </div>
        <div className="v3-actions">
          <Button variant="primary" icon="save" onClick={() => setConfirm(true)}>Save changes</Button>
        </div>
      </div>

      {settings && (
        <p className="v3-muted">
          Last updated: {settings.updated_at ? new Date(settings.updated_at).toLocaleString() : 'never'}
        </p>
      )}

      {confirm && (
        <ConfirmationDialog
          open
          title="Save retention policy?"
          message="This updates the platform-wide retention configuration. Enforcement remains a server-side concern."
          confirmLabel="Save"
          tone="approve"
          busy={busy}
          onClose={() => setConfirm(false)}
          onConfirm={onSave}
        />
      )}
    </div>
  );
}
