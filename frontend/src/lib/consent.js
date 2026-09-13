// CarbonTally cookie-consent contract.
//
// The existing banner (src/CookieBanner.jsx) remains the ONLY place a visitor
// makes a consent choice; this module is the shared contract other features
// read. Analytics integrations must respect this record rather than introduce
// a second, parallel consent mechanism.

export const COOKIE_CONSENT_KEY = 'cookieConsent';
export const CONSENT_ACCEPTED = 'accepted';
export const CONSENT_DECLINED = 'declined';

// Dispatched on the window whenever the stored choice changes, so long-lived
// consumers (analytics) react to a choice made after the app loaded.
export const CONSENT_CHANGE_EVENT = 'carbontally:cookie-consent';

/** Read the visitor's stored choice: 'accepted', 'declined' or null. */
export const readCookieConsent = () => {
  try {
    return window.localStorage.getItem(COOKIE_CONSENT_KEY);
  } catch (error) {
    // A blocked storage API is treated as "no recorded choice" (fail closed).
    return null;
  }
};

/** Persist the visitor's choice and notify consent consumers. */
export const recordCookieConsent = (value) => {
  try {
    window.localStorage.setItem(COOKIE_CONSENT_KEY, value);
  } catch (error) {
    // Storage may be unavailable; the choice still applies to this session.
  }
  try {
    window.dispatchEvent(new Event(CONSENT_CHANGE_EVENT));
  } catch (error) {
    // Best-effort notification: the persisted value stays authoritative.
  }
};

/**
 * Subscribe to consent changes (this tab's own change and other tabs').
 * Returns an unsubscribe function.
 */
export const subscribeToConsentChanges = (listener) => {
  if (typeof window === 'undefined' || typeof window.addEventListener !== 'function') {
    return () => {};
  }
  const onStorage = (event) => {
    if (event && event.key === COOKIE_CONSENT_KEY) {
      listener(readCookieConsent());
    }
  };
  const onLocalChange = () => listener(readCookieConsent());
  window.addEventListener('storage', onStorage);
  window.addEventListener(CONSENT_CHANGE_EVENT, onLocalChange);
  return () => {
    window.removeEventListener('storage', onStorage);
    window.removeEventListener(CONSENT_CHANGE_EVENT, onLocalChange);
  };
};
