// admin/src/components/AdminConfigNotice.jsx
import React from 'react';

/**
 * CarbonTally Admin — deployment configuration notice.
 *
 * H2 (P18 · PUBLIC-TRUTH-02).
 *
 * Rendered instead of the console when the deployed bundle has no Supabase
 * configuration. The previous behaviour was a blank `/admin` page (the client
 * threw during module evaluation), which is indistinguishable from "the site is
 * broken" and gives an operator nothing to act on.
 *
 * The notice names the missing BUILD SETTINGS only. It never echoes a value, a
 * key or any credential — a configuration screen must not become a disclosure
 * vector.
 *
 * No hooks are used so the component is also renderable server-side (used by its
 * test, which keeps the assertion dependency-free).
 */
const AdminConfigNotice = ({ missing = [], reason = null }) => {
  const handleRetry = () => {
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="w-full max-w-xl rounded-lg border border-gray-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-semibold text-gray-900">
          Admin console configuration required
        </h1>

        <p className="mt-3 text-sm leading-6 text-gray-600">
          This deployment of the CarbonTally Admin console was built without its
          Supabase connection settings, so it cannot start yet. This is a
          deployment configuration issue rather than a sign-in problem, and no
          data has been changed.
        </p>

        {reason && (
          <p className="mt-4 rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
            {reason}
          </p>
        )}

        {missing.length > 0 && (
          <div className="mt-5">
            <p className="text-sm font-medium text-gray-700">Missing build settings</p>
            <ul className="mt-2 list-inside list-disc font-mono text-sm text-gray-600">
              {missing.map((name) => (
                <li key={name}>{name}</li>
              ))}
            </ul>
          </div>
        )}

        <p className="mt-5 text-xs leading-5 text-gray-500">
          Configure these variables for the admin deployment, then rebuild. Only
          browser-safe values are permitted: the Supabase project URL and the
          publishable (anon) key. Never place a service-role key here.
        </p>

        <button
          type="button"
          onClick={handleRetry}
          className="mt-6 rounded bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          Retry
        </button>
      </div>
    </div>
  );
};

export default AdminConfigNotice;
