// frontend/src/lib/authErrors.js
//
// CarbonTally authentication error classification.
//
// Purpose: distinguish AUTH SERVICE UNAVAILABLE (a temporary infrastructure or
// configuration problem) from INVALID CREDENTIALS, UNAUTHORIZED, FORBIDDEN and
// UNKNOWN APPLICATION ERROR, so that:
//   * an outage is presented as a branded, reassuring notice, and
//   * authorisation/security failures are NEVER masked as outages.
//
// This module is read-only: it classifies errors produced elsewhere.

export const AUTH_SERVICE_UNAVAILABLE = 'AUTH_SERVICE_UNAVAILABLE';
export const INVALID_CREDENTIALS = 'INVALID_CREDENTIALS';
export const UNAUTHORIZED = 'UNAUTHORIZED';
export const FORBIDDEN = 'FORBIDDEN';
export const UNKNOWN_APPLICATION_ERROR = 'UNKNOWN_APPLICATION_ERROR';

// Supabase/GoTrue error codes and statuses that indicate the auth service itself
// could not serve the request (as opposed to rejecting the credentials).
const UNAVAILABLE_STATUSES = [0, 429, 500, 502, 503, 504];
const UNAVAILABLE_CODES = [
  'request_timeout',
  'timeout',
  'over_request_rate_limit',
  'too_many_requests',
  'unexpected_failure',
  'internal_error',
  'service_unavailable',
  'network_error',
  'auth_timeout',
];

const UNAVAILABLE_TEXT = [
  'failed to fetch',
  'networkerror',
  'network error',
  'load failed',
  'timeout',
  'timed out',
  'econnrefused',
  'connection refused',
  'fetch failed',
  'supabase url is required',
  'supabasekey is required',
  'invalid url',
];

const CREDENTIAL_TEXT = [
  'invalid login credentials',
  'invalid credentials',
  'invalid password',
  'wrong password',
  'user already registered',
];

const UNAUTHORIZED_TEXT = ['not authenticated', 'no session', 'jwt', 'session missing', 'session not found'];
const FORBIDDEN_TEXT = ['forbidden', 'not authorized', 'not authorised', 'permission denied', 'insufficient'];

function textOf(err) {
  const parts = [
    err && err.message,
    err && err.error_description,
    err && err.msg,
    err && err.error,
    err && err.code,
    typeof err === 'string' ? err : '',
  ];
  return parts.filter(Boolean).join(' ').toLowerCase();
}

/**
 * Classify an authentication-related error.
 * @param {any} err error thrown by a Supabase call, fetch, or workspace resolver
 * @returns {string} one of the exported classification constants
 */
export function classifyAuthError(err) {
  if (!err) return UNKNOWN_APPLICATION_ERROR;

  const status = Number(err.status || err.statusCode || 0);
  const code = String(err.code || '').toLowerCase();
  const text = textOf(err);

  // 1. Auth service / infrastructure unavailability (checked first so that a
  //    timeout is never mistaken for a credential rejection).
  if (UNAVAILABLE_STATUSES.includes(status) && status !== 400 && status !== 401 && status !== 403) {
    return AUTH_SERVICE_UNAVAILABLE;
  }
  if (code && UNAVAILABLE_CODES.includes(code)) return AUTH_SERVICE_UNAVAILABLE;
  if (UNAVAILABLE_TEXT.some((t) => text.includes(t))) return AUTH_SERVICE_UNAVAILABLE;

  // 2. Credentials rejected by a reachable auth service.
  if (CREDENTIAL_TEXT.some((t) => text.includes(t))) return INVALID_CREDENTIALS;

  // 3. Authenticated-but-not-permitted states (must NOT be shown as outages).
  if (status === 403 || FORBIDDEN_TEXT.some((t) => text.includes(t))) return FORBIDDEN;
  if (status === 401 || UNAUTHORIZED_TEXT.some((t) => text.includes(t))) return UNAUTHORIZED;

  return UNKNOWN_APPLICATION_ERROR;
}

export function isAuthServiceUnavailable(err) {
  return classifyAuthError(err) === AUTH_SERVICE_UNAVAILABLE;
}
