// admin/src/services/factorAdminService.js
//
// Admin factor governance client (PD-3).
//
// Factor management is an ADMIN authority on the backend: every call here goes
// through /api/admin/defra/* with the signed-in operator's bearer token, so the
// authorization decision is made server-side (a hidden or disabled button is
// never the security boundary — AGENTS.md §7/§44).
//
// The canonical factor store is `emission_factors`, addressed by the backend.
// The browser never talks to a factor table directly: direct table access would
// bypass the server-side admin check and depend on a schema the admin bundle
// does not own.
import { supabase } from '../supabaseClient';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const getToken = async () => {
  const { data } = supabase ? await supabase.auth.getSession() : { data: {} };
  return data?.session?.access_token || localStorage.getItem('access_token');
};

const request = async (path, options = {}) => {
  const token = await getToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body && body.detail) {
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch (error) {
      // Non-JSON error body: keep the status-based message.
    }
    throw new Error(detail);
  }

  if (response.status === 204) return null;
  return response.json();
};

/** List canonical factors (paged). Returns `{ data, count }` for the table. */
export const fetchFactors = async ({ year, activity, limit = 20, offset = 0 } = {}) => {
  const params = new URLSearchParams();
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  if (year && year !== 'all') params.set('year', String(year));
  if (activity) params.set('activity', activity);

  const payload = await request(`/api/admin/defra/factors?${params.toString()}`);
  return { data: payload.data || [], count: payload.total || 0 };
};

/** Available reporting years in the canonical factor set. */
export const fetchFactorYears = async () => {
  const payload = await request('/api/admin/defra/years');
  return payload.years || [];
};

/** Create one canonical factor. */
export const createFactor = async (factor) =>
  request('/api/admin/defra/factors', {
    method: 'POST',
    body: JSON.stringify(factor),
  });

/** Update one canonical factor. */
export const updateFactor = async (factorId, factor) =>
  request(`/api/admin/defra/factors/${factorId}`, {
    method: 'PUT',
    body: JSON.stringify(factor),
  });

/** Delete one canonical factor (the backend refuses to break provenance links). */
export const deleteFactor = async (factorId) =>
  request(`/api/admin/defra/factors/${factorId}`, { method: 'DELETE' });

/**
 * Bulk import factors, refreshing an existing canonical natural key when
 * `updateExisting` is set. The server owns duplicate detection and auditing.
 */
export const bulkUpsertFactors = async (factors, { updateExisting = false } = {}) =>
  request('/api/admin/defra/factors/bulk', {
    method: 'POST',
    body: JSON.stringify({ factors, update_existing: updateExisting }),
  });

export const factorAdminApiUrl = API_URL;
