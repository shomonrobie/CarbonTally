// frontend/src/v3/__tests__/settings-tab-email-provider.test.jsx
// CT-FINAL-01 upload policy + CT-FINAL-02 email delivery in the platform control
// plane (Admin → Settings).
//
// Covers: the effective upload limits are visible and saveable, the delivery
// provider and its non-secret transport fields are configurable, the credential
// variable may only be chosen from the server-published allow-list, readiness
// blocking issues are surfaced honestly, and NO credential value is ever shown.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../api', () => ({
  getRetentionSettings: jest.fn(),
  updateRetentionSettings: jest.fn(),
  getAnalyticsSettings: jest.fn(),
  updateAnalyticsSettings: jest.fn(),
  getUploadPolicySettings: jest.fn(),
  updateUploadPolicySettings: jest.fn(),
  getNotificationSenderSettings: jest.fn(),
  updateNotificationSenderSettings: jest.fn(),
  getEmailProviderSettings: jest.fn(),
  validateEmailProviderSettings: jest.fn(),
  updateEmailProviderSettings: jest.fn(),
}));

import SettingsTab from '../ops/SettingsTab';
import * as api from '../api';

const RETENTION = {
  audit_log_retention_days: 365,
  data_retention_days: null,
  document_retention_days: null,
  backup_retention_days: null,
  updated_at: '2026-09-13T09:00:00+00:00',
};

const ANALYTICS = { enabled: false, ga4_measurement_id: null };

const UPLOAD = {
  effective: { max_file_size_mb: 6, max_files_per_batch: 50, max_batch_size_mb: 500 },
  configured: { max_file_size_mb: 3, max_files_per_batch: null, max_batch_size_mb: null },
  defaults: { max_file_size_mb: 6, max_files_per_batch: 50, max_batch_size_mb: 500 },
  platform_caps: { max_file_size_mb: 10, max_files_per_batch: 50, max_batch_size_mb: 500 },
  summary: '3MB per file, 50 files per batch, 500MB per batch',
  updated_at: '2026-09-29T09:00:00+00:00',
  updated_by: 'u-admin',
};

const SMTP_PROVIDER = {
  provider: 'smtp',
  is_default: false,
  configured: true,
  supported_providers: ['resend', 'smtp'],
  default_provider: 'resend',
  credential_env: 'CT_SMTP_PASSWORD',
  credential_source: 'environment',
  credential_configured: true,
  credential_options: ['CT_SMTP_PASSWORD', 'RESEND_API_KEY', 'SMTP_PASSWORD'],
  smtp: {
    host: 'mail.example.com',
    port: 587,
    username: 'notifications@example.com',
    use_tls: true,
  },
  stored_invalid: null,
  readiness: {
    provider: 'smtp',
    ready: false,
    blocking_issues: ['smtp_username is not configured'],
    credential_env: 'CT_SMTP_PASSWORD',
    credential_configured: false,
    sender: 'CarbonTally <notifications@carbontally.co.uk>',
  },
  updated_at: '2026-09-29T09:00:00+00:00',
  updated_by: 'u-admin',
};

const renderTab = async (overrides = {}) => {
  api.getRetentionSettings.mockResolvedValue({ settings: RETENTION });
  api.getAnalyticsSettings.mockResolvedValue({ settings: ANALYTICS });
  api.getUploadPolicySettings.mockResolvedValue({ settings: UPLOAD });
  api.getNotificationSenderSettings.mockResolvedValue({
    settings: { email_sender: 'CarbonTally <notifications@carbontally.co.uk>' },
  });
  api.getEmailProviderSettings.mockResolvedValue({
    settings: overrides.provider || SMTP_PROVIDER,
  });
  const view = render(<SettingsTab canManage />);
  await waitFor(() => expect(api.getEmailProviderSettings).toHaveBeenCalled());
  return view;
};

beforeEach(() => {
  jest.clearAllMocks();
  delete process.env.REACT_APP_ENVIRONMENT;
});

it('shows the configured upload limits and the platform ceilings', async () => {
  await renderTab();

  expect(await screen.findByText('Upload policy')).toBeInTheDocument();
  expect(screen.getByLabelText('Maximum size per file (MB)')).toHaveValue('3');
  expect(screen.getByLabelText('Maximum files per batch')).toHaveValue('');
  expect(screen.getByText(/Platform ceilings:/)).toHaveTextContent(
    '10MB per file, 50 files per batch, 500MB per batch',
  );
});

