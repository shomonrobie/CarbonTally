// frontend/src/v3/__tests__/ops-work-api.test.js
// WS4D — D38 4C API client wrappers: dual-target assign/reassign serialise
// EXACTLY ONE of assigned_to/entity_id and hit the authorised endpoint; the
// entity directory helper forwards an active-status filter.
jest.mock('../../supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: jest.fn(),
      getUser: jest.fn(),
    },
  },
}));

beforeEach(() => {
  const { supabase } = require('../../supabaseClient');
  supabase.auth.getSession.mockImplementation(async () => ({
    data: { session: { access_token: 'test-token' } },
  }));
  supabase.auth.getUser.mockImplementation(async () => ({
    data: { user: { id: 'u-admin' } },
  }));
});

describe('D38 4C ops work API wrappers', () => {
  const captureFetch = () => {
    const calls = [];
    global.fetch = jest.fn(async (url, options) => {
      calls.push({ url: String(url), options: options || {} });
      return { ok: true, json: async () => ({ ok: true }) };
    });
    return calls;
  };

  test('opsWorkAssignTarget sends only entity_id for a PE target to /work/assign', async () => {
    const calls = captureFetch();
    const { opsWorkAssignTarget } = require('../api');
    await opsWorkAssignTarget('item-x', { entity_id: 'e-alpha' });
    expect(calls).toHaveLength(1);
    expect(calls[0].url).toContain('/api/v3/ops/items/item-x/work/assign');
    expect(calls[0].options.method).toBe('POST');
    const body = JSON.parse(calls[0].options.body);
    expect(body.entity_id).toBe('e-alpha');
    expect(body.assigned_to).toBeUndefined();
  });

  test('opsWorkAssignTarget sends only assigned_to for an internal target', async () => {
    const calls = captureFetch();
    const { opsWorkAssignTarget } = require('../api');
    await opsWorkAssignTarget('item-x', { assigned_to: 'u-operator' });
    const body = JSON.parse(calls[0].options.body);
    expect(body.assigned_to).toBe('u-operator');
    expect(body.entity_id).toBeUndefined();
  });

  test('opsWorkReassignTarget hits /work/reassign with the new party', async () => {
    const calls = captureFetch();
    const { opsWorkReassignTarget } = require('../api');
    await opsWorkReassignTarget('item-x', { entity_id: 'e-beta' }, 'handover');
    expect(calls[0].url).toContain('/api/v3/ops/items/item-x/work/reassign');
    const body = JSON.parse(calls[0].options.body);
    expect(body.entity_id).toBe('e-beta');
    expect(body.reason).toBe('handover');
  });

  test('listProcessingEntities forwards an active status filter', async () => {
    const calls = captureFetch();
    const { listProcessingEntities } = require('../api');
    await listProcessingEntities(100, 0, 'active');
    expect(calls[0].url).toContain('/api/v3/ops/entities?');
    expect(calls[0].url).toContain('limit=100');
    expect(calls[0].url).toContain('status=active');
  });
});
