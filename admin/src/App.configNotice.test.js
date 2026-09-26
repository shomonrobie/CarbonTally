/**
 * H2 — the real admin entry component must render an explanation, never a blank
 * page, when the deployment has no usable Supabase configuration
 * (P18 · PUBLIC-TRUTH-02).
 *
 * This is the regression test for the reported symptom itself: `/admin` was
 * blank because the module-scope `createClient(undefined, undefined)` threw
 * before React could mount.
 */
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

// Pre-existing issue (not introduced here): ManualReviewQueue.js uses
// `import.meta.env.VITE_API_URL`, which Jest cannot parse. It is irrelevant to
// this gate (the configuration notice renders before any route), so it is
// replaced with a stub to keep the regression test focused.
jest.mock('./pages/admin/ManualReviewQueue', () => () => null);

const ENV_KEYS = ['REACT_APP_SUPABASE_URL', 'REACT_APP_SUPABASE_ANON_KEY'];

describe('admin console startup without configuration (H2)', () => {
  let App;
  let consoleError;

  beforeAll(() => {
    ENV_KEYS.forEach((name) => delete process.env[name]);
    jest.resetModules();
    consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    // eslint-disable-next-line global-require
    App = require('./App').default;
  });

  afterAll(() => {
    consoleError.mockRestore();
  });

  it('mounts the configuration notice instead of leaving the page blank', () => {
    let html;

    expect(() => {
      html = renderToStaticMarkup(React.createElement(App));
    }).not.toThrow();

    expect(html).not.toBe('');
    expect(html).toContain('Admin console configuration required');
  });

  it('names the settings an operator must add, so the failure is actionable', () => {
    const html = renderToStaticMarkup(React.createElement(App));

    expect(html).toContain('REACT_APP_SUPABASE_URL');
    expect(html).toContain('REACT_APP_SUPABASE_ANON_KEY');
    expect(html).toContain('Missing build settings');
  });

  it('does not render any authenticated console surface', () => {
    const html = renderToStaticMarkup(React.createElement(App));

    expect(html).not.toContain('Manual Review');
    expect(html).not.toContain('Log Viewer');
    expect(html).not.toContain('Loading Access Panel');
  });
});
