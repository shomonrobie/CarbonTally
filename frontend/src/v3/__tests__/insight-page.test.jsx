// frontend/src/v3/__tests__/insight-page.test.jsx
// I6 — the authenticated Insight workspace (conversation list, conversation view,
// composer, answer states, evidence and error states).
//
// The workspace is UX only: every read/write goes through the closed I1–I4
// backend contracts, and nothing is authorized client-side. These tests pin the
// user-visible states the PO authorization requires (I6-3 … I6-8) and the
// accessibility/response contract from I6 acceptance.
import React from 'react';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import fs from 'fs';
import path from 'path';

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: jest.fn(), getUser: jest.fn() } },
}));

jest.mock('../api', () => ({
  resolveV3Organization: jest.fn(),
  listInsightConversations: jest.fn(),
  createInsightConversation: jest.fn(),
  listInsightMessages: jest.fn(),
  listInsightInteractions: jest.fn(),
  runInsightInteraction: jest.fn(),
  getInsightInteraction: jest.fn(),
  invokeInsightTool: jest.fn(),
}));

import InsightPage from '../insight/InsightPage';

const api = jest.requireMock('../api');

const ORG = { id: 'org-1', name: 'Acme Ltd' };

const CONVERSATION = {
  id: 'conv-1',
  organization_id: 'org-1',
  title: 'Q3 2025 review',
  created_at: '2026-09-01T09:00:00Z',
  updated_at: '2026-09-02T10:00:00Z',
  created_by: 'user-1',
};

const MESSAGES = {
  conversation_id: 'conv-1',
  messages: [
    {
      id: 'm1',
      conversation_id: 'conv-1',
      organization_id: 'org-1',
      role: 'user',
      content: 'What did report version 2 show for 2025?',
      ordinal: 0,
      created_at: '2026-09-02T10:00:00Z',
    },
    {
      id: 'm2',
      conversation_id: 'conv-1',
      organization_id: 'org-1',
      role: 'insight',
      content: 'Report version 2 recorded 26,661.55 kg CO2e for 2025.',
      ordinal: 1,
      created_at: '2026-09-02T10:00:06Z',
    },
  ],
  limit: 200,
  offset: 0,
};

const INTERACTION = {
  interaction_id: 'int-1',
  conversation_id: 'conv-1',
  lifecycle: 'completed',
  answer_status: 'success',
  narration_state: 'completed',
  intent: 'report_version_lookup',
  tool_call_count: 1,
  reference_count: 1,
  created_at: '2026-09-02T10:00:05Z',
  completed_at: '2026-09-02T10:00:06Z',
};

const outcomeFor = (answerStatus, overrides = {}) => ({
  interaction_id: 'int-new',
  organization_id: 'org-1',
  conversation_id: 'conv-1',
  lifecycle: answerStatus === 'error' ? 'failed' : 'completed',
  answer_status: answerStatus,
  narration_state: 'skipped',
  narration_text: null,
  intent: 'report_version_lookup',
  intent_source: 'deterministic',
  provider: null,
  model: null,
  model_version: null,
  tokens_used: null,
  cost: null,
  message_id: 'm-new',
  audit_record_id: 'audit-1',
  tool_calls: [],
  references: [],
  replayed: false,
  contract_version: 'i4-layer2-v1',
  ...overrides,
});

beforeEach(() => {
  jest.clearAllMocks();
  api.resolveV3Organization.mockResolvedValue(ORG);
  api.listInsightConversations.mockResolvedValue({ conversations: [CONVERSATION], total: 1 });
  api.listInsightMessages.mockResolvedValue(MESSAGES);
  api.listInsightInteractions.mockResolvedValue({ interactions: [INTERACTION], total: 1 });
  api.createInsightConversation.mockResolvedValue({ ...CONVERSATION, id: 'conv-2', title: 'New' });
  api.getInsightInteraction.mockResolvedValue({ ...INTERACTION, tool_calls: [], references: [] });
});

afterEach(cleanup);

