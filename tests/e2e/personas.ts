/**
 * P6-2F — representative synthetic browser personas.
 *
 * Personas are supplied through the isolated environment's variables so no
 * credential is ever hard-coded. When a persona is not configured, the specs
 * that need it SKIP (they never silently pass) — the harness must not claim
 * acceptance for an untested area.
 */
import { expect, Page } from '@playwright/test';

export interface Persona {
  email: string;
  password: string;
}

const env = (key: string): string => process.env[key] || '';

export const personas: Record<string, Persona> = {
  orgOwner: { email: env('E2E_ORG_OWNER_EMAIL'), password: env('E2E_ORG_OWNER_PASSWORD') },
  orgAdmin: { email: env('E2E_ORG_ADMIN_EMAIL'), password: env('E2E_ORG_ADMIN_PASSWORD') },
  orgMember: { email: env('E2E_ORG_MEMBER_EMAIL'), password: env('E2E_ORG_MEMBER_PASSWORD') },
  consultantA: { email: env('E2E_CONSULTANT_A_EMAIL'), password: env('E2E_CONSULTANT_A_PASSWORD') },
  consultantB: { email: env('E2E_CONSULTANT_B_EMAIL'), password: env('E2E_CONSULTANT_B_PASSWORD') },
  internalQc: { email: env('E2E_INTERNAL_QC_EMAIL'), password: env('E2E_INTERNAL_QC_PASSWORD') },
};

/** Synthetic ids created by the isolated environment (never production ids). */
export const ids = {
  clientA: env('E2E_CLIENT_A_ID'),
  clientB: env('E2E_CLIENT_B_ID'),
  itemA: env('E2E_ITEM_A_ID'),
  /** lifecycle-state items created by seed_lifecycle_fixtures.py */
  itemA2: env('E2E_ITEM_A2_ID'), // consultant_reviewed -> submit-to-QC visible
  itemA3: env('E2E_ITEM_A3_ID'), // ct_qc_approved      -> customer decision valid
  itemA6: env('E2E_ITEM_A6_ID'),
  itemA7: env('E2E_ITEM_A7_ID'),
};

/**
 * The isolated backend origin. API-boundary specs MUST target this, not the
 * CRA dev-server origin: the SPA answers ANY path with index.html (200), so a
 * relative request would never reach the server boundary at all.
 */
export function apiBase(): string {
  return process.env.E2E_API_URL || 'http://127.0.0.1:8051';
}

/** The real Supabase access token the signed-in browser session holds. */
export async function sessionToken(page: Page): Promise<string> {
  return page.evaluate(() => {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i) || '';
      if (!/-auth-token/.test(k)) continue;
      try {
        const v = JSON.parse(localStorage.getItem(k) || '{}');
        const t = v?.access_token || v?.currentSession?.access_token;
        if (t) return t as string;
      } catch {
        /* not a session entry */
      }
    }
    return '';
  });
}

/** Real authenticated call to the isolated API using the browser's own JWT. */
export async function apiCall(page: Page, method: string, path: string, data?: unknown) {
  const jwt = await sessionToken(page);
  return page.request.fetch(`${apiBase()}${path}`, {
    method,
    headers: jwt ? { Authorization: `Bearer ${jwt}` } : {},
    data: data as never,
  });
}

export function personaAvailable(persona: Persona): boolean {
  return Boolean(persona.email && persona.password);
}

export function requirePersona(persona: Persona): void {
  if (!personaAvailable(persona)) {
    throw new Error('Persona credentials are not configured in this environment.');
  }
}

/** Sign in through the real CarbonTally login surface. */
export async function login(page: Page, persona: Persona): Promise<void> {
  requirePersona(persona);
  await page.goto('/login');
  await page.locator('input[type="email"]').first().fill(persona.email);
  await page.locator('input[type="password"]').first().fill(persona.password);
  await page.getByRole('button', { name: /sign in|log in|login/i }).first().click();
  // Landed on an authenticated workspace.
  await expect(page).not.toHaveURL(/\/login/, { timeout: 15_000 });
}

/** Open a consultant item deep link (the IV-N6 route shape). */
export async function openConsultantItem(page: Page, clientId: string, itemId: string): Promise<void> {
  await page.goto(`/consultant/items/${encodeURIComponent(clientId)}/${encodeURIComponent(itemId)}`);
}
