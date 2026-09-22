// frontend/src/v3/insight/answerStates.js
// CarbonTally Insight I6 — the authoritative I4 AnswerStatus presentation
// vocabulary (presentation only; no contract change).
//
// This is the **fourteen** states ratified by the I4 contract
// (`backend/domain/insight_interaction.py` → `AnswerStatus`, Master Spec §14).
// It is deliberately NOT the I3 `ToolStatus` vocabulary and the two are never
// merged: the I4 answer vocabulary describes the outcome of a whole
// interaction, `ToolStatus` describes one tool call inside it.
//
// The UI must present the complete vocabulary, including states the current
// deterministic-first orchestration does not reach in production (I6-5), and it
// must never upgrade one state into another. The single hard invariant is:
//
//     `no_data` is NEVER rendered as `zero`.
//
// `zero` means CarbonTally found data and calculated 0; `no_data` means nothing
// matched. `answerIsZero()` below is the machine-checkable statement of that
// rule and is asserted for every state by the I6 test suite.

/** The complete I4 `AnswerStatus` vocabulary (order = backend enum order). */
export const ANSWER_STATUS_VALUES = [
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

// Tones are the existing D21 badge tones, so no new visual system is introduced.
const ANSWER_PRESENTATION = {
  success: {
    label: 'Answered',
    tone: 'success',
    icon: 'checkCircle',
    summary: "CarbonTally answered this from your organisation's own data.",
    guidance: null,
  },
  zero: {
    label: 'Answered — result is zero',
    tone: 'info',
    icon: 'calculator',
    summary: 'CarbonTally found matching records and the calculated result is 0.',
    guidance:
      'A zero result is a real calculation from records that were found. It is not an absence of data.',
  },
  no_data: {
    label: 'No data found',
    tone: 'muted',
    icon: 'search',
    summary: 'No matching CarbonTally records were found for this question.',
    guidance:
      'This is not the same as a result of 0: nothing was found to calculate from, so no figure exists. Check the reporting year or the reference in your question, or confirm the data has been processed.',
  },
  not_authorized: {
    label: 'Not available',
    tone: 'muted',
    icon: 'lock',
    summary: "This information isn't available to you.",
    guidance: null,
  },
  insufficient_data: {
    label: 'Not enough data',
    tone: 'warning',
    icon: 'alert',
    summary: 'CarbonTally does not yet hold enough data to answer this.',
    guidance: 'Upload or process the missing records, then ask again.',
  },
  needs_clarification: {
    label: 'More detail needed',
    tone: 'info',
    icon: 'help',
    summary: "CarbonTally couldn't tell which record this question refers to.",
    guidance:
      'Include a specific reference — for example a report, a report version number, or a calculation snapshot.',
  },
  tool_failure: {
    label: 'Lookup failed',
    tone: 'error',
    icon: 'xCircle',
    summary: 'A CarbonTally data lookup failed while answering this question.',
    guidance: 'No conclusion can be drawn from this attempt. Try again.',
  },
  provider_unavailable: {
    label: 'Summary unavailable',
    tone: 'warning',
    icon: 'alert',
    summary: 'The written summary could not be generated for this answer.',
    guidance:
      'The CarbonTally result below is authoritative and is unaffected. No summary has been invented in its place.',
  },
  partial: {
    label: 'Partial answer',
    tone: 'warning',
    icon: 'alert',
    summary: 'Only part of this question could be answered from your data.',
    guidance: 'The remaining part could not be resolved. Narrow the question and ask again.',
  },
  rate_limited: {
    label: 'Too many requests',
    tone: 'warning',
    icon: 'clock',
    summary: 'CarbonTally is temporarily rate limiting questions.',
    guidance: 'Wait a moment and ask again.',
  },
  refused: {
    label: 'Not answered',
    tone: 'muted',
    icon: 'xCircle',
    summary: 'CarbonTally cannot answer this question.',
    guidance: "Rephrase the question, or ask about your own organisation's emissions records.",
  },
  ungrounded: {
    label: 'Not shown — unverified wording',
    tone: 'warning',
    icon: 'alert',
    summary: 'The generated wording could not be tied to a CarbonTally result.',
    guidance: 'It is not presented as an answer. The underlying records are unchanged.',
  },
  invalid_input: {
    label: "Couldn't process that question",
    tone: 'warning',
    icon: 'alert',
    summary: 'The question could not be processed.',
    guidance: 'Rephrase it, or include a specific report, version or snapshot reference.',
  },
  error: {
    label: 'Something went wrong',
    tone: 'error',
    icon: 'xCircle',
    summary: 'This attempt did not complete.',
    guidance: 'Nothing was concluded from it. Please try again.',
  },
};

// A state the UI does not recognise (for example a future backend value) is
// presented as neutral and explicitly NOT as an answer — never as zero.
const UNKNOWN_PRESENTATION = {
  label: 'Answer state not recognised',
  tone: 'muted',
  icon: 'help',
  summary: 'CarbonTally returned an answer state this screen does not recognise.',
  guidance: 'No conclusion should be drawn from it. Refresh the conversation or try again.',
};

/** The presentation for any answer status (unknown values never render as zero). */
export function getAnswerPresentation(status) {
  const key = typeof status === 'string' ? status : '';
  return ANSWER_PRESENTATION[key] || { ...UNKNOWN_PRESENTATION, status: key || 'unknown' };
}

/** True only for the ratified `zero` state — the guard behind "no_data ≠ zero". */
export function answerIsZero(status) {
  return status === 'zero';
}

// ---------------------------------------------------------------------------
// Narration (PO Q11/Q14, I6-6)
//
// The UI only ever displays narration text the backend actually produced, and
// it states provider unavailability truthfully. There is no client-side
// provider fallback and no fabricated narration.
// ---------------------------------------------------------------------------

const NARRATION_PRESENTATION = {
  // narration_text is displayed as CarbonTally-authored content — no notice.
  completed: {
    tone: 'info',
    title: 'Summary in the conversation',
    body:
      'The written summary CarbonTally generated for this answer is shown in the conversation history above.',
  },
  unavailable: {
    tone: 'warning',
    title: 'Written summary unavailable',
    body:
      'CarbonTally could not generate the written summary for this answer. The result from your data is shown here and is unchanged — no summary has been invented to replace it.',
  },
  skipped: {
    tone: 'info',
    title: 'No written summary for this answer',
    body:
      'Only the CarbonTally result from your data is shown. No AI-written summary was generated for this answer.',
  },
  not_attempted: {
    tone: 'info',
    title: 'No written summary for this answer',
    body:
      'Only the CarbonTally result from your data is shown. No AI-written summary was generated for this answer.',
  },
};

/**
 * What to show for narration, or `null` when there is real narration text.
 *
 * `unavailable` is the case the PO singled out: the deterministic result stands
 * and the provider gap is named explicitly.
 */
export function getNarrationPresentation({ narrationState, hasNarrationText } = {}) {
  if (hasNarrationText) return null;
  const key = typeof narrationState === 'string' ? narrationState : '';
  const presentation = NARRATION_PRESENTATION[key];
  if (presentation) return { narrationState: key, ...presentation };
  return {
    narrationState: key || 'unknown',
    tone: 'info',
    title: 'No written summary for this answer',
    body:
      'Only the CarbonTally result from your data is shown. No AI-written summary was generated for this answer.',
  };
}

// ---------------------------------------------------------------------------
// Interaction lifecycle (PO Q7) — informational only. No new lifecycle model is
// introduced and internal idempotency implementation is not exposed.
// ---------------------------------------------------------------------------

const LIFECYCLE_PRESENTATION = {
  received: 'Received',
  executing: 'In progress',
  completed: 'Completed',
  failed: 'Failed',
};

export function getLifecycleLabel(lifecycle) {
  return LIFECYCLE_PRESENTATION[lifecycle] || null;
}

/**
 * The replay indication (I6-8).
 *
 * `replayed=true` means the backend recognised a repeated request and returned
 * the already-persisted interaction instead of running a second one. The UI may
 * say so as an informational lifecycle fact; it never presents it as a failure
 * and never exposes the idempotency key itself.
 */
export function getReplayNotice(replayed) {
  if (!replayed) return null;
  return {
    tone: 'info',
    title: 'Already answered',
    body:
      'This is the existing answer for this question — it was not run or recorded twice.',
  };
}



