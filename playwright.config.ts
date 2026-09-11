import { defineConfig, devices } from '@playwright/test';

/**
 * CarbonTally P6-2F — browser E2E security acceptance.
 *
 * The suite targets an ISOLATED environment (PO-PHASE6-F-ENV-20260910):
 *   E2E_BASE_URL   the running frontend under test (default http://localhost:3000)
 *   E2E_*_EMAIL / E2E_*_PASSWORD   synthetic persona credentials
 *
 * Authenticated specs skip (never silently pass) when the environment is not
 * provided, so the harness can never claim acceptance for an untested area.
 * See tests/e2e/README.md.
 */
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';

export default defineConfig({
  // P6-2F specs live under tests/e2e (the default example spec is excluded).
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['list']],
  timeout: 30_000,
  expect: { timeout: 7_500 },
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    headless: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});

