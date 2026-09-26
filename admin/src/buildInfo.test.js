/**
 * H1 — the admin console must state the commit that produced the artefact
 * serving `/admin` (P18 · PUBLIC-TRUTH-02).
 */
import fs from 'fs';
import path from 'path';

import {
  BUILD_INFO_ENV_KEYS,
  BUILD_INFO_GLOBAL_KEY,
  UNKNOWN,
  installBuildInfo,
  resolveBuildInfo,
} from './buildInfo';

describe('admin build provenance (H1)', () => {
  it('uses the same browser global as the public site', () => {
    expect(BUILD_INFO_GLOBAL_KEY).toBe('__CARBONTALLY_BUILD_INFO__');
  });

  it('resolves the values inlined at build time', () => {
    expect(
      resolveBuildInfo({
        REACT_APP_BUILD_COMMIT: 'a'.repeat(40),
        REACT_APP_BUILD_BRANCH: 'p8-release-reconciled',
        REACT_APP_BUILD_TIME: '2026-09-26T10:00:00.000Z',
      })
    ).toEqual({
      commit: 'a'.repeat(40),
      branch: 'p8-release-reconciled',
      buildTime: '2026-09-26T10:00:00.000Z',
    });
  });

  it('reports UNKNOWN rather than an empty value when provenance is absent', () => {
    const info = resolveBuildInfo({ REACT_APP_BUILD_COMMIT: '', REACT_APP_BUILD_BRANCH: '  ' });

    expect(info.commit).toBe(UNKNOWN);
    expect(info.branch).toBe(UNKNOWN);
    expect(info.buildTime).toBe(UNKNOWN);
  });

  it('publishes the record on the supplied scope', () => {
    const scope = {};
    const info = installBuildInfo(scope);

    expect(scope[BUILD_INFO_GLOBAL_KEY]).toBe(info);
  });

  it('cannot break console startup', () => {
    expect(() => installBuildInfo(null)).not.toThrow();
  });

  it('carries no hard-coded sha and no credential', () => {
    const source = fs.readFileSync(path.join(__dirname, 'buildInfo.js'), 'utf8');

    expect(source).not.toMatch(/\b[0-9a-f]{40}\b/);
    expect(source).not.toMatch(/service_role|SERVICE_KEY|RESEND|PASSWORD|SECRET/i);
  });

  it('declares the same env key names as the public frontend', () => {
    expect(BUILD_INFO_ENV_KEYS).toEqual({
      commit: 'REACT_APP_BUILD_COMMIT',
      branch: 'REACT_APP_BUILD_BRANCH',
      buildTime: 'REACT_APP_BUILD_TIME',
    });
  });
});
