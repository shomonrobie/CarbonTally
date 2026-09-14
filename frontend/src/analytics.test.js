// Verifies the PostHog wiring: inert without a key, and once a key is set it
// initializes opted out, turns on only after cookie consent, and captures
// $pageview by hand.

const mockPosthog = {
  init: jest.fn(),
  opt_in_capturing: jest.fn(),
  opt_out_capturing: jest.fn(),
  capture: jest.fn(),
};

jest.mock('posthog-js', () => mockPosthog);

const KEY = 'REACT_APP_PUBLIC_POSTHOG_KEY';
const HOST = 'REACT_APP_PUBLIC_POSTHOG_HOST';

function loadAnalytics() {
  let mod;
  jest.isolateModules(() => {
    mod = require('./analytics');
  });
  return mod;
}

describe('analytics', () => {
  const originalEnv = { key: process.env[KEY], host: process.env[HOST] };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    delete process.env[KEY];
    delete process.env[HOST];
  });

  afterAll(() => {
    process.env[KEY] = originalEnv.key;
    process.env[HOST] = originalEnv.host;
  });

  it('stays inert with no project key', () => {
    const a = loadAnalytics();
    expect(a.isAnalyticsEnabled).toBe(false);
    a.initPostHog();
    a.capturePageview();
    a.setAnalyticsConsent(true);
    expect(mockPosthog.init).not.toHaveBeenCalled();
    expect(mockPosthog.capture).not.toHaveBeenCalled();
    expect(mockPosthog.opt_in_capturing).not.toHaveBeenCalled();
  });

  it('initializes opted out and defaults to the EU host', () => {
    process.env[KEY] = 'phc_test';
    const a = loadAnalytics();
    a.initPostHog();
    expect(mockPosthog.init).toHaveBeenCalledWith('phc_test', {
      api_host: 'https://eu.i.posthog.com',
      capture_pageview: false,
      opt_out_capturing_by_default: true,
    });
    expect(mockPosthog.opt_in_capturing).not.toHaveBeenCalled();
  });

  it('opts in at init when consent was already given', () => {
    process.env[KEY] = 'phc_test';
    localStorage.setItem('cookieConsent', 'accepted');
    loadAnalytics().initPostHog();
    expect(mockPosthog.opt_in_capturing).toHaveBeenCalledTimes(1);
  });

  it('opts in and captures the current page when the visitor accepts', () => {
    process.env[KEY] = 'phc_test';
    loadAnalytics().setAnalyticsConsent(true);
    expect(mockPosthog.opt_in_capturing).toHaveBeenCalledTimes(1);
    expect(mockPosthog.capture).toHaveBeenCalledWith('$pageview');
  });

  it('opts out when the visitor declines', () => {
    process.env[KEY] = 'phc_test';
    loadAnalytics().setAnalyticsConsent(false);
    expect(mockPosthog.opt_out_capturing).toHaveBeenCalledTimes(1);
    expect(mockPosthog.capture).not.toHaveBeenCalled();
  });

  it('captures a manual pageview', () => {
    process.env[KEY] = 'phc_test';
    loadAnalytics().capturePageview();
    expect(mockPosthog.capture).toHaveBeenCalledWith('$pageview');
  });
});
