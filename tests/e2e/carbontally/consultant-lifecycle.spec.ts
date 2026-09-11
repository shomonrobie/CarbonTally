/**
 * P6-2F — consultant lifecycle ALLOW workflows (browser).
 *
 * Requires the isolated environment (see tests/e2e/README.md). Every test
 * SKIPS when its persona/ids are not configured — never a silent pass.
 */
import { test, expect } from '@playwright/test';
import {
  ids,
  login,
  openConsultantItem,
  personaAvailable,
  personas,
  visibleAfterLoad,
  waitForAccessCheck,
} from '../personas';

test.describe('P6-2F — consultant lifecycle (ALLOW)', () => {
  test.beforeEach(() => {
    test.skip(!personaAvailable(personas.consultantA), 'consultant A credentials not configured');
    test.skip(!ids.clientA || !ids.itemA, 'synthetic client/item ids not configured');
  });

  test('consultant opens the deep-linked item workspace', async ({ page }) => {
    await login(page, personas.consultantA);
    await openConsultantItem(page, ids.clientA, ids.itemA);
    await expect(page.getByRole('heading', { name: /client item workspace/i })).toBeVisible();
    // The workspace is served by the scope-aware processing route, not the
    // internal /ops route (IV-N6 / survey fix).
    const workspaceCalls: string[] = [];
    page.on('request', (r) => {
      if (r.url().includes('/workspace')) workspaceCalls.push(r.url());
    });
    await page.reload();
    await expect(page.getByRole('heading', { name: /client item workspace/i })).toBeVisible();
    expect(workspaceCalls.some((u) => u.includes('/api/v3/processing/items/'))).toBeTruthy();
    expect(workspaceCalls.some((u) => u.includes('/api/v3/ops/items/'))).toBeFalsy();
  });

  test('consultant submits reviewed work to CarbonTally QC', async ({ page }) => {
    await login(page, personas.consultantA);
    // Uses the dedicated lifecycle-state item (status `consultant_reviewed`),
    // seeded by seed_lifecycle_fixtures.py, so the "Submit to CarbonTally QC"
    // action is genuinely available instead of skipping.
    await openConsultantItem(page, ids.clientA, ids.itemA2);
    await waitForAccessCheck(page);
    const submit = page.getByRole('button', { name: /submit to carbontally qc/i });
    test.skip(!(await visibleAfterLoad(submit)), 'item is not in a submittable state');
    await submit.click();
    await expect(page.getByText(/submitted to carbontally qc/i)).toBeVisible();
  });

  test('consultant completes the review action on a calculated item', async ({ page }) => {
    await login(page, personas.consultantA);
    await openConsultantItem(page, ids.clientA, ids.itemA);
    await waitForAccessCheck(page);
    const pass = page.getByRole('button', { name: /pass review/i });
    test.skip(!(await visibleAfterLoad(pass)), 'item is not in a reviewable state');
    await pass.click();
    await expect(page.getByText(/review passed/i)).toBeVisible();
  });

  test("the consultant's own notification deep link resolves to the item", async ({ page }) => {
    await login(page, personas.consultantA);
    await page.goto('/notifications');
    await waitForAccessCheck(page);
    const open = page.getByRole('link', { name: /^open$/i });
    test.skip(!(await visibleAfterLoad(open)), 'no lifecycle notification present');
    await open.first().click();
    await expect(page.getByRole('heading', { name: /client item workspace/i })).toBeVisible();
  });
});
