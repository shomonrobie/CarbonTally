// frontend/src/v3/ops/SettingsTab.jsx
// N3 — Configurable retention settings (platform control plane). Retention is
// a CONFIGURABLE product capability: the UI renders the configured values and
// lets authorised staff admins update them. No policy duration is invented —
// unset values render as "Not configured". Enforcement is server-side (N3);
// this surface is configuration only.
//
// Analytics & Integrations — Google Analytics 4 (the only provider
// implemented) is configuration only: an enabled flag and a measurement ID.
// The ID is configuration, not a secret. GA4 is loaded by the frontend only
// when this configuration is enabled and valid, the deployment is an analytics
// environment and the visitor has accepted cookies.
//
// CT-FINAL-01 — Upload policy: the effective upload limits (per file, files per
// batch, batch total) every ingress path enforces server-side.
//
// CT-FINAL-02 EMAIL-CONFIG-01 — Email delivery: the provider (Resend | SMTP),
// its non-secret SMTP transport configuration and the platform From address.
// No credential is ever entered, sent or displayed here: the panel shows which
// allow-listed environment variable is referenced and whether it is present.
import React, { useCallback, useEffect, useState } from 'react';
import {
  getAnalyticsSettings,
  getEmailProviderSettings,
  getNotificationSenderSettings,
  getRetentionSettings,
  getUploadPolicySettings,
  updateAnalyticsSettings,
  updateEmailProviderSettings,
  updateNotificationSenderSettings,
  updateRetentionSettings,
  updateUploadPolicySettings,
  validateEmailProviderSettings,
} from '../api';
import {
  isAnalyticsEnvironmentAllowed,
  isValidGa4MeasurementId,
} from '../../lib/analytics/ga4';
import { LoadingState, ErrorState, Alert, Button, TextInput, SelectInput, CheckboxField, ConfirmationDialog } from '../components/ui';

const FIELDS = [
  { key: 'audit_log_retention_days', label: 'Audit log retention (days)' },
  { key: 'data_retention_days', label: 'Data retention (days)' },
  { key: 'document_retention_days', label: 'Document retention (days)' },
  { key: 'backup_retention_days', label: 'Backup retention (days)' },
];

const GA4_ID_HINT = 'Google Analytics 4 measurement ID, e.g. G-XXXXXXXXXX';

const UPLOAD_FIELDS = [
  {
    key: 'max_file_size_mb',
    label: 'Maximum size per file (MB)',
    hint: 'Applies to every individual upload.',
  },
  {
    key: 'max_files_per_batch',
    label: 'Maximum files per batch',
    hint: 'Applies to a batch upload.',
  },
  {
    key: 'max_batch_size_mb',
    label: 'Maximum total size per batch (MB)',
    hint: 'Sum of the files in one batch.',
  },
];

const PROVIDER_LABELS = {
  resend: 'Resend (CarbonTally platform provider)',
  smtp: 'SMTP (own mail server / SMTP submission service)',
};

const DEFAULT_PROVIDER_FORM = {
  provider: 'resend',
  smtp_host: '',
  smtp_port: '',
  smtp_username: '',
  smtp_use_tls: true,
  credential_env: '',
};

