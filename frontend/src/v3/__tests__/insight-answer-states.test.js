// frontend/src/v3/__tests__/insight-answer-states.test.js
// I6 — the complete I4 AnswerStatus vocabulary must be presented truthfully.
//
// The load-bearing assertion of this suite is PO I6-5:
//
//     `no_data` must NEVER be rendered as `zero`.
//
// `zero` means CarbonTally found records and calculated 0; `no_data` means
// nothing matched. The I6 tests therefore pin both the pure mapping
// (`answerIsZero`) and the rendered marker (`data-answer-zero`) for every one of
// the fourteen ratified states, so a future status can never be silently
// upgraded into a zero result.
import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import InsightAnswerState from '../insight/InsightAnswerState';
import {
  ANSWER_STATUS_VALUES,
  answerIsZero,
  getAnswerPresentation,
  getNarrationPresentation,
  getReplayNotice,
} from '../insight/answerStates';

afterEach(cleanup);

const EXPECTED_VOCABULARY = [
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

describe('I4 answer-state vocabulary (I6-5)', () => {
  test('covers exactly the fourteen ratified states', () => {
    expect([...ANSWER_STATUS_VALUES].sort()).toEqual([...EXPECTED_VOCABULARY].sort());
    // Each ratified state has a presentation (no state falls through to the
    // "not recognised" default).
    EXPECTED_VOCABULARY.forEach((status) => {
      expect(getAnswerPresentation(status).label).not.toMatch(/not recognised/i);
    });
  });

  test('every state has a distinct human label (no state is collapsed into another)', () => {
    const labels = ANSWER_STATUS_VALUES.map((status) => getAnswerPresentation(status).label);
    expect(new Set(labels).size).toBe(labels.length);
  });

  test('answerIsZero is true for `zero` only', () => {
    ANSWER_STATUS_VALUES.forEach((status) => {
      expect(answerIsZero(status)).toBe(status === 'zero');
    });
  });

  test('an unknown state is never presented as an answer or as zero', () => {
    const presentation = getAnswerPresentation('some_future_state');
    expect(answerIsZero('some_future_state')).toBe(false);
    expect(presentation.label).toMatch(/not recognised/i);
  });
});

describe('InsightAnswerState renders every state', () => {
  test.each(EXPECTED_VOCABULARY)('state %s renders its own label and never a false zero', (status) => {
    render(<InsightAnswerState answerStatus={status} headingId={`h-${status}`} />);

    const block = screen.getByTestId('insight-answer-state');
    expect(block).toHaveAttribute('data-answer-status', status);
    expect(block).toHaveAttribute('data-answer-zero', status === 'zero' ? 'true' : 'false');
    expect(screen.getByText(getAnswerPresentation(status).label)).toBeInTheDocument();
  });

  test('`no_data` is never rendered as `zero`', () => {
    render(<InsightAnswerState answerStatus="no_data" headingId="h-no-data" />);

    // The rendered marker is false and the label is not the zero label.
    expect(screen.getByTestId('insight-answer-state')).toHaveAttribute('data-answer-zero', 'false');
    expect(screen.queryByText(getAnswerPresentation('zero').label)).not.toBeInTheDocument();
    // And the user is told explicitly that nothing was found to calculate from.
    expect(screen.getByText(/Nothing was found to calculate from/i)).toBeInTheDocument();
  });

  test('`zero` is presented as a real calculation from records that were found', () => {
    render(<InsightAnswerState answerStatus="zero" headingId="h-zero" />);

    expect(screen.getByTestId('insight-answer-state')).toHaveAttribute('data-answer-zero', 'true');
    expect(screen.getByText(/found matching records/i)).toBeInTheDocument();
    expect(screen.getByText(/not an absence of data/i)).toBeInTheDocument();
  });

  test('`no_data` and `zero` are distinct in tone and icon, not only in text', () => {
    expect(getAnswerPresentation('no_data').tone).not.toEqual(getAnswerPresentation('zero').tone);
    expect(getAnswerPresentation('no_data').icon).not.toEqual(getAnswerPresentation('zero').icon);
  });
});

describe('InsightAnswerState — narration and lifecycle (I6-6 / I6-8)', () => {
  test('provider_unavailable keeps the deterministic result visible and names the gap', () => {
    render(
      <InsightAnswerState
        answerStatus="provider_unavailable"
        narrationState="unavailable"
        narrationText={null}
        headingId="h-provider"
      />,
    );

    expect(
      screen.getByText(getAnswerPresentation('provider_unavailable').label),
    ).toBeInTheDocument();
    // No narration was invented to fill the gap.
    expect(screen.queryByText(/^CarbonTally summary$/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Written summary unavailable/i)).toBeInTheDocument();
    expect(screen.getByText(/authoritative and is unaffected/i)).toBeInTheDocument();
  });

  test('narration produced by the backend is displayed as CarbonTally content', () => {
    render(
      <InsightAnswerState
        answerStatus="success"
        narrationState="completed"
        narrationText="Report version 2 recorded 26,661.55 kg CO2e for 2025."
        headingId="h-narrated"
      />,
    );

    expect(screen.getByText(/^CarbonTally summary$/i)).toBeInTheDocument();
    expect(
      screen.getByText('Report version 2 recorded 26,661.55 kg CO2e for 2025.'),
    ).toBeInTheDocument();
    // A completed narration carries no "unavailable" notice.
    expect(screen.queryByText(/Written summary unavailable/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Summary in the conversation$/i)).not.toBeInTheDocument();
  });

  test('a completed narration read from history points at the transcript instead of denying it', () => {
    // A persisted interaction read from history carries narration_state
    // `completed` while the narration itself lives in the conversation history.
    render(
      <InsightAnswerState answerStatus="success" narrationState="completed" headingId="h-historic" />,
    );

    expect(screen.getByText(/^Summary in the conversation$/i)).toBeInTheDocument();
    // It must NOT claim that no summary was generated.
    expect(screen.queryByText(/No AI-written summary was generated/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Written summary unavailable/i)).not.toBeInTheDocument();
  });

  test('skipped narration says the deterministic result is all that is shown', () => {
    render(
      <InsightAnswerState answerStatus="success" narrationState="skipped" headingId="h-skipped" />,
    );

    expect(screen.getByText(/No written summary for this answer/i)).toBeInTheDocument();
    expect(screen.getByText(/No AI-written summary was generated/i)).toBeInTheDocument();
  });

  test('replayed=true is shown as an informational lifecycle fact', () => {
    render(
      <InsightAnswerState
        answerStatus="success"
        lifecycle="completed"
        replayed
        headingId="h-replay"
      />,
    );

    expect(screen.getByText(/Already answered/i)).toBeInTheDocument();
    expect(screen.getByText(/not run or recorded twice/i)).toBeInTheDocument();
    expect(screen.getByText(/Interaction: Completed/i)).toBeInTheDocument();
  });

  test('replayed=false shows no replay notice', () => {
    render(
      <InsightAnswerState answerStatus="success" lifecycle="completed" headingId="h-noreplay" />,
    );
    expect(screen.queryByText(/Already answered/i)).not.toBeInTheDocument();
  });

  test('getReplayNotice returns nothing unless the backend reported a replay', () => {
    expect(getReplayNotice(undefined)).toBeNull();
    expect(getReplayNotice(false)).toBeNull();
    expect(getReplayNotice(true)).not.toBeNull();
  });

  test('narration presentation prefers real text over any notice', () => {
    expect(
      getNarrationPresentation({ narrationState: 'unavailable', hasNarrationText: true }),
    ).toBeNull();
    expect(getNarrationPresentation({ narrationState: 'unavailable' }).tone).toBe('warning');
  });
});

