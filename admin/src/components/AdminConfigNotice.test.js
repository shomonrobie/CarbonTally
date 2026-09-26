/**
 * H2 — the configuration notice rendered in place of the admin console
 * (P18 · PUBLIC-TRUTH-02).
 *
 * Rendered with `react-dom/server` so the assertion needs no extra test
 * dependency (the admin CRA project does not install @testing-library).
 */
import { renderToStaticMarkup } from 'react-dom/server';

import AdminConfigNotice from './AdminConfigNotice';

describe('AdminConfigNotice (H2)', () => {
  it('explains that the deployment is not configured and names the missing settings', () => {
    const html = renderToStaticMarkup(
      <AdminConfigNotice missing={['REACT_APP_SUPABASE_URL', 'REACT_APP_SUPABASE_ANON_KEY']} />
    );

    expect(html).toContain('Admin console configuration required');
    expect(html).toContain('REACT_APP_SUPABASE_URL');
    expect(html).toContain('REACT_APP_SUPABASE_ANON_KEY');
    expect(html).toContain('deployment configuration issue');
  });

  it('surfaces an unusable-configuration reason without listing settings', () => {
    const html = renderToStaticMarkup(
      <AdminConfigNotice missing={[]} reason="The configured Supabase project URL could not be used." />
    );

    expect(html).toContain('The configured Supabase project URL could not be used.');
    expect(html).not.toContain('Missing build settings');
  });

  it('never renders a value, key or credential — only setting names', () => {
    const html = renderToStaticMarkup(
      <AdminConfigNotice missing={['REACT_APP_SUPABASE_ANON_KEY']} />
    );

    expect(html).not.toMatch(/eyJ|sbp_|service_role|Bearer /);
    expect(html).toContain('Never place a service-role key here');
  });

  it('always offers a way forward', () => {
    const html = renderToStaticMarkup(<AdminConfigNotice missing={['REACT_APP_SUPABASE_URL']} />);

    expect(html).toContain('Retry');
    expect(html).toContain('rebuild');
  });
});
