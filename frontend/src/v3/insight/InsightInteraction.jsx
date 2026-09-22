// frontend/src/v3/insight/InsightInteraction.jsx
// CarbonTally Insight I6 — one interaction in a conversation: its answer state,
// its deterministic tool evidence, and its provenance references.
//
// The persisted detail is read lazily through the creator-private I4 read
// endpoint, so history is only loaded when the user asks for it. When the
// interaction was just run in this session, the response the backend already
// returned is used instead of a duplicate read.
import React, { useEffect, useRef, useState } from 'react';
import Alert from '../components/ui/Alert';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { LoadingState } from '../components/ui/StateViews';
import { getInsightInteraction } from '../api';
import InsightAnswerState from './InsightAnswerState';
import InsightReferences from './InsightReferences';
import { formatTimestamp } from './format';
import './insight.css';

// The closed I3 ToolStatus vocabulary, presented for evidence only. Kept
// separate from the I4 answer vocabulary (PO Q3) — never merged.
const TOOL_STATUS_PRESENTATION = {
  success: { label: 'Succeeded', tone: 'success' },
  no_data: { label: 'No data', tone: 'muted' },
  not_authorized: { label: 'Not available', tone: 'muted' },
  invalid_input: { label: 'Invalid input', tone: 'warning' },
  provider_unavailable: { label: 'Provider unavailable', tone: 'warning' },
  error: { label: 'Failed', tone: 'error' },
};

function toolStatusPresentation(status) {
  return TOOL_STATUS_PRESENTATION[status] || { label: status || 'Unknown', tone: 'muted' };
}

/** The de-duplicated reference locators carried by a persisted interaction. */
export function referencesFromDetail(detail) {
  const seen = new Set();
  const references = [];
  ((detail && detail.tool_calls) || []).forEach((call) => {
    ((call && call.references) || []).forEach((reference) => {
      if (!reference || !reference.id) return;
      const key = `${reference.kind}:${reference.id}`;
      if (seen.has(key)) return;
      seen.add(key);
      references.push({ kind: reference.kind, id: reference.id });
    });
  });
  return references;
}

export default function InsightInteraction({ row, organizationId, outcome, autoOpen = false }) {
  // A row created together with a fresh outcome (the just-asked question) opens
  // immediately so its answer and evidence are visible without a second click.
  const [open, setOpen] = useState(autoOpen || Boolean(outcome));
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);

  // A pre-existing row that later receives an outcome opens exactly once; a row
  // the user has deliberately collapsed stays collapsed.
  const autoOpened = useRef(autoOpen || Boolean(outcome));
  useEffect(() => {
    if (outcome && !autoOpened.current) {
      autoOpened.current = true;
      setOpen(true);
    }
  }, [outcome]);

  const interactionId = row.interaction_id;
  const panelId = `insight-interaction-${interactionId}`;
  const headingId = `${panelId}-answer`;
  const refsHeadingId = `${panelId}-refs`;

  const answerStatus = row.answer_status;

  const loadDetail = async () => {
    setLoading(true);
    setFailed(false);
    try {
      const response = await getInsightInteraction(organizationId, interactionId);
      setDetail(response);
    } catch (_error) {
      // Non-disclosing: a 404 for a foreign interaction is an answer, not a leak.
      setFailed(true);
    } finally {
      setLoading(false);
    }
  };

  const onToggle = () => {
    const next = !open;
    setOpen(next);
    if (next && !detail && !outcome) loadDetail();
  };

  const toolCalls = (outcome && outcome.tool_calls && outcome.tool_calls.length)
    ? outcome.tool_calls
    : ((detail && detail.tool_calls) || []);
  const references = (outcome && outcome.references && outcome.references.length)
    ? outcome.references
    : referencesFromDetail(detail);
  const narrationState = row.narration_state || (outcome && outcome.narration_state);
  const narrationText = outcome ? outcome.narration_text : null;
  const at = formatTimestamp(row.created_at);

  return (
    <li className="ct-insight-interaction" data-testid="insight-interaction">
      <p className="ct-insight-interaction__meta">
        {at ? <span>{at}</span> : null}
        {row.intent ? <span className="ct-insight-interaction__intent">Topic: {row.intent}</span> : null}
        {typeof row.tool_call_count === 'number' ? (
          <span>{row.tool_call_count} data lookup{row.tool_call_count === 1 ? '' : 's'}</span>
        ) : null}
        {typeof row.reference_count === 'number' ? (
          <span>{row.reference_count} reference{row.reference_count === 1 ? '' : 's'}</span>
        ) : null}
      </p>

      {!open && (
        <Button
          size="sm"
          variant="ghost"
          icon="chevronDown"
          onClick={onToggle}
          aria-expanded={open}
          aria-controls={panelId}
        >
          View answer details
        </Button>
      )}
      {open && (
        <div id={panelId} className="ct-insight-interaction__panel">
          <InsightAnswerState
            answerStatus={answerStatus}
            narrationState={narrationState}
            narrationText={narrationText}
            lifecycle={row.lifecycle || (detail && detail.lifecycle)}
            replayed={outcome ? outcome.replayed : false}
            createdAt={row.created_at || (detail && detail.created_at)}
            headingId={headingId}
          />

          {loading && <LoadingState label="Loading evidence…" inline />}

          {failed && (
            <Alert tone="warning" title="Evidence not available">
              CarbonTally couldn&apos;t load the evidence for this interaction. No conclusion should
              be drawn about what it contains.
              <div className="ct-insight-interaction__actions">
                <Button size="sm" icon="refresh" onClick={loadDetail}>Try again</Button>
              </div>
            </Alert>
          )}

          {toolCalls.length > 0 && (
            <div className="ct-insight-interaction__tool-calls">
              <h4 className="ct-insight-interaction__subhead">CarbonTally data lookups</h4>
              <ul className="ct-insight-interaction__calls">
                {toolCalls.map((call, index) => {
                  const status = toolStatusPresentation(call.status);
                  return (
                    <li key={call.tool_call_id || `${call.tool}-${index}`} className="ct-insight-call">
                      <code className="ct-insight-call__tool">{call.tool}</code>
                      <Badge tone={status.tone}>{status.label}</Badge>
                      {call.reason ? <span className="v3-muted">{call.reason}</span> : null}
                      {typeof call.duration_ms === 'number' ? (
                        <span className="v3-muted">{call.duration_ms} ms</span>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          <InsightReferences
            references={references}
            organizationId={organizationId}
            headingId={refsHeadingId}
          />

          <Button
            size="sm"
            variant="ghost"
            icon="chevronUp"
            onClick={onToggle}
            aria-expanded={open}
            aria-controls={panelId}
          >
            Hide answer details
          </Button>
        </div>
      )}

    </li>
  );
}
