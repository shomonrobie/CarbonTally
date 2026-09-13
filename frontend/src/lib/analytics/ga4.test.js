// CarbonTally — Google Analytics 4 loader behaviour.
//
// These tests exercise the real module (no mocks of the analytics code itself):
// the decisions, the DOM effect of loading, the consent and environment gates,
// and failure tolerance are all asserted against the production code paths.
import {
  GA4_SCRIPT_ID,
  fetchGa4Config,
  initGa4Analytics,
  isAnalyticsEnvironmentAllowed,
  isValidGa4MeasurementId,
  loadGa4,
  normaliseGa4MeasurementId,
  shouldLoadGa4,
} from './ga4';
import {
  CONSENT_ACCEPTED,
  CONSENT_CHANGE_EVENT,
  CONSENT_DECLINED,
  COOKIE_CONSENT_KEY,
  readCookieConsent,
  recordCookieConsent,
  subscribeToConsentChanges,
} from '../consent';

const MEASUREMENT_ID = 'G-ABC1234567';
const SETTINGS_URL = 'https://api.example.test/api/v3/settings/analytics';

const ORIGINAL_ENV = process.env.REACT_APP_ENVIRONMENT;
const ORIGINAL_API_URL = process.env.REACT_APP_API_URL;

/** Remove any GA4 tag plus gtag state left by a previous test. */
const resetGa4Dom = () => {
  const script = document.getElementById(GA4_SCRIPT_ID);
  if (script) script.remove();
  delete window.dataLayer;
  delete window.gtag;
};

const jsonResponse = (body, ok = true) => ({
  ok,
  status: ok ? 200 : 500,
  json: async () => body,
});

beforeEach(() => {
  resetGa4Dom();
  window.localStorage.clear();
  process.env.REACT_APP_ENVIRONMENT = 'production';
  process.env.REACT_APP_API_URL = 'https://api.example.test';
});

afterEach(() => {
  resetGa4Dom();
  window.localStorage.clear();
  if (ORIGINAL_ENV === undefined) delete process.env.REACT_APP_ENVIRONMENT;
  else process.env.REACT_APP_ENVIRONMENT = ORIGINAL_ENV;
  if (ORIGINAL_API_URL === undefined) delete process.env.REACT_APP_API_URL;
  else process.env.REACT_APP_API_URL = ORIGINAL_API_URL;
  jest.restoreAllMocks();
});

describe('measurement ID validation', () => {
  it('accepts a well-formed GA4 measurement ID', () => {
    expect(isValidGa4MeasurementId(MEASUREMENT_ID)).toBe(true);
  });

  it('accepts and normalises casing and surrounding whitespace', () => {
    expect(normaliseGa4MeasurementId('  g-abc1234567 ')).toBe(MEASUREMENT_ID);
    expect(isValidGa4MeasurementId('  g-abc1234567 ')).toBe(true);
  });

  it.each([
    'UA-123456-1',
    'GTM-ABCDEF',
    'G-',
    'G-AB',
    'ABC1234567',
    'G-ABC-123456',
    '',
    '   ',
    null,
    undefined,
    12345,
    {},
  ])('rejects %p', (candidate) => {
    expect(isValidGa4MeasurementId(candidate)).toBe(false);
  });

  it('treats an unset value as null', () => {
    expect(normaliseGa4MeasurementId('')).toBeNull();
    expect(normaliseGa4MeasurementId(null)).toBeNull();
  });
});

