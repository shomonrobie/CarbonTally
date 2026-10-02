// admin/src/services/adminApi.js
//
// CT-FINAL-03 — shared admin→backend fetch helper.
//
// The admin bundle must not talk to protected tables through PostgREST. The
// FINAL-03 RLS remediation (supabase/migrations/20261028000000_ct_final_03_rls
// _security_remediation.sql) enables RLS with ZERO policies on the platform
// tables the legacy admin screens used to read directly (system_settings,
// waitlist, email_logs, beta_access_codes, review_audit_trail, …), so those
// screens now go through the admin-gated backend API with the signed-in
// operator's bearer token. Authorization is decided server-side; a hidden or
// disabled button is never the security boundary (AGENTS.md §7/§44).
//
// Mirrors the established pattern in `factorAdminService.js`.
import { supabase } from '../supabaseClient';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const getToken = async () => {
  const { data } = supabase ? await supabase.auth.getSession() : { data: {} };
  return data?.session?.access_token || localStorage.getItem('access_token');
};

/**
 * Perform an authenticated admin API request.
 *
 * @param {string} path    API path, e.g. '/api/v3/settings/upload-policy'
 * @param {object} options fetch options (method, body, headers, …)
 * @returns {Promise<any>} parsed JSON body
 * @throws {Error} with `.status` and `.raw` set when the backend refuses
 */
export const adminFetch = async (path, options = {}) => {
  const token = await getToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  let body = null;
  try {
    body = await response.json();
  } catch (_e) {
    body = null;
  }

  if (!response.ok) {
    const raw =
      (body && (body.detail || body.error?.message)) ||
      `Request failed (${response.status})`;
    const error = new Error(
      typeof raw === 'string' ? raw : JSON.stringify(raw)
    );
    error.status = response.status;
    error.raw = raw;
    throw error;
  }

  return body;
};

export default adminFetch;
