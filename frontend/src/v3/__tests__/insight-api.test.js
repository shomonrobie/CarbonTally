// frontend/src/v3/__tests__/insight-api.test.js
// I6 — the Insight client functions must target the closed I1–I4 backend
// contracts, with the organization scope always supplied by the caller and
// never implied client-side. No new endpoint is invented for I6.
jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: jest.fn(), getUser: jest.fn() } },
}));

// CRA's jest config sets `resetMocks: true`, so defaults are re-established here.
beforeEach(() => {
  const { supabase } = require('../../supabaseClient');
  supabase.auth.getSession.mockImplementation(async () => ({ data: { session: null } }));
  supabase.auth.getUser.mockImplementation(async () => ({ data: { user: null } }));
  global.fetch = jest.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ({}),
  }));
});

afterEach(() => {
  delete global.fetch;
});

const lastCall = () => global.fetch.mock.calls[global.fetch.mock.calls.length - 1];
const lastBody = () => JSON.parse(lastCall()[1].body);

describe('Insight API client (I6)', () => {
  test('conversations are listed creator-privately within one organization', async () => {
    const { listInsightConversations } = require('../api');
    await listInsightConversations('org-1');

    const [url, options] = lastCall();
    expect(url).toContain('/api/v3/insight/conversations?');
    expect(url).toContain('organization_id=org-1');
    expect(url).toContain('limit=50');
    expect(url).toContain('offset=0');
    expect(options.method || 'GET').toBe('GET');
  });

  test('starting a conversation posts the organization and an optional title', async () => {
    const { createInsightConversation } = require('../api');
    await createInsightConversation('org-1', 'Q3 2025 emissions');
    expect(lastCall()[0]).toContain('/api/v3/insight/conversations');
    expect(lastCall()[1].method).toBe('POST');
    expect(lastBody()).toEqual({ organization_id: 'org-1', title: 'Q3 2025 emissions' });

    await createInsightConversation('org-1', '');
    expect(lastBody()).toEqual({ organization_id: 'org-1', title: null });
  });

  test('messages are read through the authorized conversation route', async () => {
    const { listInsightMessages } = require('../api');
    await listInsightMessages('org-1', 'conv-9');
    const [url] = lastCall();
    expect(url).toContain('/api/v3/insight/conversations/conv-9/messages?');
    expect(url).toContain('organization_id=org-1');
  });

  test('an interaction posts the question with a client idempotency key', async () => {
    const { runInsightInteraction } = require('../api');
    await runInsightInteraction({
      organizationId: 'org-1',
      conversationId: 'conv-9',
      question: 'What did report version 2 show?',
      idempotencyKey: 'key-1',
      narration: 'optional',
    });

    expect(lastCall()[0]).toContain('/api/v3/insight/interactions');
    expect(lastCall()[1].method).toBe('POST');
    expect(lastBody()).toEqual({
      organization_id: 'org-1',
      conversation_id: 'conv-9',
      question: 'What did report version 2 show?',
      idempotency_key: 'key-1',
      narration: 'optional',
    });
  });

  test('the idempotency key and narration are omitted when not supplied', async () => {
    const { runInsightInteraction } = require('../api');
    await runInsightInteraction({ organizationId: 'o', conversationId: 'c', question: 'q' });
    expect(Object.keys(lastBody()).sort()).toEqual([
      'conversation_id',
      'organization_id',
      'question',
    ]);
  });

  test('interactions can be filtered to one conversation', async () => {
    const { listInsightInteractions } = require('../api');
    await listInsightInteractions('org-1', { conversationId: 'conv-9' });
    const [url] = lastCall();
    expect(url).toContain('/api/v3/insight/interactions?');
    expect(url).toContain('conversation_id=conv-9');
    expect(url).toContain('organization_id=org-1');
  });

  test('one interaction is re-read through the authorized creator-private route', async () => {
    const { getInsightInteraction } = require('../api');
    await getInsightInteraction('org-1', 'int-3');
    const [url] = lastCall();
    expect(url).toContain('/api/v3/insight/interactions/int-3?');
    expect(url).toContain('organization_id=org-1');
  });

  test('reference resolution uses the ratified I3 tool surface', async () => {
    const { invokeInsightTool } = require('../api');
    await invokeInsightTool('org-1', 'report_lookup', { report_id: 'report-1' });

    expect(lastCall()[0]).toContain('/api/v3/insight/tools/invoke');
    expect(lastCall()[1].method).toBe('POST');
    expect(lastBody()).toEqual({
      organization_id: 'org-1',
      tool: 'report_lookup',
      input: { report_id: 'report-1' },
    });
  });
});