const openConversation = async () => {
  const button = await screen.findByRole('button', { name: /Q3 2025 review/ });
  fireEvent.click(button);
  return button;
};

describe('I6 entry — authenticated workspace context', () => {
  test('shows a loading state while the workspace resolves', () => {
    api.resolveV3Organization.mockReturnValue(new Promise(() => {}));
    render(<InsightPage />);
    expect(screen.getByTestId('insight-page')).toHaveTextContent('Loading CarbonTally Insight…');
  });

  test('an account with no organisation gets an explicit empty state, not an error', async () => {
    api.resolveV3Organization.mockResolvedValue(null);
    render(<InsightPage />);

    expect(await screen.findByTestId('insight-no-org')).toBeInTheDocument();
    expect(api.listInsightConversations).not.toHaveBeenCalled();
  });

  test('a context failure offers a controlled retry', async () => {
    api.resolveV3Organization.mockRejectedValue(new Error('boom'));
    render(<InsightPage />);

    expect(await screen.findByText(/Insight isn't available just now/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    await waitFor(() => expect(api.resolveV3Organization.mock.calls.length).toBeGreaterThan(1));
  });
});

describe('I6 conversation list (creator-private)', () => {
  test('lists the conversations the backend returned for the caller', async () => {
    render(<InsightPage />);

    const list = await screen.findByTestId('insight-conversation-list');
    expect(list).toHaveTextContent('Q3 2025 review');
    expect(api.listInsightConversations).toHaveBeenCalledWith('org-1');
  });

  test('marks the opened conversation as current for assistive technology', async () => {
    render(<InsightPage />);
    const button = await openConversation();
    await waitFor(() => expect(button).toHaveAttribute('aria-current', 'true'));
  });

  test('an empty list explains what to do next', async () => {
    api.listInsightConversations.mockResolvedValue({ conversations: [], total: 0 });
    render(<InsightPage />);

    expect(await screen.findByTestId('insight-conversations-empty')).toHaveTextContent(
      /Start one with the box above/i,
    );
  });

  test('a list failure is retryable and never shows a raw error', async () => {
    api.listInsightConversations.mockRejectedValue(new Error('duplicate key constraint ...'));
    render(<InsightPage />);

    const error = await screen.findByText(/Conversations unavailable/i);
    expect(error).toBeInTheDocument();
    expect(screen.queryByText(/duplicate key constraint/)).not.toBeInTheDocument();

    api.listInsightConversations.mockResolvedValue({ conversations: [CONVERSATION], total: 1 });
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(await screen.findByTestId('insight-conversation-list')).toHaveTextContent('Q3 2025 review');
  });
});

describe('I6 start and continue (I6-3)', () => {
  test('starting a new conversation creates it and opens it', async () => {
    render(<InsightPage />);
    const topic = await screen.findByLabelText('Start a new conversation');
    fireEvent.change(topic, { target: { value: 'Q4 review' } });

    api.listInsightConversations.mockResolvedValue({
      conversations: [CONVERSATION, { ...CONVERSATION, id: 'conv-2', title: 'Q4 review' }],
      total: 2,
    });
    fireEvent.click(screen.getByRole('button', { name: 'New' }));

    await waitFor(() =>
      expect(api.createInsightConversation).toHaveBeenCalledWith('org-1', 'Q4 review'),
    );
    expect(await screen.findByRole('button', { name: /Q4 review/ })).toHaveAttribute(
      'aria-current',
      'true',
    );
  });

  test('a failed creation keeps the workspace usable and says nothing technical', async () => {
    api.createInsightConversation.mockRejectedValue(new Error('duplicate key constraint "x"'));
    render(<InsightPage />);
    fireEvent.change(await screen.findByLabelText('Start a new conversation'), {
      target: { value: 'Q4 review' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'New' }));

    expect(await screen.findByTestId('insight-error')).toHaveTextContent(
      /couldn't start a new conversation/i,
    );
    expect(screen.queryByText(/duplicate key constraint/)).not.toBeInTheDocument();
  });

  test('continuing a conversation runs one interaction and shows its answer', async () => {
    render(<InsightPage />);
    await openConversation();

    api.listInsightInteractions.mockResolvedValue({ interactions: [], total: 0 });
    fireEvent.change(screen.getByLabelText('Ask a question about your emissions data'), {
      target: { value: 'What did report version 2 show?' },
    });
    api.runInsightInteraction.mockResolvedValue(
      outcomeFor('success', {
        narration_state: 'completed',
        narration_text: 'Report version 2 recorded 26,661.55 kg CO2e for 2025.',
        tool_calls: [
          { tool_call_id: 'tc-1', tool: 'report_version_lookup', status: 'success', reason: null, duration_ms: 12 },
        ],
        references: [{ kind: 'report_version', id: 'ver-1' }],
      }),
    );

    fireEvent.click(screen.getByRole('button', { name: /^Ask$/ }));

    await waitFor(() => expect(api.runInsightInteraction).toHaveBeenCalledTimes(1));
    const args = api.runInsightInteraction.mock.calls[0][0];
    expect(args).toEqual(
      expect.objectContaining({
        organizationId: 'org-1',
        conversationId: 'conv-1',
        question: 'What did report version 2 show?',
        narration: 'optional',
      }),
    );
    // A bounded client request key accompanies the submit (duplicate prevention).
    expect(typeof args.idempotencyKey).toBe('string');
    expect(args.idempotencyKey.length).toBeGreaterThan(8);

    // The answer, its narration, its tool evidence and its references are shown.
    expect(await screen.findByText('Answered')).toBeInTheDocument();
    // The narration is persisted as an I4 message *and* returned in the outcome,
    // so it legitimately appears in both the transcript and the answer card.
    expect(
      screen.getAllByText('Report version 2 recorded 26,661.55 kg CO2e for 2025.').length,
    ).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('report_version_lookup')).toBeInTheDocument();
    expect(await screen.findByTestId('insight-reference')).toHaveAttribute(
      'data-reference-kind',
      'report_version',
    );
    // The composer is cleared for the next turn.
    expect(screen.getByLabelText('Ask a question about your emissions data')).toHaveValue('');
  });

  test('a failed question is reported without disclosing anything and keeps the draft', async () => {
    render(<InsightPage />);
    await openConversation();

    const draft = 'Tell me about a report I may not be allowed to see';
    fireEvent.change(screen.getByLabelText('Ask a question about your emissions data'), {
      target: { value: draft },
    });
    const notFound = new Error('Conversation not found');
    notFound.status = 404;
    api.runInsightInteraction.mockRejectedValue(notFound);

    fireEvent.click(screen.getByRole('button', { name: /^Ask$/ }));

    const error = await screen.findByTestId('insight-error');
    expect(error).toHaveTextContent(/couldn't complete that question/i);
    // The backend's non-disclosing 404 wording is not echoed, and no state is claimed.
    expect(error.textContent).not.toMatch(/not found|not authorized|does not exist/i);
    expect(screen.getByLabelText('Ask a question about your emissions data')).toHaveValue(draft);
  });
});

describe('I6 conversation view', () => {
  test('nothing is selected until the user opens a conversation', async () => {
    render(<InsightPage />);
    expect(await screen.findByTestId('insight-no-conversation-selected')).toBeInTheDocument();
  });

  test('opening a conversation shows its message history and its answers', async () => {
    render(<InsightPage />);
    await openConversation();

    const thread = await screen.findByTestId('insight-thread');
    expect(thread).toHaveTextContent('What did report version 2 show for 2025?');
    expect(thread).toHaveTextContent('Report version 2 recorded 26,661.55 kg CO2e for 2025.');
    expect(screen.getByText('You asked')).toBeInTheDocument();
    expect(screen.getByText('CarbonTally')).toBeInTheDocument();

    expect(api.listInsightMessages).toHaveBeenCalledWith('org-1', 'conv-1');
    expect(api.listInsightInteractions).toHaveBeenCalledWith('org-1', { conversationId: 'conv-1' });
    expect(await screen.findByTestId('insight-interactions')).toBeInTheDocument();
  });

  test('an empty conversation shows an explicit empty state on both panels', async () => {
    api.listInsightMessages.mockResolvedValue({ conversation_id: 'conv-1', messages: [] });
    api.listInsightInteractions.mockResolvedValue({ interactions: [], total: 0 });
    render(<InsightPage />);
    await openConversation();

    expect(await screen.findByTestId('insight-history-empty')).toHaveTextContent(/Ask the first question/i);
    expect(screen.getByTestId('insight-answers-empty')).toHaveTextContent(/No answers recorded yet/i);
  });

  test('history and answers failures are contained and retryable', async () => {
    api.listInsightMessages.mockRejectedValue(new Error('column reference "id" is ambiguous'));
    api.listInsightInteractions.mockRejectedValue(new Error('boom'));
    render(<InsightPage />);
    await openConversation();

    expect(await screen.findByText(/History unavailable/i)).toBeInTheDocument();
    expect(await screen.findByText(/Answers unavailable/i)).toBeInTheDocument();
    expect(screen.queryByText(/ambiguous/)).not.toBeInTheDocument();
  });
});


const EXPECTED_ANSWER_STATES = [
  'success',
  'zero',
  'no_data',
  'not_authorized',
  'insufficient_data',
  'needs_clarification',
  'tool_failure',
  'provider_unavailable',
  'partial',
  'rate_limited',
  'refused',
  'ungrounded',
  'invalid_input',
  'error',
];

const ask = async (question = 'What did report version 2 show?') => {
  fireEvent.change(screen.getByLabelText('Ask a question about your emissions data'), {
    target: { value: question },
  });
  fireEvent.click(screen.getByRole('button', { name: /^Ask$/ }));
};

describe('I6 answer-state presentation in the workspace (I6-5)', () => {
  test.each(EXPECTED_ANSWER_STATES)(
    'an interaction answered as %s renders that state and never a false zero',
    async (status) => {
      render(<InsightPage />);
      await openConversation();
      api.listInsightInteractions.mockResolvedValue({ interactions: [], total: 0 });
      api.runInsightInteraction.mockResolvedValue(outcomeFor(status));

      await ask();

      const block = await screen.findByTestId('insight-answer-state');
      expect(block).toHaveAttribute('data-answer-status', status);
      expect(block).toHaveAttribute('data-answer-zero', status === 'zero' ? 'true' : 'false');
    },
  );

  test('`no_data` is shown as no data in the workspace, never as a zero result', async () => {
    render(<InsightPage />);
    await openConversation();
    api.listInsightInteractions.mockResolvedValue({ interactions: [], total: 0 });
    api.runInsightInteraction.mockResolvedValue(outcomeFor('no_data'));

    await ask();

    expect(await screen.findByText('No data found')).toBeInTheDocument();
    expect(screen.getByTestId('insight-answer-state')).toHaveAttribute('data-answer-zero', 'false');
    expect(screen.queryByText('Answered — result is zero')).not.toBeInTheDocument();
  });

  test('a not_authorized answer discloses nothing about the underlying record', async () => {
    render(<InsightPage />);
    await openConversation();
    api.listInsightInteractions.mockResolvedValue({ interactions: [], total: 0 });
    api.runInsightInteraction.mockResolvedValue(outcomeFor('not_authorized'));

    await ask();

    const block = await screen.findByTestId('insight-answer-state');
    expect(block).toHaveTextContent("This information isn't available to you.");
    expect(block.textContent).not.toMatch(/does not exist|not found|denied|forbidden/i);
  });
});

describe('I6 provider-unavailable behaviour (I6-6)', () => {
  test('the deterministic result stays visible, the gap is named, nothing is fabricated', async () => {
    render(<InsightPage />);
    await openConversation();
    api.listInsightInteractions.mockResolvedValue({ interactions: [], total: 0 });
    api.runInsightInteraction.mockResolvedValue(
      outcomeFor('provider_unavailable', {
        narration_state: 'unavailable',
        narration_text: null,
        tool_calls: [
          { tool_call_id: 'tc-1', tool: 'report_version_lookup', status: 'success', reason: null, duration_ms: 9 },
        ],
        references: [{ kind: 'report_version', id: 'ver-1' }],
      }),
    );

    await ask();

    // (a) the deterministic evidence is still shown
    expect(await screen.findByText('report_version_lookup')).toBeInTheDocument();
    expect(screen.getByText('Succeeded')).toBeInTheDocument();
    expect(screen.getByTestId('insight-reference')).toBeInTheDocument();
    // (b) the provider gap is explicit
    expect(screen.getByText('Summary unavailable')).toBeInTheDocument();
    expect(screen.getByText(/Written summary unavailable/i)).toBeInTheDocument();
    // (c) no narration was invented, and CarbonTally itself is not blamed for the gap
    expect(screen.queryByText(/^CarbonTally summary$/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/CarbonTally found matching records and the calculated result is 0/i),
    ).not.toBeInTheDocument();
  });

  test('a skipped narration still shows the deterministic result alone', async () => {
    render(<InsightPage />);
    await openConversation();
    api.listInsightInteractions.mockResolvedValue({ interactions: [], total: 0 });
    api.runInsightInteraction.mockResolvedValue(
      outcomeFor('success', {
        narration_state: 'skipped',
        narration_text: null,
        tool_calls: [
          { tool_call_id: 'tc-1', tool: 'calculation_snapshot_lookup', status: 'success', reason: null, duration_ms: 4 },
        ],
      }),
    );

    await ask();

    expect(await screen.findByText('calculation_snapshot_lookup')).toBeInTheDocument();
    expect(screen.getByText(/No written summary for this answer/i)).toBeInTheDocument();
  });
});

describe('I6 replay lifecycle (I6-8)', () => {
  test('replayed=true is shown as an informational fact, not a failure', async () => {
    render(<InsightPage />);
    await openConversation();
    api.listInsightInteractions.mockResolvedValue({ interactions: [], total: 0 });
    api.runInsightInteraction.mockResolvedValue(
      outcomeFor('success', { replayed: true, narration_text: null }),
    );

    await ask();

    expect(await screen.findByText(/Already answered/i)).toBeInTheDocument();
    expect(screen.getByText(/not run or recorded twice/i)).toBeInTheDocument();
    // No error state is raised for a replay.
    expect(screen.queryByTestId('insight-error')).not.toBeInTheDocument();
  });
});

describe('I6 evidence for a historical interaction (I6-4)', () => {
  test('the persisted interaction is re-read through the authorized endpoint', async () => {
    api.getInsightInteraction.mockResolvedValue({
      ...INTERACTION,
      tool_calls: [
        {
          tool_call_id: 'tc-9',
          tool: 'report_lookup',
          status: 'success',
          arguments: { report_id: 'r-1' },
          result_metadata: {},
          references: [{ kind: 'report', id: 'r-1' }, { kind: 'report_version', id: 'v-1' }],
          duration_ms: 7,
        },
      ],
    });
    render(<InsightPage />);
    await openConversation();

    const toggle = await screen.findByRole('button', { name: /view answer details/i });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(toggle);

    await waitFor(() => expect(api.getInsightInteraction).toHaveBeenCalledWith('org-1', 'int-1'));
    expect(await screen.findByText('report_lookup')).toBeInTheDocument();
    expect(screen.getAllByTestId('insight-reference').length).toBe(2);

    const expanded = screen.getByRole('button', { name: /hide answer details/i });
    expect(expanded).toHaveAttribute('aria-expanded', 'true');
    expect(document.getElementById(expanded.getAttribute('aria-controls'))).not.toBeNull();
  });

  test('an interaction that cannot be read shows a non-disclosing evidence state', async () => {
    const notFound = new Error('Interaction not found');
    notFound.status = 404;
    api.getInsightInteraction.mockRejectedValue(notFound);
    render(<InsightPage />);
    await openConversation();

    fireEvent.click(await screen.findByRole('button', { name: /view answer details/i }));

    expect(await screen.findByText(/Evidence not available/i)).toBeInTheDocument();
    expect(screen.queryByText(/Interaction not found/)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });
});

describe('I6 accessibility (I6 acceptance)', () => {
  test('every control carries a meaningful accessible label', async () => {
    render(<InsightPage />);
    await openConversation();

    expect(screen.getByLabelText('Start a new conversation')).toBeInTheDocument();
    expect(screen.getByLabelText('Ask a question about your emissions data')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'New' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Ask$/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Q3 2025 review/ })).toBeInTheDocument();
  });

  test('keyboard access reaches the workspace controls in reading order', async () => {
    render(<InsightPage />);
    await screen.findByTestId('insight-conversation-list');

    userEvent.tab();
    expect(document.activeElement).toBe(screen.getByLabelText('Start a new conversation'));
    userEvent.tab();
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'New' }));
    userEvent.tab();
    expect(document.activeElement).toBe(screen.getByRole('button', { name: /Q3 2025 review/ }));
  });

  test('the newest answer takes focus after a question is asked', async () => {
    render(<InsightPage />);
    await openConversation();
    api.listInsightInteractions.mockResolvedValue({ interactions: [], total: 0 });
    api.runInsightInteraction.mockResolvedValue(outcomeFor('success'));

    await ask();

    await screen.findByTestId('insight-answer-state');
    await waitFor(() =>
      expect(document.activeElement).toBe(
        document.getElementById('insight-interaction-int-new-answer'),
      ),
    );
  });

  test('answer state is conveyed by a text label and an icon, never by colour alone', async () => {
    render(<InsightPage />);
    await openConversation();
    api.listInsightInteractions.mockResolvedValue({ interactions: [], total: 0 });
    api.runInsightInteraction.mockResolvedValue(outcomeFor('no_data'));

    await ask();

    const heading = await screen.findByText('No data found');
    expect(heading.tagName).toBe('H3');
    expect(heading.querySelector('svg')).not.toBeNull();
    expect(heading).toHaveAttribute('id', 'insight-interaction-int-new-answer');
  });
});

