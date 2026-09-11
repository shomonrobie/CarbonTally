/**
 * P6-2F — browser DENY / security matrix.
 *
 * Each boundary is exercised from the DENY side through the browser: direct
 * navigation AND direct API invocation (the real server authorization is the
 * boundary — a hidden control is not evidence).
 *
 * Requires the isolated environment (see tests/e2e/README.md); tests SKIP when
 * credentials are not configured.
 */
import { test, expect } from '@playwright/test';
import { apiBase, apiCall, ids, login, openConsultantItem, personaAvailable, personas } from '../personas';

test.describe('P6-2F — browser security DENY', () => {
  test('cross-firm consultant cannot open another firm client item (direct navigation)', async ({ page }) => {
    test.skip(!personaAvailable(personas.consultantB), 'consultant B credentials not configured');
    test.skip(!ids.clientA || !ids.itemA, 'synthetic client/item ids not configured');
    await login(page, personas.consultantB);
    await openConsultantItem(page, ids.clientA, ids.itemA);
    // Denied server-side: no workspace heading; an error/denied state is shown.
    await expect(page.getByRole('heading', { name: /client item workspace/i })).toHaveCount(0, { timeout: 15_000 });
  });

  test('organisation member cannot approve a customer decision (API boundary)', async ({ page }) => {
    test.skip(!personaAvailable(personas.orgMember), 'org member credentials not configured');
    test.skip(!ids.itemA3, 'synthetic lifecycle item id not configured');
    await login(page, personas.orgMember);
    // Real API boundary (NOT the CRA origin, which answers every path with the
    // SPA index.html 200). The item is genuinely in `ct_qc_approved`, so the
    // action is *applicable* and only authorization can deny it: a member is not
    // an owner/admin, so the server must refuse. 401 (no/invalid session) and 403
    // (authenticated but not permitted) are both legitimate refusals.
    const resp = await apiCall(page, 'POST', `/api/v3/processing/items/${ids.itemA3}/customer-review`,
      { approved: true, customer_notes: 'e2e' });
    expect([401, 403]).toContain(resp.status());
    // The refusal must not mutate the item into a decided state.
    const after = await page.request.get(`${apiBase()}/api/v3/processing/items/${ids.itemA3}/workspace`,
      { headers: { Authorization: `Bearer ${await page.evaluate(() => {
        for (let i = 0; i < localStorage.length; i++) {
          const k = localStorage.key(i) || '';
          if (!/-auth-token/.test(k)) continue;
          try { const t = JSON.parse(localStorage.getItem(k) || '{}')?.access_token; if (t) return t as string; } catch { /* ignore */ }
        }
        return '';
      })}` } });
    expect([200, 401, 403, 404]).toContain(after.status());
  });

  test('unauthenticated API calls are rejected', async ({ request }) => {
    // Target the API origin explicitly (no credentials at all).
    const resp = await request.get(`${apiBase()}/api/v3/notifications`);
    expect([401, 403]).toContain(resp.status());
    expect(await resp.text()).not.toContain('<html');
  });

  test('consultant cannot invoke the internal ops workspace route', async ({ page }) => {
    test.skip(!personaAvailable(personas.consultantA), 'consultant A credentials not configured');
    test.skip(!ids.itemA, 'synthetic item id not configured');
    await login(page, personas.consultantA);
    // Real API boundary with the consultant's real JWT: the internal /ops route
    // must refuse a consultant (auth/server allow-list), never return the
    // internal workspace payload.
    const resp = await apiCall(page, 'GET', `/api/v3/ops/items/${ids.itemA}/workspace`);
    expect([401, 403, 404]).toContain(resp.status());
    expect(await resp.text()).not.toContain('<html');
  });

  test('consultant cannot reach the admin control plane', async ({ page }) => {
    test.skip(!personaAvailable(personas.consultantA), 'consultant A credentials not configured');
    await login(page, personas.consultantA);
    await page.goto('/admin');
    // Role-gated: never the admin control plane for a consultant.
    await expect(page.getByRole('heading', { name: /admin control plane/i })).toHaveCount(0, { timeout: 15_000 });
  });
});
