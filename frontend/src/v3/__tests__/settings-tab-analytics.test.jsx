// frontend/src/v3/__tests__/settings-tab-analytics.test.jsx
// Analytics & Integrations in the platform control plane (Admin → Settings).
//
// Covers: the existing retention surface is unchanged, the GA4 configuration is
// readable and writable by staff-admin capability only, an invalid measurement
// ID cannot be submitted, and a deployment that is not an analytics environment
// says so plainly instead of silently doing nothing.
import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../api', () => ({
  getRetentionSettings: jest.fn(),
  updateRetentionSettings: jest.fn(),
  getAnalyticsSettings: jest.fn(),
  updateAnalyticsSettings: jest.fn(),
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

const renderTab = async (canManage, analytics) => {
  api.getRetentionSettings.mockResolvedValue({ settings: RETENTION });
  api.getAnalyticsSettings.mockResolvedValue({ settings: analytics });
  const view = render(<SettingsTab canManage={canManage} />);
  await waitFor(() => expect(api.getRetentionSettings).toHaveBeenCalled());
  return view;
};

beforeEach(() => {
  jest.clearAllMocks();
  // jest runs without a production environment: the tab must say so.
  delete process.env.REACT_APP_ENVIRONMENT;
});

it('keeps the existing retention surface working', async () => {
  await renderTab(true, { enabled: false, ga4_measurement_id: null });

  await waitFor(() => expect(screen.getByText('Data retention policy')).toBeInTheDocument());
  expect(screen.getByLabelText('Audit log retention (days)')).toHaveValue('365');
  expect(screen.getByLabelText('Data retention (days)')).toHaveValue('');
});

it('does not expose analytics configuration to staff without admin capability', async () => {
  await renderTab(false, { enabled: false, ga4_measurement_id: null });

  await waitFor(() =>
    expect(screen.getByText('Settings are admin-managed')).toBeInTheDocument(),
  );
  expect(screen.queryByText('Analytics & Integrations')).not.toBeInTheDocument();
  expect(screen.queryByLabelText('Measurement ID')).not.toBeInTheDocument();
});

it('renders the configured GA4 state', async () => {
  await renderTab(true, { enabled: true, ga4_measurement_id: 'G-ABC1234567' });

  await waitFor(() => expect(screen.getByText('Analytics & Integrations')).toBeInTheDocument());
  expect(screen.getByLabelText('Enabled')).toBeChecked();
  expect(screen.getByLabelText('Measurement ID')).toHaveValue('G-ABC1234567');
});

it('states plainly that analytics cannot load outside production', async () => {
  await renderTab(true, { enabled: true, ga4_measurement_id: 'G-ABC1234567' });

  await waitFor(() => expect(screen.getByText('How analytics loads')).toBeInTheDocument());
  expect(
    screen.getByText(/This deployment is not a production environment/),
  ).toBeInTheDocument();
});

it('saves the GA4 configuration through the platform settings API', async () => {
  api.updateAnalyticsSettings.mockResolvedValue({
    settings: { enabled: true, ga4_measurement_id: 'G-ABC1234567' },
  });
  await renderTab(true, { enabled: false, ga4_measurement_id: null });

  await waitFor(() => expect(screen.getByLabelText('Enabled')).toBeInTheDocument());
  fireEvent.click(screen.getByLabelText('Enabled'));
  fireEvent.change(screen.getByLabelText('Measurement ID'), {
    target: { value: 'G-ABC1234567' },
  });

  fireEvent.click(screen.getByRole('button', { name: /save analytics settings/i }));
  const dialog = await screen.findByRole('dialog');
  fireEvent.click(within(dialog).getByRole('button', { name: 'Save' }));

  await waitFor(() =>
    expect(api.updateAnalyticsSettings).toHaveBeenCalledWith({
      enabled: true,
      ga4_measurement_id: 'G-ABC1234567',
    }),
  );
});

it('will not submit an enabled analytics configuration with an invalid ID', async () => {
  await renderTab(true, { enabled: true, ga4_measurement_id: 'G-ABC1234567' });

  await waitFor(() => expect(screen.getByLabelText('Measurement ID')).toBeInTheDocument());
  fireEvent.change(screen.getByLabelText('Measurement ID'), {
    target: { value: 'UA-123456-1' },
  });

  expect(screen.getByText(/Enter a GA4 measurement ID/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /save analytics settings/i })).toBeDisabled();
  expect(api.updateAnalyticsSettings).not.toHaveBeenCalled();
});
