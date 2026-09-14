import posthog from 'posthog-js';

// PostHog product analytics for the public CarbonTally site.
//
// The SDK loads only when REACT_APP_PUBLIC_POSTHOG_KEY is set, so builds
// without the key stay inert. Capture starts opted out and turns on only
// after the visitor accepts cookies in the CookieBanner. The app uses
// BrowserRouter, so $pageview is captured by hand on each route change
// (see PostHogPageview in App.js) instead of by the SDK.

const POSTHOG_KEY = process.env.REACT_APP_PUBLIC_POSTHOG_KEY;
const POSTHOG_HOST = process.env.REACT_APP_PUBLIC_POSTHOG_HOST || 'https://eu.i.posthog.com';
const CONSENT_KEY = 'cookieConsent';

export const isAnalyticsEnabled = Boolean(POSTHOG_KEY);

export function initPostHog() {
  if (!isAnalyticsEnabled) return;

  posthog.init(POSTHOG_KEY, {
    api_host: POSTHOG_HOST,
    capture_pageview: false,
    opt_out_capturing_by_default: true,
  });

  if (localStorage.getItem(CONSENT_KEY) === 'accepted') {
    posthog.opt_in_capturing();
  }
}

export function setAnalyticsConsent(accepted) {
  if (!isAnalyticsEnabled) return;

  if (accepted) {
    posthog.opt_in_capturing();
    posthog.capture('$pageview');
  } else {
    posthog.opt_out_capturing();
  }
}

export function capturePageview() {
  if (!isAnalyticsEnabled) return;
  posthog.capture('$pageview');
}
