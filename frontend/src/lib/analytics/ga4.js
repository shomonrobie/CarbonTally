// CarbonTally — Google Analytics 4 (GA4) loader.
//
// Google Analytics 4 is the only analytics provider implemented. It is
// configuration-driven: the enabled flag and measurement ID live in the
// platform Admin settings (Admin → Settings → Analytics & Integrations, backed
// by backend/api/v3_settings.py) and nothing is hard-coded here.
//
// GA4 loads only when ALL of the following hold:
//   1. an admin has enabled analytics,
//   2. the configured measurement ID is a valid GA4 ID (G-XXXXXXXXXX),
//   3. the deployment environment is an analytics environment, and
//   4. the visitor has accepted cookies through the existing consent banner.
//
// Any failure — a failed config request, an invalid ID, a blocked script — is
// swallowed: analytics is never a dependency for CarbonTally's own operation.
//
// This module sends NO CarbonTally business data and no custom events. It
// configures the standard GA4 page view only.

import { CONSENT_ACCEPTED, readCookieConsent } from '../consent';

const GTAG_ORIGIN = 'https://www.googletagmanager.com';

//: Marks the injected gtag.js tag, so loading is idempotent.
export const GA4_SCRIPT_ID = 'carbontally-ga4-gtag';

//: GA4 measurement IDs are 'G-' plus uppercase alphanumerics.
export const GA4_MEASUREMENT_ID_PATTERN = /^G-[A-Z0-9]{4,20}$/;

//: Bounded config request: analytics must never hang the page.
const CONFIG_REQUEST_TIMEOUT_MS = 5000;

/** Trim/uppercase a candidate measurement ID; null when it is effectively unset. */
export const normaliseGa4MeasurementId = (raw) => {
  if (typeof raw !== 'string') return null;
  const candidate = raw.trim().toUpperCase();
  return candidate === '' ? null : candidate;
};

/** True only for a well-formed GA4 measurement ID. */
export const isValidGa4MeasurementId = (raw) => {
  const candidate = normaliseGa4MeasurementId(raw);
  return candidate !== null && GA4_MEASUREMENT_ID_PATTERN.test(candidate);
};

/**
 * Whether this deployment may send analytics traffic.
 *
 * Production and non-production deployments can share the same Admin settings
 * row, so the deployment itself gates traffic: only an explicit
 * REACT_APP_ENVIRONMENT=production build is an analytics environment. An unset
 * or unrecognised value suppresses analytics (fail closed).
 */
export const isAnalyticsEnvironmentAllowed = (
  environment = process.env.REACT_APP_ENVIRONMENT,
) => String(environment == null ? '' : environment).trim().toLowerCase() === 'production';

/**
 * Pure load decision for a fetched configuration.
 *
 * @param {{enabled?: boolean, ga4_measurement_id?: string}|null} config
 * @param {{environment?: string, consent?: string}} [options]
 */
export const shouldLoadGa4 = (config, options = {}) => {
  if (!config || config.enabled !== true) return false;
  if (!isValidGa4MeasurementId(config.ga4_measurement_id)) return false;

  const environment = 'environment' in options ? options.environment : undefined;
  if (!isAnalyticsEnvironmentAllowed(environment)) return false;

  const consent = 'consent' in options ? options.consent : readCookieConsent();
  return consent === CONSENT_ACCEPTED;
};

/**
 * Fetch the Admin-configured GA4 settings from the V3 API.
 * Returns null on any failure — never throws.
 */
export const fetchGa4Config = async (options = {}) => {
  const apiUrl = 'apiUrl' in options ? options.apiUrl : process.env.REACT_APP_API_URL;
  const fetchImpl = options.fetchImpl || (typeof fetch === 'function' ? fetch : null);
  if (!apiUrl || !fetchImpl) return null;

  const controller = typeof AbortController === 'function' ? new AbortController() : null;
  const timer = controller
    ? setTimeout(() => controller.abort(), CONFIG_REQUEST_TIMEOUT_MS)
    : null;
  try {
    const response = await fetchImpl(`${apiUrl}/api/v3/settings/analytics`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: controller ? controller.signal : undefined,
    });
    if (!response || !response.ok) return null;
    const body = await response.json();
    const settings = body && body.settings;
    if (!settings || typeof settings !== 'object') return null;
    return {
      enabled: settings.enabled === true,
      ga4_measurement_id: normaliseGa4MeasurementId(settings.ga4_measurement_id),
    };
  } catch (error) {
    return null;
  } finally {
    if (timer) clearTimeout(timer);
  }
};

/**
 * Inject Google's gtag.js and configure GA4 for one measurement ID.
 *
 * Idempotent (a second call reuses the existing tag) and failure-tolerant: a
 * blocked or unavailable script must not affect the application.
 * Returns true when GA4 was loaded or was already loaded.
 */
export const loadGa4 = (measurementId) => {
  if (typeof document === 'undefined' || typeof window === 'undefined') return false;
  const id = normaliseGa4MeasurementId(measurementId);
  if (!isValidGa4MeasurementId(id)) return false;
  if (document.getElementById(GA4_SCRIPT_ID)) return true;

  try {
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function gtag() {
      window.dataLayer.push(arguments);
    };
    window.gtag('js', new Date());
    window.gtag('config', id);

    const script = document.createElement('script');
    script.id = GA4_SCRIPT_ID;
    script.async = true;
    script.src = `${GTAG_ORIGIN}/gtag/js?id=${encodeURIComponent(id)}`;
    document.head.appendChild(script);
    return true;
  } catch (error) {
    return false;
  }
};

/**
 * Full bootstrap: gate on environment and consent, read the Admin
 * configuration, then load GA4 when every condition holds.
 *
 * The environment and consent gates are checked before any network request, so
 * a visitor who has not accepted cookies is never contacted on behalf of
 * analytics.
 */
export const initGa4Analytics = async (options = {}) => {
  const environment = 'environment' in options ? options.environment : undefined;
  if (!isAnalyticsEnvironmentAllowed(environment)) return false;

  const consent = 'consent' in options ? options.consent : readCookieConsent();
  if (consent !== CONSENT_ACCEPTED) return false;

  const config = await fetchGa4Config(options);
  if (!shouldLoadGa4(config, { environment, consent })) return false;
  return loadGa4(config.ga4_measurement_id);
};