describe('environment gate', () => {
  it('allows only an explicit production deployment', () => {
    expect(isAnalyticsEnvironmentAllowed('production')).toBe(true);
    expect(isAnalyticsEnvironmentAllowed(' Production ')).toBe(true);
    expect(isAnalyticsEnvironmentAllowed('staging')).toBe(false);
    expect(isAnalyticsEnvironmentAllowed('development')).toBe(false);
    expect(isAnalyticsEnvironmentAllowed('')).toBe(false);
    expect(isAnalyticsEnvironmentAllowed('false')).toBe(false);
  });

  it('falls back to the deployment environment and fails closed when unset', () => {
    process.env.REACT_APP_ENVIRONMENT = 'staging';
    expect(isAnalyticsEnvironmentAllowed(undefined)).toBe(false);
    delete process.env.REACT_APP_ENVIRONMENT;
    expect(isAnalyticsEnvironmentAllowed(undefined)).toBe(false);
    process.env.REACT_APP_ENVIRONMENT = 'production';
    expect(isAnalyticsEnvironmentAllowed(undefined)).toBe(true);
  });
});

describe('load decision', () => {
  const enabledConfig = { enabled: true, ga4_measurement_id: MEASUREMENT_ID };
  const production = { environment: 'production', consent: CONSENT_ACCEPTED };

  it('does not load when analytics is disabled', () => {
    expect(shouldLoadGa4({ enabled: false, ga4_measurement_id: MEASUREMENT_ID }, production)).toBe(false);
  });

  it('loads when enabled, valid, in production and consented', () => {
    expect(shouldLoadGa4(enabledConfig, production)).toBe(true);
  });

  it('does not load when the measurement ID is missing', () => {
    expect(shouldLoadGa4({ enabled: true, ga4_measurement_id: null }, production)).toBe(false);
    expect(shouldLoadGa4({ enabled: true }, production)).toBe(false);
  });

  it('does not load when the measurement ID is invalid', () => {
    expect(shouldLoadGa4({ enabled: true, ga4_measurement_id: 'UA-123456-1' }, production)).toBe(false);
    expect(shouldLoadGa4({ enabled: true, ga4_measurement_id: 'not-an-id' }, production)).toBe(false);
  });

  it('does not load outside a production deployment', () => {
    expect(shouldLoadGa4(enabledConfig, { environment: 'staging', consent: CONSENT_ACCEPTED })).toBe(false);
    process.env.REACT_APP_ENVIRONMENT = 'staging';
    expect(shouldLoadGa4(enabledConfig, { consent: CONSENT_ACCEPTED })).toBe(false);
    delete process.env.REACT_APP_ENVIRONMENT;
    expect(shouldLoadGa4(enabledConfig, { consent: CONSENT_ACCEPTED })).toBe(false);
  });

  it('inherits the deployment environment when none is supplied', () => {
    expect(shouldLoadGa4(enabledConfig, { consent: CONSENT_ACCEPTED })).toBe(true);
  });

  it('does not load without an accepted consent choice', () => {
    expect(shouldLoadGa4(enabledConfig, { environment: 'production', consent: CONSENT_DECLINED })).toBe(false);
    expect(shouldLoadGa4(enabledConfig, { environment: 'production', consent: null })).toBe(false);
    expect(shouldLoadGa4(enabledConfig, { environment: 'production', consent: 'unset' })).toBe(false);
  });

  it('does not load without a configuration', () => {
    expect(shouldLoadGa4(null, production)).toBe(false);
    expect(shouldLoadGa4(undefined, production)).toBe(false);
  });

  it('reads the stored consent choice when none is supplied', () => {
    recordCookieConsent(CONSENT_ACCEPTED);
    expect(shouldLoadGa4(enabledConfig, { environment: 'production' })).toBe(true);
    recordCookieConsent(CONSENT_DECLINED);
    expect(shouldLoadGa4(enabledConfig, { environment: 'production' })).toBe(false);
  });
});

