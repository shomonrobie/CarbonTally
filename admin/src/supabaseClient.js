import { createClient } from '@supabase/supabase-js';

/**
 * CarbonTally Admin — Supabase client.
 *
 * H2 (P18 · PUBLIC-TRUTH-02): this module used to call
 * `createClient(undefined, undefined)` at import time when the deployment had no
 * Supabase settings. `createClient` throws ("supabaseUrl is required") during
 * module evaluation — i.e. before React can mount — so `/admin` rendered a blank
 * page with no explanation. Configuration problems must be REPORTED, never
 * thrown at import time: the UI now renders a controlled configuration notice.
 *
 * Only browser-safe values belong here. Create React App inlines REACT_APP_*
 * variables into the served bundle, so a publishable/anon key (which is designed
 * to be public and is constrained by RLS) is acceptable, while a service-role
 * key must NEVER be configured in these variables.
 */

/** Trimmed non-empty string, or null. */
const readConfig = (value) => {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed === '' ? null : trimmed;
};

const supabaseUrl = readConfig(process.env.REACT_APP_SUPABASE_URL);
const supabaseAnonKey = readConfig(process.env.REACT_APP_SUPABASE_ANON_KEY);

/** Names of the build settings that are absent — never their values. */
export const missingSupabaseConfig = [
  ['REACT_APP_SUPABASE_URL', supabaseUrl],
  ['REACT_APP_SUPABASE_ANON_KEY', supabaseAnonKey],
]
  .filter(([, value]) => value === null)
  .map(([name]) => name);

export const isSupabaseConfigured = missingSupabaseConfig.length === 0;

if (missingSupabaseConfig.length > 0) {
  console.error(
    `❌ CarbonTally Admin is missing Supabase configuration (${missingSupabaseConfig.join(', ')}). ` +
      'The console will show a configuration notice instead of the dashboard.'
  );
}

/**
 * The shared client, or `null` when this deployment cannot use Supabase.
 *
 * `createClient` validates its arguments and throws on a malformed project URL;
 * that throw used to happen at module scope and produced the blank `/admin`
 * page (H2). The client is therefore created defensively — a bad build setting
 * must become a reported state, never a fatal import error.
 */
let client = null;
let configurationError = null;

if (isSupabaseConfigured) {
  try {
    client = createClient(supabaseUrl, supabaseAnonKey);
  } catch (error) {
    configurationError =
      'The configured Supabase project URL could not be used by the Supabase client.';
    console.error(
      `❌ CarbonTally Admin Supabase client could not be created: ${error && error.message}`,
      'Check REACT_APP_SUPABASE_URL (it must be the project URL, e.g. https://<project>.supabase.co).'
    );
  }
}

/** True when this build can actually talk to Supabase (configured AND constructible). */
export const isSupabaseReady = Boolean(client);

/** Human-readable reason when configuration exists but the client is unusable. */
export const supabaseConfigurationError = configurationError;

export const supabase = client;

// Admin helper to check if user is admin or staff
export const isAdminOrStaff = async (userId) => {
  if (!userId) return false;
  // Fail closed when the deployment has no Supabase configuration (H2).
  if (!supabase) return { isStaff: false, role: 'user' };

  try {
    // Check if user is in staff_profiles table
    const { data: staffData, error: staffError } = await supabase
      .from('staff_profiles')
      .select('role')
      .eq('id', userId)
      .single();
    
    if (staffData) {
      return { isStaff: true, role: staffData.role };
    }
    
    // Check if user is an admin in any organization
    const { data: orgData, error: orgError } = await supabase
      .from('organization_members')
      .select('role')
      .eq('user_id', userId)
      .eq('role', 'admin')
      .limit(1);
    
    if (orgData && orgData.length > 0) {
      return { isStaff: false, role: 'admin' };
    }
    
    return { isStaff: false, role: 'user' };
  } catch (error) {
    console.error('Error checking admin status:', error);
    return { isStaff: false, role: 'user' };
  }
};