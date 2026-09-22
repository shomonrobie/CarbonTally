// frontend/src/v3/insight/InsightPage.jsx
// CarbonTally Insight I6 — the authenticated Insight workspace (PO I6-1/I6-2).
//
// Scope: the creator-private conversation list, the conversation view (message
// history + the answer state/evidence of each interaction) and the composer that
// starts or continues a conversation. Everything is read and written through the
// closed I1–I4 backend contracts; there is no shared conversation workspace and
// no client-side authorization. The UI is not a security boundary — the backend
// re-authorizes every read.
import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  createInsightConversation,
  listInsightConversations,
  listInsightInteractions,
  listInsightMessages,
  resolveV3Organization,
  runInsightInteraction,
} from '../api';
import Button from '../components/ui/Button';
import Icon from '../components/ui/Icon';
import { EmptyState, ErrorState, LoadingState } from '../components/ui/StateViews';
import { v4 as uuid } from '../components/ui/uuidFallback';
import InsightInteraction from './InsightInteraction';
import { conversationTitle, formatTimestamp } from './format';
import './insight.css';

const ASK_FAILED_MESSAGE =
  "CarbonTally couldn't complete that question. Nothing was concluded from it. Please try again.";

export default function InsightPage() {
  const [org, setOrg] = useState(null);
  const [contextLoading, setContextLoading] = useState(true);
  const [contextError, setContextError] = useState(false);

  const [conversations, setConversations] = useState([]);
  const [conversationsLoading, setConversationsLoading] = useState(true);
  const [conversationsError, setConversationsError] = useState(false);

  const [activeId, setActiveId] = useState(null);

  const [messages, setMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState(false);

  const [interactions, setInteractions] = useState([]);
  const [interactionsLoading, setInteractionsLoading] = useState(false);
  const [interactionsError, setInteractionsError] = useState(false);

  // The interaction response the backend already returned in this session, so a
  // fresh answer renders its narration/evidence without a duplicate read.
  const [outcomes, setOutcomes] = useState({});

  const [newTitle, setNewTitle] = useState('');
  const [starting, setStarting] = useState(false);

  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState('');
  const [focusInteractionId, setFocusInteractionId] = useState(null);

  const [reloadKey, setReloadKey] = useState(0);
  const [contextKey, setContextKey] = useState(0);
  const questionRef = useRef(null);

  // ---- Actor context (server-authoritative) -------------------------------
  useEffect(() => {
    let active = true;
    // Only the first resolution (or an explicit retry after a failure) shows the
    // full-page state: a refresh of the conversation data must never blank a
    // workspace the user is already working in.
    if (!org) setContextLoading(true);
    resolveV3Organization()
      .then((organization) => {
        if (!active) return;
        // A null resolution is "no organisation available for this account";
        // a thrown failure is a separate, retryable error state.
        setOrg(organization && organization.id ? organization : null);
      })
      .catch(() => { if (active) setContextError(true); })
      .finally(() => { if (active) setContextLoading(false); });
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contextKey]);

  // ---- Creator-private conversation list ----------------------------------
  useEffect(() => {
    if (!org) return undefined;
    let active = true;
    setConversationsLoading(true);
    setConversationsError(false);
    listInsightConversations(org.id)
      .then((response) => {
        if (!active) return;
        setConversations((response && response.conversations) || []);
      })
      .catch(() => { if (active) setConversationsError(true); })
      .finally(() => { if (active) setConversationsLoading(false); });
    return () => { active = false; };
  }, [org, reloadKey]);

  // ---- Conversation view (messages + interactions) ------------------------
  useEffect(() => {
    if (!org || !activeId) return undefined;
    let active = true;

    setMessagesLoading(true);
    setMessagesError(false);
    listInsightMessages(org.id, activeId)
      .then((response) => {
        if (!active) return;
        setMessages((response && response.messages) || []);
      })
      .catch(() => { if (active) setMessagesError(true); })
      .finally(() => { if (active) setMessagesLoading(false); });

    setInteractionsLoading(true);
    setInteractionsError(false);
    listInsightInteractions(org.id, { conversationId: activeId })
      .then((response) => {
        if (!active) return;
        setInteractions((response && response.interactions) || []);
      })
      .catch(() => { if (active) setInteractionsError(true); })
      .finally(() => { if (active) setInteractionsLoading(false); });

    return () => { active = false; };
  }, [org, activeId, reloadKey]);
  // ---- Focus management: the newest answer is focused after a question ----
  useEffect(() => {
    if (!focusInteractionId) return;
    const heading = document.getElementById(`insight-interaction-${focusInteractionId}-answer`);
    // The row may not be committed yet (a fresh answer arrives with its outcome);
    // wait for it rather than dropping the focus move.
    if (!heading) return;
    heading.setAttribute('tabindex', '-1');
    heading.focus();
    setFocusInteractionId(null);
  }, [focusInteractionId, interactions, outcomes]);

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeId) || null,
    [conversations, activeId],
  );

  const onStartConversation = async (event) => {
    event.preventDefault();
    if (!org || starting) return;
    setStarting(true);
    setAskError('');
    try {
      const created = await createInsightConversation(org.id, newTitle.trim());
      setNewTitle('');
      setOutcomes({});
      setReloadKey((n) => n + 1);
      if (created && created.id) {
        setActiveId(created.id);
      }
    } catch (_error) {
      setAskError("CarbonTally couldn't start a new conversation. Please try again.");
    } finally {
      setStarting(false);
    }
  };

  const onSelectConversation = (conversationId) => {
    setAskError('');
    setOutcomes({});
    setActiveId(conversationId);
  };

  const onAsk = async (event) => {
    event.preventDefault();
    const text = question.trim();
    if (!org || !activeId || !text || asking) return;
    setAsking(true);
    setAskError('');
    try {
      const outcome = await runInsightInteraction({
        organizationId: org.id,
        conversationId: activeId,
        question: text,
        // A plain client request key so a retried submit cannot record a second
        // interaction. The backend owns the replay decision (`replayed`) and the
        // key itself is never displayed.
        idempotencyKey: uuid(),
        narration: 'optional',
      });
      setQuestion('');
      if (outcome && outcome.interaction_id) {
        setOutcomes((previous) => ({ ...previous, [outcome.interaction_id]: outcome }));
        setFocusInteractionId(outcome.interaction_id);
      }
      setReloadKey((n) => n + 1);
    } catch (_error) {
      // Covers 403/404/422/5xx and network failure with one non-disclosing
      // message: nothing about whether a resource exists is revealed.
      setAskError(ASK_FAILED_MESSAGE);
    } finally {
      setAsking(false);
    }
  };
  // ---- Render -------------------------------------------------------------

  if (contextLoading) {
    return (
      <div className="v3-page ct-insight" data-testid="insight-page">
        <LoadingState label="Loading CarbonTally Insight…" />
      </div>
    );
  }

  if (contextError) {
    return (
      <div className="v3-page ct-insight" data-testid="insight-page">
        <div className="v3-page-header">
          <h1>Insight</h1>
          <p className="v3-subtitle">
            Ask about your organisation&apos;s emissions data and see how each answer was produced.
          </p>
        </div>
        <ErrorState
          title="Insight isn't available just now"
          message="CarbonTally couldn't confirm your organisation for this session. Please try again."
          onRetry={() => { setContextError(false); setContextKey((n) => n + 1); }}
        />
      </div>
    );
  }

  if (!org) {
    return (
      <div className="v3-page ct-insight" data-testid="insight-page">
        <div className="v3-page-header">
          <h1>Insight</h1>
          <p className="v3-subtitle">
            Ask about your organisation&apos;s emissions data and see how each answer was produced.
          </p>
        </div>
        <div data-testid="insight-no-org">
          <EmptyState icon="briefcase" title="No organisation is linked to this account">
            CarbonTally Insight answers from the emissions data of the organisation your account
            belongs to. Once an organisation is linked, your questions and their evidence will appear
            here.
          </EmptyState>
        </div>
      </div>
    );
  }

  const knownInteractionIds = new Set(interactions.map((row) => row.interaction_id));
  const pendingOutcomeRows = Object.values(outcomes)
    .filter((outcome) => outcome && !knownInteractionIds.has(outcome.interaction_id))
    .map((outcome) => ({
      interaction_id: outcome.interaction_id,
      conversation_id: outcome.conversation_id,
      lifecycle: outcome.lifecycle,
      answer_status: outcome.answer_status,
      narration_state: outcome.narration_state,
      intent: outcome.intent,
      tool_call_count: (outcome.tool_calls || []).length,
      reference_count: (outcome.references || []).length,
      created_at: null,
    }));
  const interactionRows = [...pendingOutcomeRows, ...interactions];

  return (
    <div className="v3-page ct-insight" data-testid="insight-page">
      <div className="v3-page-header">
        <h1>Insight</h1>
        <p className="v3-subtitle">
          {`Ask about ${org.name}'s emissions data. Every answer shows the CarbonTally records behind it. Your conversations are private to you.`}
        </p>
      </div>

      {askError && (
        <div className="v3-error" role="alert" data-testid="insight-error">{askError}</div>
      )}

      <div className="ct-insight-layout">
        <aside className="ct-insight-sidebar" aria-label="Your Insight conversations">
          <form className="ct-insight-new" onSubmit={onStartConversation} data-testid="insight-new-conversation">
            <label className="ct-insight-new__label" htmlFor="insight-new-topic">
              Start a new conversation
            </label>
            <div className="ct-insight-new__row">
              <input
                id="insight-new-topic"
                className="v3-input"
                type="text"
                value={newTitle}
                onChange={(event) => setNewTitle(event.target.value)}
                maxLength={200}
                placeholder="Topic (optional)"
              />
              <Button type="submit" variant="primary" size="sm" loading={starting}>
                New
              </Button>
            </div>
          </form>

          <h2 className="ct-insight-sidebar__title">Conversations</h2>

          {conversationsLoading && conversations.length === 0 && (
            <LoadingState label="Loading conversations…" inline />
          )}

          {conversationsError && !conversationsLoading && (
            <ErrorState
              inline
              title="Conversations unavailable"
              message="CarbonTally couldn't load your conversations."
              onRetry={() => setReloadKey((n) => n + 1)}
            />
          )}

          {!conversationsLoading && !conversationsError && conversations.length === 0 && (
            <div data-testid="insight-conversations-empty">
              <EmptyState icon="help" title="No conversations yet">
                Start one with the box above, then ask a question about your organisation&apos;s
                emissions data.
              </EmptyState>
            </div>
          )}

          {!conversationsError && conversations.length > 0 && (
            <ul className="ct-insight-conversations" data-testid="insight-conversation-list">
              {conversations.map((conversation) => {
                const isActive = conversation.id === activeId;
                const at = formatTimestamp(conversation.updated_at || conversation.created_at);
                return (
                  <li key={conversation.id}>
                    <button
                      type="button"
                      className={`ct-insight-conversation${isActive ? ' ct-insight-conversation--active' : ''}`}
                      onClick={() => onSelectConversation(conversation.id)}
                      aria-current={isActive ? 'true' : undefined}
                    >
                      <span className="ct-insight-conversation__title">{conversationTitle(conversation)}</span>
                      {at ? <span className="ct-insight-conversation__meta">{at}</span> : null}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </aside>
        <section className="ct-insight-main" aria-label="Conversation">
          {!activeId && (
            <div data-testid="insight-no-conversation-selected">
              <EmptyState icon="messaging" title="Nothing selected">
                Select one of your conversations on the left, or start a new one.
              </EmptyState>
            </div>
          )}

          {activeId && (
            <>
              <header className="ct-insight-main__header">
                <h2 className="ct-insight-main__title">
                  {conversationTitle(activeConversation || { id: activeId })}
                </h2>
                <p className="v3-muted">
                  This conversation is private to you. CarbonTally never shows it to another user.
                </p>
              </header>

              <form className="ct-insight-ask" onSubmit={onAsk} data-testid="insight-ask-form">
                <label className="ct-insight-ask__label" htmlFor="insight-question">
                  Ask a question about your emissions data
                </label>
                <textarea
                  id="insight-question"
                  ref={questionRef}
                  className="v3-input ct-insight-ask__input"
                  rows={3}
                  maxLength={2000}
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  disabled={asking}
                  placeholder="For example: what did report version 2 show for 2025?"
                />
                <div className="ct-insight-ask__row">
                  <span className="v3-muted">{`${question.length}/2000`}</span>
                  <Button
                    type="submit"
                    variant="primary"
                    icon="send"
                    loading={asking}
                    disabled={asking || !question.trim()}
                  >
                    {asking ? 'Asking…' : 'Ask'}
                  </Button>
                </div>
              </form>

              <section className="ct-insight-history" aria-labelledby="insight-history-heading">
                <h3 id="insight-history-heading" className="ct-insight-section__title">
                  <Icon name="messaging" size={15} aria-hidden="true" />
                  Conversation history
                </h3>
                {messagesLoading && messages.length === 0 && (
                  <LoadingState label="Loading history…" inline />
                )}
                {messagesError && !messagesLoading && (
                  <ErrorState
                    inline
                    title="History unavailable"
                    message="CarbonTally couldn't load this conversation's history."
                    onRetry={() => setReloadKey((n) => n + 1)}
                  />
                )}
                {!messagesLoading && !messagesError && messages.length === 0 && (
                  <div data-testid="insight-history-empty">
                    <EmptyState icon="messaging" title="No history yet">
                      Ask the first question in this conversation and it will appear here.
                    </EmptyState>
                  </div>
                )}
                {!messagesError && messages.length > 0 && (
                  <ol className="ct-insight-thread" data-testid="insight-thread">
                    {messages.map((message) => {
                      const at = formatTimestamp(message.created_at);
                      const speaker = message.role === 'user'
                        ? 'You asked'
                        : message.role === 'insight'
                          ? 'CarbonTally'
                          : message.role;
                      return (
                        <li
                          key={message.id}
                          className={`ct-insight-message ct-insight-message--${message.role === 'insight' ? 'insight' : 'user'}`}
                        >
                          <p className="ct-insight-message__speaker">
                            {speaker}
                            {at ? <span className="v3-muted"> · {at}</span> : null}
                          </p>
                          <p className="ct-insight-message__body">{message.content}</p>
                        </li>
                      );
                    })}
                  </ol>
                )}
              </section>
              <section className="ct-insight-answers" aria-labelledby="insight-answers-heading">
                <h3 id="insight-answers-heading" className="ct-insight-section__title">
                  <Icon name="activity" size={15} aria-hidden="true" />
                  Answers and evidence
                </h3>

                {interactionsLoading && interactionRows.length === 0 && (
                  <LoadingState label="Loading answers…" inline />
                )}

                {interactionsError && !interactionsLoading && (
                  <ErrorState
                    inline
                    title="Answers unavailable"
                    message="CarbonTally couldn't load the answers recorded in this conversation."
                    onRetry={() => setReloadKey((n) => n + 1)}
                  />
                )}

                {!interactionsLoading && !interactionsError && interactionRows.length === 0 && (
                  <div data-testid="insight-answers-empty">
                    <EmptyState icon="help" title="No answers recorded yet">
                      Each question CarbonTally answers appears here with its answer state and the
                      references behind it.
                    </EmptyState>
                  </div>
                )}

                {interactionRows.length > 0 && (
                  <ul className="ct-insight-interactions" data-testid="insight-interactions">
                    {interactionRows.map((row) => (
                      <InsightInteraction
                        key={row.interaction_id}
                        row={row}
                        organizationId={org.id}
                        outcome={outcomes[row.interaction_id]}
                      />
                    ))}
                  </ul>
                )}
              </section>

            </>
          )}
        </section>
      </div>
    </div>
  );
}