describe('gtag.js loading', () => {
  it('injects Google\u2019s gtag.js for the configured measurement ID', () => {
    expect(loadGa4(MEASUREMENT_ID)).toBe(true);

    const script = document.getElementById(GA4_SCRIPT_ID);
    expect(script).not.toBeNull();
    expect(script.src).toBe(`https://www.googletagmanager.com/gtag/js?id=${MEASUREMENT_ID}`);
    expect(script.async).toBe(true);
  });

  it('initialises GA4 with the measurement ID and nothing else', () => {
    loadGa4(MEASUREMENT_ID);

    // Only the standard js/config calls are queued — no custom events and no
    // application or carbon data.
    expect(window.dataLayer.length).toBe(2);
    expect(Array.from(window.dataLayer[0])).toEqual(['js', expect.any(Date)]);
    expect(Array.from(window.dataLayer[1])).toEqual(['config', MEASUREMENT_ID]);
  });

  it('does not inject a tag for an invalid or missing measurement ID', () => {
    expect(loadGa4('UA-123456-1')).toBe(false);
    expect(loadGa4('')).toBe(false);
    expect(loadGa4(null)).toBe(false);
    expect(document.getElementById(GA4_SCRIPT_ID)).toBeNull();
  });

  it('is idempotent — a second call does not add a second tag', () => {
    loadGa4(MEASUREMENT_ID);
    loadGa4(MEASUREMENT_ID);
    expect(document.querySelectorAll(`#${GA4_SCRIPT_ID}`).length).toBe(1);
    expect(window.dataLayer.length).toBe(2);
  });

  it('fails safely when the tag cannot be injected', () => {
    jest.spyOn(document.head, 'appendChild').mockImplementation(() => {
      throw new Error('blocked by the browser');
    });
    expect(() => loadGa4(MEASUREMENT_ID)).not.toThrow();
    expect(loadGa4(MEASUREMENT_ID)).toBe(false);
  });
});

describe('configuration retrieval', () => {
  it('reads the enabled flag and measurement ID from the platform settings API', async () => {
    const fetchImpl = jest.fn().mockResolvedValue(
      jsonResponse({ settings: { enabled: true, ga4_measurement_id: MEASUREMENT_ID } }),
    );
    const config = await fetchGa4Config({ apiUrl: 'https://api.example.test', fetchImpl });

    expect(fetchImpl).toHaveBeenCalledTimes(1);
    const [url, options] = fetchImpl.mock.calls[0];
    expect(url).toBe(SETTINGS_URL);
    expect(options.method).toBe('GET');
    expect(options.body).toBeUndefined();
    expect(config).toEqual({ enabled: true, ga4_measurement_id: MEASUREMENT_ID });
  });

  it('fails safely on an error response', async () => {
    const fetchImpl = jest.fn().mockResolvedValue(jsonResponse({}, false));
    expect(await fetchGa4Config({ apiUrl: 'https://api.example.test', fetchImpl })).toBeNull();
  });

  it('fails safely on a network failure', async () => {
    const fetchImpl = jest.fn().mockRejectedValue(new Error('offline'));
    await expect(
      fetchGa4Config({ apiUrl: 'https://api.example.test', fetchImpl }),
    ).resolves.toBeNull();
  });

  it('fails safely on a malformed payload', async () => {
    const fetchImpl = jest.fn().mockResolvedValue(jsonResponse({ unexpected: true }));
    expect(await fetchGa4Config({ apiUrl: 'https://api.example.test', fetchImpl })).toBeNull();

    const broken = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => {
        throw new Error('invalid json');
      },
    });
    expect(await fetchGa4Config({ apiUrl: 'https://api.example.test', fetchImpl: broken })).toBeNull();
  });

  it('does nothing when no API URL is configured', async () => {
    const fetchImpl = jest.fn();
    expect(await fetchGa4Config({ apiUrl: '', fetchImpl })).toBeNull();
    expect(fetchImpl).not.toHaveBeenCalled();
  });
});

