/**
 * CarbonTally — frontend build provenance (H1 / P18-PUBLIC-TRUTH-02).
 *
 * The public marketing site and the authenticated application ship as one
 * bundle, so "which commit produced the artefact a visitor is looking at?" is a
 * deployment-integrity question that must be answerable without dashboard
 * access or a shell on the host.
 *
 * Provenance is captured at BUILD time by `tools/generate_build_info.js`, which
 * writes `.env.production.local` (Create React App inlines only `REACT_APP_*`
 * variables). At runtime the values are published on
 * `window.__CARBONTALLY_BUILD_INFO__` so a release check, a verification script
 * or a developer console can confirm exactly what is deployed.
 *
 * The global is never missing: a build that could not obtain Git provenance
 * reports `UNKNOWN`, so "unknown commit" is distinguishable from "field absent".
 *
 * The same contract is implemented for the admin console in
 * `admin/src/buildInfo.js` (the two CRA apps cannot share `src/`); the shared
 * contract is asserted by `buildInfo.test.js`.
 */

export const BUILD_INFO_GLOBAL_KEY = '__CARBONTALLY_BUILD_INFO__';

export const BUILD_INFO_ENV_KEYS = Object.freeze({
  commit: 'REACT_APP_BUILD_COMMIT',
  branch: 'REACT_APP_BUILD_BRANCH',
  buildTime: 'REACT_APP_BUILD_TIME',
});

/** Sentinel used whenever a provenance value was unavailable at build time. */
export const UNKNOWN = 'UNKNOWN';

/** Trimmed non-empty string, or null. Never returns '' so "missing" stays detectable. */
const normalise = (value) => {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed === '' ? null : trimmed;
};

/**
 * Normalise a raw provenance record into the published shape.
 *
 * Accepts raw env-style input (`{ REACT_APP_BUILD_COMMIT }`) or already-named
 * input (`{ commit }`) so it is usable from both the runtime and tests.
 */
export const resolveBuildInfo = (env = process.env) => {
  const source = env || {};
  return Object.freeze({
    commit: normalise(source.REACT_APP_BUILD_COMMIT || source.commit) || UNKNOWN,
    branch: normalise(source.REACT_APP_BUILD_BRANCH || source.branch) || UNKNOWN,
    buildTime: normalise(source.REACT_APP_BUILD_TIME || source.buildTime) || UNKNOWN,
  });
};

/**
 * Publish the build identity on `window` and return it.
 *
 * Deliberately defensive: provenance must never be able to break application
 * startup (a missing global is a reporting gap, not a fatal error).
 */
export const installBuildInfo = (target) => {
  const info = resolveBuildInfo();
  const scope = target || (typeof window !== 'undefined' ? window : null);
  if (scope) {
    scope[BUILD_INFO_GLOBAL_KEY] = info;
  }
  return info;
};

export default installBuildInfo;
