/**
 * P6-2F — browser route protection (UNAUTHENTICATED).
 *
 * The UI is never the security boundary, but the client must also fail closed:
 * an unauthenticated visitor who directly navigates to a protected route is
 * redirected to the sign-in surface rather than shown any workspace.
 *
 * This spec runs against any served CarbonTally frontend and needs no
 * credentials, so it is executable in the isolated environment immediately.
 */
import { test, expect } from '@playwright/test';

const PROTECTED_ROUTES = ['/consultant', '/ops', '/notifications', '/billing', '/messaging'];

test.describe('P6-2F — direct navigation is protected', () => {
  for (const route of PROTECTED_ROUTES) {
    test(`unauthenticated ${route} redirects to /login`, async ({ page }) => {
      await page.goto(route);
      await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
      // No workspace content leaks before the redirect.
      await expect(page.getByRole('heading', { name: /client item workspace|operations/i })).toHaveCount(0);
    });
  }

  test('the sign-in surface renders an email + password form', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[type="email"]').first()).toBeVisible();
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
  });

  test('a consultant item deep link is not reachable unauthenticated', async ({ page }) => {
    await page.goto('/consultant/items/synthetic-client/synthetic-item');
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
  });
});
