/**
 * CarbonTally Admin — build provenance (H1 / P18-PUBLIC-TRUTH-02).
 *
 * Mirror of `frontend/src/lib/buildInfo.js`. The admin console is a separate
 * Create React App project and cannot import the frontend's `src/`, so the
 * contract is duplicated deliberately and kept small; the shared contract
 * (global key, env key names, UNKNOWN sentinel) is asserted by
 * `frontend/src/lib/buildInfo.test.js` so the two copies cannot drift silently.
 *
 * Values are captured at build time by `tools/generate_build_info.js` (wired to
 * the `prebuild` npm script) and published on
 * `window.__CARBONTALLY_BUILD_INFO__` at runtime.
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

/** Normalise a raw provenance record into the published shape. */
export const resolveBuildInfo = (env = process.env) => {
  const source = env || {};
  return Object.freeze({
    commit: normalise(source.REACT_APP_BUILD_COMMIT || source.commit) || UNKNOWN,
    branch: normalise(source.REACT_APP_BUILD_BRANCH || source.branch) || UNKNOWN,
    buildTime: normalise(source.REACT_APP_BUILD_TIME || source.buildTime) || UNKNOWN,
  });
};

/** Publish the build identity on `window` and return it. Never throws. */
export const installBuildInfo = (target) => {
  const info = resolveBuildInfo();
  const scope = target || (typeof window !== 'undefined' ? window : null);
  if (scope) {
    scope[BUILD_INFO_GLOBAL_KEY] = info;
  }
  return info;
};

export default installBuildInfo;
