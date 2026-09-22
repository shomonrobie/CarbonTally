// frontend/src/v3/insight/InsightAnswerState.jsx
// CarbonTally Insight I6 — the answer-state presentation block.
//
// Renders exactly one I4 `AnswerStatus` truthfully: the state is never upgraded,
// `no_data` is never shown as `zero`, provider narration is either the text the
// backend produced or an explicit unavailability notice — never fabricated.
//
// Accessibility: the state is a labelled section with a visible text label and
// an icon (status is never conveyed by colour alone).
import React from 'react';
import Alert from '../components/ui/Alert';
import Icon from '../components/ui/Icon';
import {
  answerIsZero,
  getAnswerPresentation,
  getLifecycleLabel,
  getNarrationPresentation,
  getReplayNotice,
} from './answerStates';
import { formatTimestamp } from './format';
import './insight.css';

export default function InsightAnswerState({
  answerStatus,
  narrationState,
  narrationText,
  lifecycle,
  replayed,
  createdAt,
  headingId,
}) {
  const presentation = getAnswerPresentation(answerStatus);
  const narration = getNarrationPresentation({
    narrationState,
    hasNarrationText: Boolean(narrationText),
  });
  const replay = getReplayNotice(replayed);
  const lifecycleLabel = getLifecycleLabel(lifecycle);
  const at = formatTimestamp(createdAt);

  return (
    <section
      className="ct-insight-answer"
      data-testid="insight-answer-state"
      data-answer-status={answerStatus || 'unknown'}
      // The machine-checkable form of "no_data must never render as zero".
      data-answer-zero={answerIsZero(answerStatus) ? 'true' : 'false'}
      aria-labelledby={headingId}
    >
      <h3
        id={headingId}
        className={`ct-insight-answer__title ct-insight-answer__title--${presentation.tone}`}
      >
        <Icon name={presentation.icon} size={16} aria-hidden="true" />
        {presentation.label}
      </h3>

      {(at || lifecycleLabel) && (
        <p className="v3-muted ct-insight-answer__meta">
          {at ? <span>{at}</span> : null}
          {at && lifecycleLabel ? <span aria-hidden="true"> · </span> : null}
          {lifecycleLabel ? <span>Interaction: {lifecycleLabel}</span> : null}
        </p>
      )}

      <p className="ct-insight-answer__summary">{presentation.summary}</p>
      {presentation.guidance && (
        <p className="ct-insight-answer__guidance">{presentation.guidance}</p>
      )}

      {narrationText ? (
        <div className="ct-insight-answer__narration">
          <h4 className="ct-insight-answer__narration-label">CarbonTally summary</h4>
          <p>{narrationText}</p>
        </div>
      ) : null}

      {narration && (
        <Alert tone={narration.tone} title={narration.title}>
          {narration.body}
        </Alert>
      )}

      {replay && (
        <Alert tone={replay.tone} title={replay.title}>
          {replay.body}
        </Alert>
      )}
    </section>
  );
}