describe('bootstrap', () => {
  const runInit = (body, ok = true) => {
    const fetchImpl = jest.fn().mockResolvedValue(jsonResponse(body, ok));
    return { fetchImpl, result: initGa4Analytics({ apiUrl: 'https://api.example.test', fetchImpl }) };
  };

  it('loads GA4 when enabled, valid, in production and consented', async () => {
    recordCookieConsent(CONSENT_ACCEPTED);
    const { result } = runInit({ settings: { enabled: true, ga4_measurement_id: MEASUREMENT_ID } });
    await expect(result).resolves.toBe(true);
    expect(document.getElementById(GA4_SCRIPT_ID)).not.toBeNull();
  });

  it('does not load gtag.js when analytics is disabled', async () => {
    recordCookieConsent(CONSENT_ACCEPTED);
    const { fetchImpl, result } = runInit({
      settings: { enabled: false, ga4_measurement_id: MEASUREMENT_ID },
    });
    await expect(result).resolves.toBe(false);
    expect(document.getElementById(GA4_SCRIPT_ID)).toBeNull();
    // The configuration is still read, so the Admin setting is what decided it.
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  it('does not load gtag.js when the measurement ID is missing', async () => {
    recordCookieConsent(CONSENT_ACCEPTED);
    const { result } = runInit({ settings: { enabled: true, ga4_measurement_id: null } });
    await expect(result).resolves.toBe(false);
    expect(document.getElementById(GA4_SCRIPT_ID)).toBeNull();
  });

  it('does not load gtag.js when the measurement ID is invalid', async () => {
    recordCookieConsent(CONSENT_ACCEPTED);
    const { result } = runInit({ settings: { enabled: true, ga4_measurement_id: 'UA-123456-1' } });
    await expect(result).resolves.toBe(false);
    expect(document.getElementById(GA4_SCRIPT_ID)).toBeNull();
  });

  it('never contacts the analytics configuration endpoint without consent', async () => {
    recordCookieConsent(CONSENT_DECLINED);
    const { fetchImpl, result } = runInit({
      settings: { enabled: true, ga4_measurement_id: MEASUREMENT_ID },
    });
    await expect(result).resolves.toBe(false);
    expect(fetchImpl).not.toHaveBeenCalled();
    expect(document.getElementById(GA4_SCRIPT_ID)).toBeNull();
  });

  it('does not load outside a production deployment', async () => {
    process.env.REACT_APP_ENVIRONMENT = 'staging';
    recordCookieConsent(CONSENT_ACCEPTED);
    const { fetchImpl, result } = runInit({
      settings: { enabled: true, ga4_measurement_id: MEASUREMENT_ID },
    });
    await expect(result).resolves.toBe(false);
    expect(fetchImpl).not.toHaveBeenCalled();
    expect(document.getElementById(GA4_SCRIPT_ID)).toBeNull();
  });

  it('continues normally when the configuration request fails', async () => {
    recordCookieConsent(CONSENT_ACCEPTED);
    const { result } = runInit({}, false);
    await expect(result).resolves.toBe(false);
    expect(document.getElementById(GA4_SCRIPT_ID)).toBeNull();
  });
});

describe('existing consent mechanism', () => {
  it('records the choice under the existing cookieConsent key', () => {
    recordCookieConsent(CONSENT_ACCEPTED);
    expect(window.localStorage.getItem(COOKIE_CONSENT_KEY)).toBe(CONSENT_ACCEPTED);
    expect(readCookieConsent()).toBe(CONSENT_ACCEPTED);
  });

  it('notifies consent consumers when the choice is recorded', () => {
    const listener = jest.fn();
    window.addEventListener(CONSENT_CHANGE_EVENT, listener);
    recordCookieConsent(CONSENT_ACCEPTED);
    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener(CONSENT_CHANGE_EVENT, listener);
  });

  it('subscribes to consent changes and unsubscribes cleanly', () => {
    const listener = jest.fn();
    const unsubscribe = subscribeToConsentChanges(listener);
    recordCookieConsent(CONSENT_ACCEPTED);
    expect(listener).toHaveBeenCalledWith(CONSENT_ACCEPTED);
    unsubscribe();
    recordCookieConsent(CONSENT_DECLINED);
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it('treats unreadable storage as no recorded choice', () => {
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('storage blocked');
    });
    expect(readCookieConsent()).toBeNull();
  });
});
