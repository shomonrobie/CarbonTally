// frontend/src/components/chat/__tests__/chat-identity.test.jsx
// P8-FIN-01b (D-9) — chat participant identity must come from the authorised,
// org-scoped projection (GET /api/v3/organizations/{org_id}/members).
// These two display sites must never perform a direct peer read of `users`, an
// unresolved participant must keep the existing generic fallback, and a
// participant who is not in the authorised projection must not gain an identity.
import React from 'react';
import fs from 'fs';
import path from 'path';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatWindow from '../ChatWindow';
import ChatList from '../ChatList';

jest.mock('../../../supabaseClient', () => {
  const tablesRead = [];
  const data = {
    // The other participant is user-2; currentUser is user-1.
    conversation_participants: [{ user_id: 'user-1' }, { user_id: 'user-2' }],
    messages: [],
  };
  const makeQuery = (table) => {
    const query = {};
    [
      'select', 'eq', 'neq', 'in', 'order', 'limit', 'range',
      'single', 'maybeSingle', 'insert', 'update', 'upsert', 'delete', 'match',
    ].forEach((method) => { query[method] = () => query; });
    query.then = (onFulfilled, onRejected) => Promise
      .resolve({ data: data[table] ?? [], error: null })
      .then(onFulfilled, onRejected);
    return query;
  };
  const channel = { on: () => channel, subscribe: () => channel, unsubscribe: () => channel };
  const supabase = {
    auth: { getUser: jest.fn() },
    from: jest.fn(),
    channel: jest.fn(),
    removeChannel: jest.fn(),
  };
  // CRA's jest config enables resetMocks, so implementations are (re)installed
  // through this helper before each test.
  const install = () => {
    tablesRead.length = 0;
    supabase.auth.getUser.mockResolvedValue({ data: { user: { id: 'user-1' } } });
    supabase.from.mockImplementation((table) => {
      tablesRead.push(table);
      return makeQuery(table);
    });
    supabase.channel.mockImplementation(() => channel);
    supabase.removeChannel.mockImplementation(() => {});
  };
  install();
  return { __tablesRead: tablesRead, __install: install, supabase };
});

jest.mock('../../../v3/api', () => ({ listMembers: jest.fn() }));

jest.mock('../../../context/RealtimeContext', () => ({
  useRealtime: () => ({ onlineStaff: [] }),
}));

const { __tablesRead, __install } = jest.requireMock('../../../supabaseClient');
const api = jest.requireMock('../../../v3/api');

const ORG = { id: 'org-1', name: 'Acme Ltd' };
const CONVERSATIONS = [{ id: 'conv-1', participants: [{ user_id: 'user-1' }, { user_id: 'user-2' }] }];

// Fixtures mirror the REAL projection contract of
// `GET /api/v3/organizations/{org_id}/members` — the backend repository mapper
// `_row_to_member_with_email` (backend/data/organizations.py) returns
// email / first_name / last_name, NOT the raw SQL aliases user_email /
// user_first_name / user_last_name. Getting this wrong is silently invisible
// at runtime (the UI just falls back to a generic label), so it is guarded
// below by `projection contract` tests.
const MEMBER_PROJECTION_KEYS = [
  'id', 'organization_id', 'user_id', 'role', 'is_active', 'created_at',
  'email', 'first_name', 'last_name',
];

const MEMBER_PROJECTION = {
  members: [
    { user_id: 'user-1', email: 'me@acme.test', first_name: 'Me', last_name: 'Self' },
    { user_id: 'user-2', email: 'alice@acme.test', first_name: 'Alice', last_name: 'Member' },
  ],
};

const renderWindow = () => render(
  <ChatWindow conversationId="conv-1" organization={ORG} compact onBack={() => {}} />,
);

const renderList = () => render(
  <ChatList
    conversations={CONVERSATIONS}
    selectedId={null}
    onSelectConversation={() => {}}
    loading={false}
    organization={ORG}
  />,
);

beforeEach(() => {
  jest.clearAllMocks();
  __install();
  api.listMembers.mockResolvedValue(MEMBER_PROJECTION);
  jest.spyOn(console, 'warn').mockImplementation(() => {});
});