it('saves the upload policy through the admin endpoint', async () => {
  api.updateUploadPolicySettings.mockResolvedValue({ settings: UPLOAD });
  await renderTab();

  fireEvent.change(await screen.findByLabelText('Maximum files per batch'), {
    target: { value: '8' },
  });
  fireEvent.click(screen.getByRole('button', { name: /Save upload policy/i }));
  fireEvent.click(screen.getByRole('button', { name: /^Save$/ }));

  await waitFor(() =>
    expect(api.updateUploadPolicySettings).toHaveBeenCalledWith({
      max_file_size_mb: 3,
      max_files_per_batch: 8,
      max_batch_size_mb: null,
    }),
  );
});

it('shows the delivery provider, its transport and the credential variable', async () => {
  await renderTab();

  expect(await screen.findByText('Email delivery')).toBeInTheDocument();
  // The selected provider is described, not implied.
  expect(screen.getByLabelText('Delivery provider')).toHaveValue('smtp');
  expect(screen.getByLabelText('SMTP host')).toHaveValue('mail.example.com');
  expect(screen.getByLabelText('SMTP port')).toHaveValue('587');
  expect(screen.getByLabelText('SMTP username')).toHaveValue('notifications@example.com');
  // Only the server-published allow-listed variables are offered.
  const credentialSelect = screen.getByLabelText('Credential environment variable');
  expect(credentialSelect).toHaveValue('CT_SMTP_PASSWORD');
  expect(Array.from(credentialSelect.options).map((o) => o.value)).toEqual([
    'CT_SMTP_PASSWORD',
    'RESEND_API_KEY',
    'SMTP_PASSWORD',
  ]);
});

it('never renders a credential value', async () => {
  await renderTab();

  const text = document.body.textContent;
  expect(text).not.toMatch(/re_[A-Za-z0-9]/);
  expect(text).toContain('CT_SMTP_PASSWORD is set in this environment.');
});

it('surfaces readiness blocking issues instead of claiming success', async () => {
  await renderTab();

  expect(await screen.findByText('Delivery readiness')).toBeInTheDocument();
  expect(screen.getByText('smtp_username is not configured')).toBeInTheDocument();
  expect(screen.queryByText(/ready to deliver email from/)).not.toBeInTheDocument();
});

it('validates the configuration without saving it', async () => {
  api.validateEmailProviderSettings.mockResolvedValue({
    valid: false,
    errors: ['smtp_host is required'],
  });
  await renderTab();

  fireEvent.click(await screen.findByRole('button', { name: /Validate configuration/i }));

  await waitFor(() =>
    expect(api.validateEmailProviderSettings).toHaveBeenCalledWith({
      provider: 'smtp',
      smtp_host: 'mail.example.com',
      smtp_username: 'notifications@example.com',
      smtp_port: 587,
      smtp_use_tls: true,
      credential_env: 'CT_SMTP_PASSWORD',
    }),
  );
  expect(await screen.findByText('Configuration rejected')).toBeInTheDocument();
  expect(api.updateEmailProviderSettings).not.toHaveBeenCalled();
});

it('saves the provider configuration', async () => {
  api.updateEmailProviderSettings.mockResolvedValue({ settings: SMTP_PROVIDER });
  await renderTab();

  fireEvent.click(await screen.findByRole('button', { name: /Save email delivery/i }));
  fireEvent.click(screen.getByRole('button', { name: /^Save$/ }));

  await waitFor(() => expect(api.updateEmailProviderSettings).toHaveBeenCalled());
  expect(api.updateEmailProviderSettings.mock.calls[0][0]).toMatchObject({
    provider: 'smtp',
    smtp_host: 'mail.example.com',
  });
});

it('saves the From address through the notification-sender endpoint', async () => {
  api.updateNotificationSenderSettings.mockResolvedValue({
    settings: { email_sender: 'CarbonTally <no-reply@carbontally.co.uk>' },
  });
  await renderTab();

  fireEvent.change(await screen.findByLabelText('Notification sender'), {
    target: { value: 'CarbonTally <no-reply@carbontally.co.uk>' },
  });
  fireEvent.click(screen.getByRole('button', { name: /Save sender/i }));

  await waitFor(() =>
    expect(api.updateNotificationSenderSettings).toHaveBeenCalledWith({
      email_sender: 'CarbonTally <no-reply@carbontally.co.uk>',
    }),
  );
});