export default function SettingsTab({ canManage }) {
  const [settings, setSettings] = useState(null);
  const [form, setForm] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // Analytics & Integrations (GA4) — separate load/save state so an analytics
  // problem can never block the retention configuration surface.
  const [analytics, setAnalytics] = useState(null);
  const [analyticsForm, setAnalyticsForm] = useState({ enabled: false, ga4_measurement_id: '' });
  const [analyticsError, setAnalyticsError] = useState('');
  const [analyticsNotice, setAnalyticsNotice] = useState('');
  const [analyticsBusy, setAnalyticsBusy] = useState(false);
  const [analyticsConfirm, setAnalyticsConfirm] = useState(false);

  // Upload policy (CT-FINAL-01).
  const [uploadPolicy, setUploadPolicy] = useState(null);
  const [uploadForm, setUploadForm] = useState({});
  const [uploadError, setUploadError] = useState('');
  const [uploadNotice, setUploadNotice] = useState('');
  const [uploadBusy, setUploadBusy] = useState(false);
  const [uploadConfirm, setUploadConfirm] = useState(false);

  // Email delivery provider + sender (CT-FINAL-02).
  const [provider, setProvider] = useState(null);
  const [providerForm, setProviderForm] = useState(DEFAULT_PROVIDER_FORM);
  const [senderForm, setSenderForm] = useState({ email_sender: '' });
  const [providerError, setProviderError] = useState('');
  const [providerNotice, setProviderNotice] = useState('');
  const [providerValidation, setProviderValidation] = useState(null);
  const [providerBusy, setProviderBusy] = useState(false);
  const [providerConfirm, setProviderConfirm] = useState(false);

  const applyProviderSettings = (s) => {
    setProvider(s);
    setProviderForm({
      provider: s.provider || DEFAULT_PROVIDER_FORM.provider,
      smtp_host: s.smtp && s.smtp.host ? s.smtp.host : '',
      smtp_port: s.smtp && s.smtp.port != null ? String(s.smtp.port) : '',
      smtp_username: s.smtp && s.smtp.username ? s.smtp.username : '',
      smtp_use_tls: s.smtp ? s.smtp.use_tls !== false : true,
      credential_env: s.credential_env || '',
    });
  };

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

    try {
      const result = await getAnalyticsSettings();
      const a = result.settings || {};
      setAnalytics(a);
      setAnalyticsForm({
        enabled: a.enabled === true,
        ga4_measurement_id: a.ga4_measurement_id || '',
      });
      setAnalyticsError('');
    } catch (e) {
      setAnalyticsError(e.message || 'Unable to load analytics configuration.');
    }

    try {
      const result = await getUploadPolicySettings();
      const p = result.settings || {};
      setUploadPolicy(p);
      const configured = p.configured || {};
      const next = {};
      UPLOAD_FIELDS.forEach((f) => {
        next[f.key] = configured[f.key] == null ? '' : String(configured[f.key]);
      });
      setUploadForm(next);
      setUploadError('');
    } catch (e) {
      setUploadError(e.message || 'Unable to load the upload policy.');
    }

    try {
      const [providerResult, senderResult] = await Promise.all([
        getEmailProviderSettings(),
        getNotificationSenderSettings(),
      ]);
      applyProviderSettings(providerResult.settings || {});
      setSenderForm({ email_sender: (senderResult.settings || {}).email_sender || '' });
      setProviderError('');
    } catch (e) {
      setProviderError(e.message || 'Unable to load the email delivery configuration.');
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

  const measurementId = analyticsForm.ga4_measurement_id.trim();
  const measurementIdInvalid = analyticsForm.enabled
    && !isValidGa4MeasurementId(measurementId);
  const analyticsEnvironmentActive = isAnalyticsEnvironmentAllowed();

  // ---------------------------------------------------------------------------
  // CT-FINAL-01 — upload policy
  // ---------------------------------------------------------------------------
  const uploadPayload = () => {
    const payload = {};
    UPLOAD_FIELDS.forEach((f) => {
      const raw = String(uploadForm[f.key] || '').trim();
      payload[f.key] = raw === '' ? null : Number(raw);
    });
    return payload;
  };

  const onSaveUploadPolicy = async () => {
    setUploadBusy(true);
    setUploadError('');
    try {
      const result = await updateUploadPolicySettings(uploadPayload());
      const p = result.settings || {};
      setUploadPolicy(p);
      const configured = p.configured || {};
      const next = {};
      UPLOAD_FIELDS.forEach((f) => {
        next[f.key] = configured[f.key] == null ? '' : String(configured[f.key]);
      });
      setUploadForm(next);
      setUploadConfirm(false);
      setUploadNotice('Upload policy saved. Every upload path enforces it server-side.');
      setTimeout(() => setUploadNotice(''), 6000);
    } catch (e) {
      setUploadConfirm(false);
      setUploadError(e.message || 'Failed to save the upload policy.');
    } finally {
      setUploadBusy(false);
    }
  };

  // ---------------------------------------------------------------------------
  // CT-FINAL-02 — email delivery provider + sender
  // ---------------------------------------------------------------------------
  const providerPayload = () => {
    const payload = { provider: providerForm.provider };
    if (providerForm.provider === 'smtp') {
      payload.smtp_host = String(providerForm.smtp_host || '').trim();
      payload.smtp_username = String(providerForm.smtp_username || '').trim();
      const port = String(providerForm.smtp_port || '').trim();
      if (port !== '') payload.smtp_port = Number(port);
      payload.smtp_use_tls = providerForm.smtp_use_tls === true;
    }
    if (providerForm.credential_env) payload.credential_env = providerForm.credential_env;
    return payload;
  };

  const onValidateProvider = async () => {
    setProviderBusy(true);
    setProviderError('');
    setProviderValidation(null);
    try {
      const result = await validateEmailProviderSettings(providerPayload());
      setProviderValidation(result);
    } catch (e) {
      setProviderError(e.message || 'Unable to validate the email provider configuration.');
    } finally {
      setProviderBusy(false);
    }
  };

  const onSaveProvider = async () => {
    setProviderBusy(true);
    setProviderError('');
    try {
      const result = await updateEmailProviderSettings(providerPayload());
      applyProviderSettings(result.settings || {});
      setProviderValidation(null);
      setProviderConfirm(false);
      setProviderNotice('Email delivery configuration saved.');
      setTimeout(() => setProviderNotice(''), 6000);
    } catch (e) {
      setProviderConfirm(false);
      setProviderError(e.message || 'Failed to save the email delivery configuration.');
    } finally {
      setProviderBusy(false);
    }
  };

  const onSaveSender = async () => {
    setProviderBusy(true);
    setProviderError('');
    try {
      const result = await updateNotificationSenderSettings({
        email_sender: String(senderForm.email_sender || '').trim() || null,
      });
      setSenderForm({ email_sender: (result.settings || {}).email_sender || '' });
      // Refresh the readiness description: the sender is part of it.
      const providerResult = await getEmailProviderSettings();
      applyProviderSettings(providerResult.settings || {});
      setProviderNotice('Notification sender saved.');
      setTimeout(() => setProviderNotice(''), 6000);
    } catch (e) {
      setProviderError(e.message || 'Failed to save the notification sender.');
    } finally {
      setProviderBusy(false);
    }
  };

  const onSaveAnalytics = async () => {
    setAnalyticsBusy(true);
    setAnalyticsError('');
    try {
      const result = await updateAnalyticsSettings({
        enabled: analyticsForm.enabled,
        ga4_measurement_id: measurementId === '' ? null : measurementId,
      });
      const a = result.settings || {};
      setAnalytics(a);
      setAnalyticsForm({
        enabled: a.enabled === true,
        ga4_measurement_id: a.ga4_measurement_id || '',
      });
      setAnalyticsConfirm(false);
      setAnalyticsNotice('Analytics configuration saved.');
      setTimeout(() => setAnalyticsNotice(''), 6000);
    } catch (e) {
      setAnalyticsConfirm(false);
      setAnalyticsError(e.message || 'Failed to save analytics configuration');
    } finally {
      setAnalyticsBusy(false);
    }
  };

  if (loading) return <LoadingState label="Loading settings…" />;
  if (error) return <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  if (!canManage) {
    return (
      <Alert tone="info" title="Settings are admin-managed">
        Platform retention and Analytics &amp; Integrations configuration are reserved for staff with
        staff-admin permissions.
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

      <div className="v3-card">
        <h2>Analytics &amp; Integrations</h2>
        <p className="v3-muted">
          Configuration for analytics providers. Google Analytics 4 is the only provider currently available.
        </p>

        {analyticsNotice && <Alert tone="success" title="Saved">{analyticsNotice}</Alert>}
        {analyticsError && <Alert tone="error" title="Not saved">{analyticsError}</Alert>}
        {!analytics && !analyticsError && <p className="v3-muted">Loading analytics configuration…</p>}

        {analytics && (
          <>
            <h3>Google Analytics</h3>
            <CheckboxField
              label="Enabled"
              checked={analyticsForm.enabled}
              onChange={(e) => setAnalyticsForm({ ...analyticsForm, enabled: e.target.checked })}
              hint="When enabled and correctly configured, the application loads Google's gtag.js and initialises GA4."
            />
            <div className="v3-form-grid">
              <TextInput
                label="Measurement ID"
                value={analyticsForm.ga4_measurement_id}
                onChange={(e) => setAnalyticsForm({ ...analyticsForm, ga4_measurement_id: e.target.value })}
                hint={GA4_ID_HINT}
                error={measurementIdInvalid ? 'Enter a GA4 measurement ID of the form G-XXXXXXXXXX.' : ''}
              />
            </div>
            <Alert tone="info" title="How analytics loads">
              GA4 loads on the public website and in the application only when it is enabled with a valid
              measurement ID, this deployment is the production environment and the visitor has accepted cookies.
              Analytics never affects core application behaviour, and no carbon, evidence or customer data is sent
              to the provider.
              {!analyticsEnvironmentActive && (
                <> This deployment is not a production environment, so analytics will not load here even if it is
                enabled.</>
              )}
            </Alert>
            <div className="v3-actions">
              <Button
                variant="primary"
                icon="save"
                disabled={measurementIdInvalid}
                onClick={() => setAnalyticsConfirm(true)}
              >
                Save analytics settings
              </Button>
            </div>
          </>
        )}
      </div>

      {analyticsConfirm && (
        <ConfirmationDialog
          open
          title="Save analytics configuration?"
          message={
            analyticsForm.enabled
              ? 'Google Analytics 4 will be loaded for visitors who have accepted cookies in the production environment.'
              : 'Google Analytics 4 will not be loaded.'
          }
          confirmLabel="Save"
          tone="approve"
          busy={analyticsBusy}
          onClose={() => setAnalyticsConfirm(false)}
          onConfirm={onSaveAnalytics}
        />
      )}

      <div className="v3-card">
        <h2>Upload policy</h2>
        <p className="v3-muted">
          The limits every upload path enforces server-side: per file, files per batch and total
          size per batch. Clearing a value restores the documented default; the platform ceilings
          shown below can never be exceeded.
        </p>

        {uploadNotice && <Alert tone="success" title="Saved">{uploadNotice}</Alert>}
        {uploadError && <Alert tone="error" title="Not saved">{uploadError}</Alert>}
        {!uploadPolicy && !uploadError && <p className="v3-muted">Loading upload policy…</p>}

        {uploadPolicy && (
          <>
            <div className="v3-form-grid">
              {UPLOAD_FIELDS.map((f) => (
                <TextInput
                  key={f.key}
                  label={f.label}
                  value={uploadForm[f.key] == null ? '' : uploadForm[f.key]}
                  onChange={(e) => setUploadForm({ ...uploadForm, [f.key]: e.target.value })}
                  hint={`${f.hint} Effective now: ${(uploadPolicy.effective || {})[f.key]}`}
                />
              ))}
            </div>
            <p className="v3-muted">
              Effective: {uploadPolicy.summary}. Platform ceilings:{' '}
              {(uploadPolicy.platform_caps || {}).max_file_size_mb}MB per file,{' '}
              {(uploadPolicy.platform_caps || {}).max_files_per_batch} files per batch,{' '}
              {(uploadPolicy.platform_caps || {}).max_batch_size_mb}MB per batch.
            </p>
            <div className="v3-actions">
              <Button variant="primary" icon="save" onClick={() => setUploadConfirm(true)}>
                Save upload policy
              </Button>
            </div>
          </>
        )}
      </div>

      {uploadConfirm && (
        <ConfirmationDialog
          open
          title="Save upload policy?"
          message="This changes the upload limits enforced for every organisation on the platform."
          confirmLabel="Save"
          tone="approve"
          busy={uploadBusy}
          onClose={() => setUploadConfirm(false)}
          onConfirm={onSaveUploadPolicy}
        />
      )}

      <div className="v3-card">
        <h2>Email delivery</h2>
        <p className="v3-muted">
          How the platform delivers transactional email, and which address it comes from. Delivery
          credentials are never entered or stored here — the platform reads them from the server
          environment variable named below.
        </p>

        {providerNotice && <Alert tone="success" title="Saved">{providerNotice}</Alert>}
        {providerError && <Alert tone="error" title="Not saved">{providerError}</Alert>}
        {!provider && !providerError && <p className="v3-muted">Loading email settings…</p>}

        {provider && (
          <>
            <SelectInput
              label="Delivery provider"
              value={providerForm.provider}
              onChange={(e) => setProviderForm({ ...providerForm, provider: e.target.value })}
              hint={`Effective now: ${PROVIDER_LABELS[provider.provider] || provider.provider}`}
            >
              {(provider.supported_providers || []).map((name) => (
                <option key={name} value={name}>
                  {PROVIDER_LABELS[name] || name}
                </option>
              ))}
            </SelectInput>

            {providerForm.provider === 'smtp' && (
              <div className="v3-form-grid">
                <TextInput
                  label="SMTP host"
                  value={providerForm.smtp_host}
                  onChange={(e) => setProviderForm({ ...providerForm, smtp_host: e.target.value })}
                  hint="Hostname only, e.g. mail.example.com"
                />
                <TextInput
                  label="SMTP port"
                  value={providerForm.smtp_port}
                  onChange={(e) => setProviderForm({ ...providerForm, smtp_port: e.target.value })}
                  hint="Default 587 (STARTTLS)"
                />
                <TextInput
                  label="SMTP username"
                  value={providerForm.smtp_username}
                  onChange={(e) => setProviderForm({ ...providerForm, smtp_username: e.target.value })}
                  hint="The mailbox the SMTP service authenticates as"
                />
                <CheckboxField
                  label="Use STARTTLS"
                  checked={providerForm.smtp_use_tls}
                  onChange={(e) => setProviderForm({ ...providerForm, smtp_use_tls: e.target.checked })}
                  hint="Leave enabled unless the provider requires plain SMTP."
                />
              </div>
            )}

            <SelectInput
              label="Credential environment variable"
              value={providerForm.credential_env}
              onChange={(e) => setProviderForm({ ...providerForm, credential_env: e.target.value })}
              hint={
                provider.credential_configured
                  ? `${provider.credential_env} is set in this environment.`
                  : `${provider.credential_env} is not set in this environment — delivery will fail until it is.`
              }
            >
              {(provider.credential_options || []).map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </SelectInput>

            <Alert
              tone={provider.readiness && provider.readiness.ready ? 'success' : 'warning'}
              title="Delivery readiness"
            >
              {provider.readiness && provider.readiness.ready ? (
                <>
                  The configured provider is ready to deliver email from{' '}
                  {provider.readiness.sender}.
                </>
              ) : (
                <>
                  Email cannot be delivered yet:
                  <ul>
                    {((provider.readiness || {}).blocking_issues || []).map((issue) => (
                      <li key={issue}>{issue}</li>
                    ))}
                  </ul>
                  The platform reports the failure honestly rather than showing a false success.
                </>
              )}
            </Alert>

            {providerValidation && (
              <Alert
                tone={providerValidation.valid ? 'info' : 'error'}
                title={
                  providerValidation.valid
                    ? 'Configuration valid (not saved yet)'
                    : 'Configuration rejected'
                }
              >
                {providerValidation.valid ? (
                  <>The values entered above are valid. Save them to apply.</>
                ) : (
                  <ul>
                    {(providerValidation.errors || ['The configuration is not valid.']).map((err) => (
                      <li key={err}>{err}</li>
                    ))}
                  </ul>
                )}
              </Alert>
            )}

            <h3>From address</h3>
            <TextInput
              label="Notification sender"
              value={senderForm.email_sender}
              onChange={(e) => setSenderForm({ email_sender: e.target.value })}
              hint="A CarbonTally platform address, e.g. CarbonTally <notifications@carbontally.co.uk>"
            />
            <p className="v3-muted">
              Configuration last updated:{' '}
              {provider.updated_at ? new Date(provider.updated_at).toLocaleString() : 'never'}
            </p>

            <div className="v3-actions">
              <Button
                variant="secondary"
                icon="check"
                disabled={providerBusy}
                onClick={onValidateProvider}
              >
                Validate configuration
              </Button>
              <Button
                variant="secondary"
                icon="notifications"
                disabled={providerBusy}
                onClick={onSaveSender}
              >
                Save sender
              </Button>
              <Button
                variant="primary"
                icon="save"
                disabled={providerBusy}
                onClick={() => setProviderConfirm(true)}
              >
                Save email delivery
              </Button>
            </div>
          </>
        )}
      </div>

      {providerConfirm && (
        <ConfirmationDialog
          open
          title="Save email delivery configuration?"
          message="New transactional email will be delivered through the selected provider. Credentials continue to come only from the server environment."
          confirmLabel="Save"
          tone="approve"
          busy={providerBusy}
          onClose={() => setProviderConfirm(false)}
          onConfirm={onSaveProvider}
        />
      )}
    </div>
  );
}