// jsdom does not implement Element.prototype.scrollIntoView, which ChatWindow
// calls (on a timer) after messages render. Stub it locally so the suite is not
// timing-flaky; this is unrelated to the identity behaviour under test.
beforeAll(() => {
  Element.prototype.scrollIntoView = jest.fn();
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('P8-FIN-01b — ChatWindow participant identity', () => {
  it('resolves an organisation member participant to the projected identity', async () => {
    renderWindow();

    expect(api.listMembers).toHaveBeenCalledWith('org-1');
    await screen.findByText('Alice Member');
  });

  it('uses the projected email when the member has no display name', async () => {
    api.listMembers.mockResolvedValue({
      members: [
        { user_id: 'user-1', email: 'me@acme.test' },
        { user_id: 'user-2', email: 'alice@acme.test' },
      ],
    });
    renderWindow();

    await screen.findByText('alice@acme.test');
  });

  it('keeps the generic fallback for a participant with no projected identity', async () => {
    api.listMembers.mockResolvedValue({ members: [{ user_id: 'user-1', email: 'me@acme.test' }] });
    renderWindow();

    await screen.findByText('Chat');
    expect(api.listMembers).toHaveBeenCalledWith('org-1');
    expect(screen.queryByText('Alice Member')).not.toBeInTheDocument();
  });

  it('keeps the generic fallback when the projection is unavailable (never throws)', async () => {
    api.listMembers.mockRejectedValue(new Error('projection unavailable'));
    renderWindow();

    await screen.findByText('Chat');
  });

  it('never reads peer identity directly from users', async () => {
    renderWindow();

    await screen.findByText('Alice Member');
    expect(__tablesRead).not.toContain('users');
    expect(__tablesRead).toContain('conversation_participants');
  });
});

describe('P8-FIN-01b — ChatList participant identity', () => {
  it('resolves an organisation member participant to the projected identity', async () => {
    renderList();

    expect(api.listMembers).toHaveBeenCalledWith('org-1');
    await screen.findByText('Alice Member');
  });

  it('keeps the generic fallback for a participant with no projected identity', async () => {
    api.listMembers.mockResolvedValue({ members: [{ user_id: 'user-1', email: 'me@acme.test' }] });
    renderList();

    await screen.findByText('Unknown');
    expect(screen.queryByText('Alice Member')).not.toBeInTheDocument();
  });

  it('keeps the generic fallback when the projection is unavailable (never throws)', async () => {
    api.listMembers.mockRejectedValue(new Error('projection unavailable'));
    renderList();

    await screen.findByText('Unknown');
  });

  it('never reads peer identity directly from users', async () => {
    renderList();

    await screen.findByText('Alice Member');
    expect(__tablesRead).not.toContain('users');
  });
});

describe('P8-FIN-01b — member projection contract', () => {
  const BACKEND_MAPPER_PATH = path.join(
    __dirname, '..', '..', '..', '..', '..', 'backend', 'data', 'organizations.py',
  );

  const backendProjectionKeys = () => {
    const source = fs.readFileSync(BACKEND_MAPPER_PATH, 'utf8');
    const fnIndex = source.indexOf('def _row_to_member_with_email');
    expect(fnIndex).toBeGreaterThan(-1);
    const rest = source.slice(fnIndex + 1);
    const nextDef = rest.indexOf('\ndef ');
    const body = nextDef === -1 ? rest.slice(0, 2000) : rest.slice(0, nextDef);
    // Returned dict keys look like `"email": r.get("user_email"),` — the SQL
    // aliases inside r.get(...) carry no trailing colon and are not matched.
    const keys = [...body.matchAll(/"([a-z_]+)":/g)].map((match) => match[1]);
    return [...new Set(keys)].sort();
  };

  it('the API projection still returns exactly the keys these tests model', () => {
    expect(backendProjectionKeys()).toEqual([...MEMBER_PROJECTION_KEYS].sort());
  });

  it('fixtures use only real projection keys (never the raw SQL aliases)', () => {
    MEMBER_PROJECTION.members.forEach((member) => {
      Object.keys(member).forEach((key) => {
        expect(MEMBER_PROJECTION_KEYS).toContain(key);
      });
    });
  });
});
