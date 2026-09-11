// frontend/src/services/apiClient.js
// WS4 / ARCH-0003 — shared API client for the legacy (non-V3) frontend surface.
//
// Controlled convergence toward the V3 client architecture (frontend/src/v3/api.js):
// the V3 surface funnels all HTTP through `v3Fetch`; the legacy surface used to
// re-declare `API_URL` + a token helper + ad-hoc `fetch`/`axios` calls in every
// component. This module centralises that plumbing for the legacy surface so
// header propagation, token handling and base-URL resolution are consistent
// across legacy components.
//
// `apiRequest` deliberately mirrors the shape the legacy call-sites already use
// (`{ ok, status, data }`) so migration preserves existing behaviour exactly:
// the caller still checks `response.ok` and reads `response.data` (already
// parsed JSON) or the server `detail` message on error. It throws only on
// network-level failures, matching the previous `fetch` behaviour.

import { supabase } from '../supabaseClient';

const DEFAULT_API_URL = 'http://localhost:8000';

/** Resolve the API base URL once, consistently (no per-component constants). */
export function getApiUrl() {
  return process.env.REACT_APP_API_URL || DEFAULT_API_URL;
}

/** Resolve the current bearer token from the Supabase session or legacy storage. */
export async function getToken() {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || localStorage.getItem('access_token') || null;
}

/**
 * Perform a JSON-aware API request with a consistent Authorization header.
 *
 * @param {string} path  API path (e.g. '/api/organizations/{org}/assets').
 * @param {Object} [options] fetch options ({ method, body, headers, ... }).
 *   `body` may be a plain object (JSON-encoded automatically), a string, or
 *   FormData (sent as-is, no Content-Type set).
 * @returns {Promise<{ok: boolean, status: number, data: any|null}>}
 */
export async function apiRequest(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = await getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let body = options.body;
  if (
    body !== undefined &&
    body !== null &&
    typeof body !== 'string' &&
    !(body instanceof FormData)
  ) {
    if (!headers['Content-Type']) headers['Content-Type'] = 'application/json';
    body = JSON.stringify(body);
  }

  const response = await fetch(`${getApiUrl()}${path}`, {
    ...options,
    headers,
    body,
  });

  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json')
    ? await response.json().catch(() => null)
    : null;

  return { ok: response.ok, status: response.status, data };
}
