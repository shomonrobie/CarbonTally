#!/usr/bin/env node
/**
 * CarbonTally — build provenance generator.
 *
 * P18 · PUBLIC-TRUTH-02 · finding H1 (frontend/admin build provenance).
 *
 * WHY THIS EXISTS
 * ---------------
 * The deployed frontend bundle previously carried no record of the commit that
 * produced it, so "what is actually deployed on carbontally.co.uk?" could only
 * be answered by trusting the hosting dashboard. Deployment truth is a
 * verification requirement, not a convenience.
 *
 * Create React App inlines ONLY `REACT_APP_*` variables into the bundle at build
 * time, so the deployment's Git identity (supplied by the hosting platform as
 * `VERCEL_GIT_COMMIT_SHA` / `VERCEL_GIT_COMMIT_REF`) has to be translated into
 * `REACT_APP_BUILD_*` before `react-scripts build` runs. That is what this
 * script does: it writes `<app>/.env.production.local` for each CRA app.
 *
 * `.env.production.local` is the highest-priority CRA production env file and is
 * git-ignored (root `.gitignore` covers `.env*`; `frontend/.gitignore` lists it
 * explicitly), so the generated file can never be committed by accident.
 *
 * The React-side counterpart of this contract lives in
 * `frontend/src/lib/buildInfo.js` and `admin/src/buildInfo.js`; those modules
 * publish the values on `window.__CARBONTALLY_BUILD_INFO__`.
 *
 * USAGE
 * -----
 *   node tools/generate_build_info.js                 # frontend + admin
 *   node tools/generate_build_info.js frontend        # one app
 *   node tools/generate_build_info.js frontend --dry-run
 *
 * Each app invokes it from its own `prebuild` npm script, so `npm run build`
 * always produces provenance without any extra operator step.
 *
 * NO SECRETS: only public deployment metadata (commit SHA, branch, timestamp)
 * is ever written.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..');
const BUILD_INFO_FILENAME = '.env.production.local';
const UNKNOWN = 'UNKNOWN';
const DEFAULT_TARGETS = ['frontend', 'admin'];

// Canonical contract shared with frontend/src/lib/buildInfo.js and
// admin/src/buildInfo.js (asserted by frontend/src/lib/buildInfo.test.js).
const ENV_KEYS = {
  commit: 'REACT_APP_BUILD_COMMIT',
  branch: 'REACT_APP_BUILD_BRANCH',
  buildTime: 'REACT_APP_BUILD_TIME',
};

/** Trimmed non-empty string, or null. Never returns '' so "missing" stays detectable. */
const normalise = (value) => {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed === '' ? null : trimmed;
};

/**
 * Resolve the deployment's build identity.
 *
 * `VERCEL_GIT_COMMIT_SHA` / `VERCEL_GIT_COMMIT_REF` are exported by the Vercel
 * build environment; the `GIT_*` names allow the same generator to run under any
 * other CI provider. Anything unavailable is reported as UNKNOWN — never as an
 * empty string — so evidence can distinguish "unknown" from "missing field".
 */
const resolveBuildInfo = (env = process.env, now = new Date()) => ({
  commit: normalise(env && env.VERCEL_GIT_COMMIT_SHA) || normalise(env && env.GIT_COMMIT) || UNKNOWN,
  branch: normalise(env && env.VERCEL_GIT_COMMIT_REF) || normalise(env && env.GIT_BRANCH) || UNKNOWN,
  buildTime: (now instanceof Date && !Number.isNaN(now.getTime()) ? now : new Date()).toISOString(),
});

/** Serialise the provenance record as a CRA production env file. */
const toEnvFileContents = (info) =>
  [
    '# ---------------------------------------------------------------------------',
    '# GENERATED FILE — CarbonTally build provenance (H1 / P18-PUBLIC-TRUTH-02).',
    '# Written by tools/generate_build_info.js immediately before `react-scripts build`.',
    '# Do not edit by hand and do not commit: .gitignore covers .env.production.local.',
    '# Public deployment metadata only — no credentials, keys or tokens belong here.',
    '# ---------------------------------------------------------------------------',
    `${ENV_KEYS.commit}=${info.commit}`,
    `${ENV_KEYS.branch}=${info.branch}`,
    `${ENV_KEYS.buildTime}=${info.buildTime}`,
    '',
  ].join('\n');

/**
 * Write the provenance env file for each target app.
 *
 * Throws on a missing target directory: a build that silently loses its
 * provenance would defeat the purpose of the finding.
 */
const writeBuildInfo = ({
  targets = DEFAULT_TARGETS,
  env = process.env,
  cwd = process.cwd(),
  repoRoot = REPO_ROOT,
  now = new Date(),
  dryRun = false,
  log = console.log,
} = {}) => {
  const info = resolveBuildInfo(env, now);
  const contents = toEnvFileContents(info);
  const files = [];

  targets.forEach((target) => {
    // Relative targets resolve against the caller's working directory, which for
    // a `prebuild` npm script is the app being built (`node ../tools/generate_build_info.js .`).
    const appDir = path.isAbsolute(target) ? target : path.resolve(cwd, target);
    if (!fs.existsSync(appDir)) {
      throw new Error(`target app directory does not exist: ${appDir}`);
    }
    const file = path.join(appDir, BUILD_INFO_FILENAME);
    if (!dryRun) {
      fs.writeFileSync(file, contents, 'utf8');
    }
    files.push(file);
    log(
      `build-info: ${dryRun ? 'would write' : 'wrote'} ${path.relative(repoRoot, file)} ` +
        `(commit=${info.commit} branch=${info.branch})`
    );
  });

  return { info, contents, files };
};

const USAGE = `Usage: node tools/generate_build_info.js [app ...] [--dry-run]

  app         CRA app directory relative to the repository root
              (default: ${DEFAULT_TARGETS.join(' ')})
  --dry-run   report the provenance without writing any file

Resolves commit/branch from VERCEL_GIT_COMMIT_SHA / VERCEL_GIT_COMMIT_REF
(GIT_COMMIT / GIT_BRANCH accepted as a fallback) and writes
${BUILD_INFO_FILENAME} for each app.`;

const parseArgs = (argv) => {
  const targets = [];
  let dryRun = false;

  argv.forEach((arg) => {
    if (arg === '--dry-run') {
      dryRun = true;
    } else if (arg === '--help' || arg === '-h') {
      console.log(USAGE);
      process.exit(0);
    } else if (arg.startsWith('-')) {
      throw new Error(`unknown option: ${arg}`);
    } else {
      targets.push(arg);
    }
  });

  return { targets: targets.length > 0 ? targets : DEFAULT_TARGETS, dryRun };
};

if (require.main === module) {
  try {
    const { targets, dryRun } = parseArgs(process.argv.slice(2));
    writeBuildInfo({ targets, dryRun });
  } catch (error) {
    console.error(`build-info: FAILED — ${error.message}`);
    process.exit(1);
  }
}

module.exports = {
  BUILD_INFO_FILENAME,
  DEFAULT_TARGETS,
  ENV_KEYS,
  REPO_ROOT,
  UNKNOWN,
  normalise,
  parseArgs,
  resolveBuildInfo,
  toEnvFileContents,
  writeBuildInfo,
};
