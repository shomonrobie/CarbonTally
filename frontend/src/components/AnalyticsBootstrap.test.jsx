// CarbonTally — analytics bootstrap mount.
//
// Exercises the real bootstrap component with the real GA4 module: the mount
// must render nothing, load gtag.js exactly when consent/environment/Admin
// configuration allow it, and never load it otherwise.
import { render, waitFor } from '@testing-library/react';
import AnalyticsBootstrap from './AnalyticsBootstrap';
import { GA4_SCRIPT_ID } from '../lib/analytics/ga4';
import { CONSENT_ACCEPTED, CONSENT_DECLINED, recordCookieConsent } from '../lib/consent';

const MEASUREMENT_ID = 'G-ABC1234567';
const ORIGINAL_ENV = process.env.REACT_APP_ENVIRONMENT;
const ORIGINAL_API_URL = process.env.REACT_APP_API_URL;

const stubSettingsApi = (settings) => {
  const fetchImpl = jest.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ settings }),
  });
  global.fetch = fetchImpl;
  return fetchImpl;
};

const removeGa4Tag = () => {
  const script = document.getElementById(GA4_SCRIPT_ID);
  if (script) script.remove();
  delete window.dataLayer;
  delete window.gtag;
};

beforeEach(() => {
  removeGa4Tag();
  window.localStorage.clear();
  process.env.REACT_APP_ENVIRONMENT = 'production';
  process.env.REACT_APP_API_URL = 'https://api.example.test';
});

afterEach(() => {
  removeGa4Tag();
  window.localStorage.clear();
  delete global.fetch;
  if (ORIGINAL_ENV === undefined) delete process.env.REACT_APP_ENVIRONMENT;
  else process.env.REACT_APP_ENVIRONMENT = ORIGINAL_ENV;
  if (ORIGINAL_API_URL === undefined) delete process.env.REACT_APP_API_URL;
  else process.env.REACT_APP_API_URL = ORIGINAL_API_URL;
  jest.restoreAllMocks();
});

it('renders nothing', () => {
  stubSettingsApi({ enabled: false, ga4_measurement_id: null });
  const { container } = render(<AnalyticsBootstrap />);
  expect(container).toBeEmptyDOMElement();
});

it('loads gtag.js once the visitor has accepted cookies and analytics is enabled', async () => {
  recordCookieConsent(CONSENT_ACCEPTED);
  const fetchImpl = stubSettingsApi({ enabled: true, ga4_measurement_id: MEASUREMENT_ID });

  render(<AnalyticsBootstrap />);

  await waitFor(() => expect(document.getElementById(GA4_SCRIPT_ID)).not.toBeNull());
  expect(fetchImpl).toHaveBeenCalledWith(
    'https://api.example.test/api/v3/settings/analytics',
    expect.objectContaining({ method: 'GET' }),
  );
});

it('does not load gtag.js when the visitor has declined cookies', async () => {
  recordCookieConsent(CONSENT_DECLINED);
  const fetchImpl = stubSettingsApi({ enabled: true, ga4_measurement_id: MEASUREMENT_ID });

  render(<AnalyticsBootstrap />);

  await waitFor(() => expect(fetchImpl).not.toHaveBeenCalled());
  expect(document.getElementById(GA4_SCRIPT_ID)).toBeNull();
});

it('does not load gtag.js when the Admin configuration is disabled', async () => {
  recordCookieConsent(CONSENT_ACCEPTED);
  stubSettingsApi({ enabled: false, ga4_measurement_id: MEASUREMENT_ID });

  render(<AnalyticsBootstrap />);

  await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
  expect(document.getElementById(GA4_SCRIPT_ID)).toBeNull();
});

it('stays operational when the settings request fails', async () => {
  recordCookieConsent(CONSENT_ACCEPTED);
  global.fetch = jest.fn().mockRejectedValue(new Error('offline'));

  render(<AnalyticsBootstrap />);

  await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
  expect(document.getElementById(GA4_SCRIPT_ID)).toBeNull();
});
