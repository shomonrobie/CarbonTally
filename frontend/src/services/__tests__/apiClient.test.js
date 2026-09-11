// frontend/src/services/__tests__/apiClient.test.js
// WS4 / ARCH-0003 — unit tests for the shared legacy API client.
// The supabase client is stubbed (no network / live Auth session required).

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: jest.fn() } },
}));

// CRA's jest config sets `resetMocks: true`, which wipes jest.fn()
// implementations before EVERY test — re-establish defaults here.
beforeEach(() => {
  const { supabase } = require('../../supabaseClient');
  supabase.auth.getSession.mockImplementation(async () => ({
    data: { session: { access_token: 'session-token-123' } },
  }));
  global.fetch = jest.fn();
});

import { apiRequest, getApiUrl, getToken } from '../apiClient';

describe('shared legacy API client (WS4)', () => {
  test('getApiUrl respects REACT_APP_API_URL when configured', () => {
    const prev = process.env.REACT_APP_API_URL;
    process.env.REACT_APP_API_URL = 'https://api.example.test';
    try {
      expect(getApiUrl()).toBe('https://api.example.test');
    } finally {
      process.env.REACT_APP_API_URL = prev;
    }
  });

  test('getApiUrl falls back to the legacy default when unset', () => {
    const prev = process.env.REACT_APP_API_URL;
    delete process.env.REACT_APP_API_URL;
    try {
      expect(getApiUrl()).toBe('http://localhost:8000');
    } finally {
      process.env.REACT_APP_API_URL = prev;
    }
  });

  test('getToken prefers the Supabase session token', async () => {
    const token = await getToken();
    expect(token).toBe('session-token-123');
  });

  test('getToken falls back to localStorage when no session', async () => {
    const { supabase } = require('../../supabaseClient');
    supabase.auth.getSession.mockImplementation(async () => ({ data: { session: null } }));
    localStorage.setItem('access_token', 'local-token-456');
    const token = await getToken();
    expect(token).toBe('local-token-456');
    localStorage.removeItem('access_token');
  });

  test('apiRequest attaches the bearer token and parses JSON', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => 'application/json' },
      json: async () => ({ facilities: [{ id: 'f1' }] }),
    });

    const result = await apiRequest('/api/organizations/org-a/facilities');

    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toContain('/api/organizations/org-a/facilities');
    expect(init.headers.Authorization).toBe('Bearer session-token-123');
    expect(result).toEqual({ ok: true, status: 200, data: { facilities: [{ id: 'f1' }] } });
  });

  test('apiRequest JSON-encodes object bodies with a content-type header', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      status: 201,
      headers: { get: () => 'application/json' },
      json: async () => ({ id: 'f2' }),
    });

    await apiRequest('/api/organizations/org-a/facilities', {
      method: 'POST',
      body: { name: 'HQ' },
    });

    const [, init] = global.fetch.mock.calls[0];
    expect(init.method).toBe('POST');
    expect(init.headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(init.body)).toEqual({ name: 'HQ' });
  });

  test('apiRequest does not throw on HTTP errors — exposes { ok:false, data }', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 403,
      headers: { get: () => 'application/json' },
      json: async () => ({ detail: 'Admin privileges required' }),
    });

    const result = await apiRequest('/api/v3/admin/review-queue');
    expect(result.ok).toBe(false);
    expect(result.status).toBe(403);
    expect(result.data.detail).toBe('Admin privileges required');
  });

  test('apiRequest passes FormData through without a content-type header', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => 'application/json' },
      json: async () => ({}),
    });

    const formData = new FormData();
    formData.append('file', 'x');

    await apiRequest('/api/upload', { method: 'POST', body: formData });

    const [, init] = global.fetch.mock.calls[0];
    expect(init.body).toBe(formData);
    expect(init.headers['Content-Type']).toBeUndefined();
  });
});
