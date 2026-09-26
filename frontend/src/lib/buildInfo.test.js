/**
 * H1 — build provenance (P18 · PUBLIC-TRUTH-02).
 *
 * Verifies that a deployment can state which commit/branch/time produced the
 * artefact being served, that an unprovenanced build reports UNKNOWN instead of
 * silently claiming nothing, and that the generator and both CRA apps agree on
 * one contract.
 */
import fs from 'fs';
import os from 'os';
import path from 'path';

import {
  BUILD_INFO_ENV_KEYS,
  BUILD_INFO_GLOBAL_KEY,
  UNKNOWN,
  installBuildInfo,
  resolveBuildInfo,
} from './buildInfo';

// CommonJS module (the prebuild script must run before Babel/webpack exist).
const generator = require('../../../tools/generate_build_info.js');

const ADMIN_BUILD_INFO_SOURCE = path.resolve(__dirname, '../../../admin/src/buildInfo.js');
const ADMIN_ROOT = path.resolve(__dirname, '../../../admin');

describe('build provenance (H1)', () => {
  describe('published record', () => {
    it('uses the canonical browser global', () => {
      expect(BUILD_INFO_GLOBAL_KEY).toBe('__CARBONTALLY_BUILD_INFO__');
    });

    it('resolves the values inlined at build time', () => {
      const info = resolveBuildInfo({
        REACT_APP_BUILD_COMMIT: 'a'.repeat(40),
        REACT_APP_BUILD_BRANCH: 'p8-release-reconciled',
        REACT_APP_BUILD_TIME: '2026-09-26T10:00:00.000Z',
      });

      expect(info).toEqual({
        commit: 'a'.repeat(40),
        branch: 'p8-release-reconciled',
        buildTime: '2026-09-26T10:00:00.000Z',
      });
    });

    it('reports UNKNOWN — never an empty value — when a build had no provenance', () => {
      const info = resolveBuildInfo({});

      expect(info.commit).toBe(UNKNOWN);
      expect(info.branch).toBe(UNKNOWN);
      expect(info.buildTime).toBe(UNKNOWN);
    });

    it('treats blank and whitespace-only settings as missing', () => {
      const info = resolveBuildInfo({
        REACT_APP_BUILD_COMMIT: '   ',
        REACT_APP_BUILD_BRANCH: '',
        REACT_APP_BUILD_TIME: undefined,
      });

      expect(Object.values(info)).toEqual([UNKNOWN, UNKNOWN, UNKNOWN]);
    });

    it('trims surrounding whitespace from a real value', () => {
      expect(resolveBuildInfo({ REACT_APP_BUILD_COMMIT: ' abc123 ' }).commit).toBe('abc123');
    });

    it('publishes the record on the supplied scope', () => {
      const scope = {};
      const info = installBuildInfo(scope);

      expect(scope[BUILD_INFO_GLOBAL_KEY]).toBe(info);
      expect(info.commit).toBe(UNKNOWN); // no provenance in the test environment
    });

    it('can never break application startup', () => {
      expect(() => installBuildInfo(null)).not.toThrow();
      expect(installBuildInfo(null)).toEqual({
        commit: UNKNOWN,
        branch: UNKNOWN,
        buildTime: UNKNOWN,
      });
    });

    it('does not hard-code a commit sha or any credential in the shipped module', () => {
      const source = fs.readFileSync(path.join(__dirname, 'buildInfo.js'), 'utf8');

      expect(source).not.toMatch(/\b[0-9a-f]{40}\b/);
      expect(source).not.toMatch(/service_role|SERVICE_KEY|RESEND|PASSWORD|SECRET/i);
    });
  });

  describe('generator contract (tools/generate_build_info.js)', () => {
    const FIXED_NOW = new Date('2026-09-26T12:34:56.789Z');

    it('uses the hosting platform Git identity, falling back to generic Git variables', () => {
      expect(
        generator.resolveBuildInfo(
          { VERCEL_GIT_COMMIT_SHA: 'f'.repeat(40), VERCEL_GIT_COMMIT_REF: 'main' },
          FIXED_NOW
        )
      ).toEqual({ commit: 'f'.repeat(40), branch: 'main', buildTime: FIXED_NOW.toISOString() });

      expect(generator.resolveBuildInfo({ GIT_COMMIT: 'abc123' }, FIXED_NOW)).toEqual({
        commit: 'abc123',
        branch: UNKNOWN,
        buildTime: FIXED_NOW.toISOString(),
      });
    });

    it('reports UNKNOWN when the environment carries no Git identity', () => {
      expect(generator.resolveBuildInfo({}, FIXED_NOW)).toEqual({
        commit: UNKNOWN,
        branch: UNKNOWN,
        buildTime: FIXED_NOW.toISOString(),
      });
    });

    it('agrees with the frontend runtime on the env key names', () => {
      expect(generator.ENV_KEYS).toEqual({ ...BUILD_INFO_ENV_KEYS });
      expect(generator.UNKNOWN).toBe(UNKNOWN);
    });

    it('writes the provenance env file for every target app without any secret', () => {
      const root = fs.mkdtempSync(path.join(os.tmpdir(), 'ct-build-info-'));
      try {
        ['frontend', 'admin'].forEach((app) => fs.mkdirSync(path.join(root, app)));

        const result = generator.writeBuildInfo({
          targets: ['frontend', 'admin'],
          env: { VERCEL_GIT_COMMIT_SHA: 'b'.repeat(40), VERCEL_GIT_COMMIT_REF: 'release' },
          cwd: root,
          repoRoot: root,
          now: FIXED_NOW,
          log: () => {},
        });

        expect(result.files).toEqual([
          path.join(root, 'frontend', '.env.production.local'),
          path.join(root, 'admin', '.env.production.local'),
        ]);

        result.files.forEach((file) => {
          const contents = fs.readFileSync(file, 'utf8');
          expect(contents).toContain(`REACT_APP_BUILD_COMMIT=${'b'.repeat(40)}`);
          expect(contents).toContain('REACT_APP_BUILD_BRANCH=release');
          expect(contents).toContain(`REACT_APP_BUILD_TIME=${FIXED_NOW.toISOString()}`);
          expect(contents).not.toMatch(/service_role|SERVICE_KEY|RESEND|PASSWORD|SECRET/i);
        });
      } finally {
        fs.rmSync(root, { recursive: true, force: true });
      }
    });

    it('supports a dry run that reports provenance without writing', () => {
      const root = fs.mkdtempSync(path.join(os.tmpdir(), 'ct-build-info-dry-'));
      try {
        fs.mkdirSync(path.join(root, 'frontend'));

        const result = generator.writeBuildInfo({
          targets: ['frontend'],
          env: { VERCEL_GIT_COMMIT_SHA: 'c'.repeat(40) },
          cwd: root,
          repoRoot: root,
          now: FIXED_NOW,
          dryRun: true,
          log: () => {},
        });

        expect(result.info.commit).toBe('c'.repeat(40));
        expect(fs.existsSync(path.join(root, 'frontend', '.env.production.local'))).toBe(false);
      } finally {
        fs.rmSync(root, { recursive: true, force: true });
      }
    });

    it('fails loudly when a target app directory is missing', () => {
      const root = fs.mkdtempSync(path.join(os.tmpdir(), 'ct-build-info-missing-'));
      try {
        expect(() =>
          generator.writeBuildInfo({
            targets: ['not-an-app'],
            cwd: root,
            repoRoot: root,
            log: () => {},
          })
        ).toThrow(/does not exist/);
      } finally {
        fs.rmSync(root, { recursive: true, force: true });
      }
    });
  });

  describe('admin console contract (admin/src/buildInfo.js)', () => {
    it('keeps the same global key, env keys and sentinel as the frontend', () => {
      const source = fs.readFileSync(ADMIN_BUILD_INFO_SOURCE, 'utf8');

      expect(source).toContain(BUILD_INFO_GLOBAL_KEY);
      Object.values(BUILD_INFO_ENV_KEYS).forEach((key) => expect(source).toContain(key));
      expect(source).toContain(UNKNOWN);
    });

    it('is wired into the admin build so /admin also reports its provenance', () => {
      const adminPackage = JSON.parse(
        fs.readFileSync(path.join(ADMIN_ROOT, 'package.json'), 'utf8')
      );

      expect(adminPackage.scripts.prebuild).toBe('node ../tools/generate_build_info.js .');
      expect(fs.readFileSync(path.join(ADMIN_ROOT, 'src/index.js'), 'utf8')).toContain(
        'installBuildInfo()'
      );
    });
  });
});