describe('I6 responsive layout (I6 acceptance)', () => {
  // jsdom does not evaluate media queries, so the responsive contract is pinned
  // against the stylesheet the browser applies, alongside the DOM the classes
  // are applied to.
  const CSS = fs.readFileSync(path.join(__dirname, '..', 'insight', 'insight.css'), 'utf8');

  test('the workspace renders the responsive two-pane structure', async () => {
    const { container } = render(<InsightPage />);
    await openConversation();

    expect(container.querySelector('.ct-insight-layout')).not.toBeNull();
    expect(container.querySelector('.ct-insight-sidebar')).not.toBeNull();
    expect(container.querySelector('.ct-insight-main')).not.toBeNull();
  });

  test('the two-pane layout collapses to one column at the tablet breakpoint', () => {
    expect(CSS).toMatch(
      /@media \(max-width: 900px\)\s*\{\s*\.ct-insight-layout\s*\{[^}]*grid-template-columns: minmax\(0, 1fr\)/s,
    );
  });

  test('the mobile breakpoint stacks evidence rows and narrows the workspace', () => {
    expect(CSS).toContain('@media (max-width: 640px)');
    expect(CSS).toMatch(/\.ct-insight-ref__rows\s*\{\s*grid-template-columns: minmax\(0, 1fr\)/s);
  });

  test('long identifiers and text cannot overflow the workspace', () => {
    expect(CSS).toContain('overflow-wrap: anywhere');
    expect(CSS).toContain('min-width: 0');
  });

  test('the workspace uses the shared D21 tokens and no private palette', () => {
    expect(CSS).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(CSS).toContain('var(--ct-color-');
  });
});


