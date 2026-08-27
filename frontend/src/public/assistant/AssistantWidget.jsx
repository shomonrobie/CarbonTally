// AssistantWidget.jsx — Public CarbonTally Assistant (website candidate).
//
// Floating bottom-right chatbot. The response layer is the deterministic
// local knowledge module (assistantKnowledge.js) backed by the approved
// target-state FAQ — no AI provider, no API key, no network call.
//
// UX features:
//   - launcher (open/close), panel with header + messages + input
//   - suggested question chips (welcome, intents and fallbacks)
//   - source attribution per answer ("CarbonTally Customer FAQ")
//   - "See this answer in the FAQ" deep link to /faq#faq-<id>
//   - related-question chips, copy answer, feedback (helpful/not), retry
//   - unknown-question fallback with contact CTA
//   - keyboard: Enter to send, Escape to close, focus into input on open
//   - responsive: bottom sheet on small screens
//
// The production assistant architecture (CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md)
// describes how this widget connects to an Assistant Gateway with a model
// provider and authenticated tools in a later phase.

import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { handleQuery, SUGGESTED_QUESTIONS } from './assistantKnowledge';
import './assistant.css';

let UID = 0;
const nextId = () => `m${++UID}`;

function userMessage(text) {
  return { id: nextId(), role: 'user', text };
}

function assistantMessage(resp) {
  return {
    id: nextId(),
    role: 'assistant',
    text: resp.answer,
    source: resp.source,
    category: resp.category,
    faqId: resp.id,
    related: resp.related || [],
    suggestions: resp.suggestions || [],
  };
}

const WELCOME_MESSAGE = assistantMessage({
  answer:
    'Hi, I\u2019m the CarbonTally Assistant. I can help you understand CarbonTally and how the processing service works. Ask a question, or pick one below.',
  source: 'CarbonTally Assistant',
  suggestions: SUGGESTED_QUESTIONS.slice(0, 3),
});

export default function AssistantWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [feedback, setFeedback] = useState({});
  const [copiedId, setCopiedId] = useState(null);

  const launcherRef = useRef(null);
  const inputRef = useRef(null);
  const scrollRef = useRef(null);
  const lastUserRef = useRef(null);

  // Keep track of the most recent user question for retry.
  useEffect(() => {
    const last = [...messages].reverse().find((m) => m.role === 'user');
    lastUserRef.current = last ? last.text : null;
  }, [messages]);

  // Scroll new content into view.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, typing, open]);

  // Focus the input when the panel opens.
  useEffect(() => {
    if (open && inputRef.current) inputRef.current.focus();
  }, [open]);

  const produceAnswer = (text) => {
    setTyping(true);
    window.setTimeout(() => {
      const resp = handleQuery(text);
      setTyping(false);
      setMessages((prev) => [...prev, assistantMessage(resp)]);
    }, 650);
  };

  const submit = (text) => {
    const t = String(text || '').trim();
    if (!t || typing) return;
    setInput('');
    setMessages((prev) => [...prev, userMessage(t)]);
    produceAnswer(t);
  };

  const retry = () => {
    const q = lastUserRef.current;
    if (!q || typing) return;
    // Drop trailing assistant messages so the re-run answers the same question.
    const msgs = [...messages];
    let i = msgs.length - 1;
    while (i >= 0 && msgs[i].role === 'assistant') i -= 1;
    setMessages(i >= 0 ? msgs.slice(0, i + 1) : [WELCOME_MESSAGE]);
    produceAnswer(q);
  };

  const toggleFeedback = (msgId, value) => {
    setFeedback((prev) => ({ ...prev, [msgId]: prev[msgId] === value ? null : value }));
  };

  const copyAnswer = (msg) => {
    if (navigator.clipboard) navigator.clipboard.writeText(msg.text).catch(() => {});
    setCopiedId(msg.id);
    window.setTimeout(() => setCopiedId((c) => (c === msg.id ? null : c)), 1800);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setOpen(false);
      if (launcherRef.current) launcherRef.current.focus();
    }
  };

  const onFormSubmit = (e) => {
    e.preventDefault();
    submit(input);
  };

  const lastAssistantId = [...messages].reverse().find((m) => m.role === 'assistant')?.id;

  return (
    <>
      {/* Launcher */}
      <button
        ref={launcherRef}
        type="button"
        className={`ct-ast-launcher${open ? ' ct-ast-launcher-open' : ''}`}
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label={open ? 'Close CarbonTally Assistant' : 'Open CarbonTally Assistant'}
        aria-haspopup="dialog"
      >
        <span className="ct-ast-launcher-icon" aria-hidden="true">
          {open ? <CloseIcon /> : <ChatIcon />}
        </span>
        <span className="ct-ast-launcher-tip">CarbonTally Assistant</span>
      </button>

      {/* Panel */}
      {open && (
        <div
          className="ct-ast-panel"
          role="dialog"
          aria-label="CarbonTally Assistant"
          onKeyDown={handleKeyDown}
        >
          <div className="ct-ast-header">
            <div className="ct-ast-header-brand">
              <span className="ct-ast-header-logo" aria-hidden="true">🌱</span>
              <div className="ct-ast-header-text">
                <span className="ct-ast-header-title">CarbonTally Assistant</span>
                <span className="ct-ast-header-status">
                  <span className="ct-ast-dot" aria-hidden="true" /> Can answer questions about CarbonTally
                </span>
              </div>
            </div>
            <button
              type="button"
              className="ct-ast-close"
              onClick={() => setOpen(false)}
              aria-label="Close CarbonTally Assistant"
            >
              <CloseIcon />
            </button>
          </div>

          <div className="ct-ast-messages" ref={scrollRef} aria-live="polite">
            {messages.map((msg) =>
              msg.role === 'user' ? (
                <div key={msg.id} className="ct-ast-row ct-ast-row-user">
                  <div className="ct-ast-bubble ct-ast-bubble-user">{msg.text}</div>
                </div>
              ) : (
                <div key={msg.id} className="ct-ast-row ct-ast-row-assistant">
                  <div className="ct-ast-bubble ct-ast-bubble-assistant">
                    <p className="ct-ast-answer">{msg.text}</p>

                    {msg.related.length > 0 && (
                      <div className="ct-ast-chips">
                        <span className="ct-ast-chips-label">Related:</span>
                        {msg.related.map((rel) => (
                          <button key={rel.id} type="button" className="ct-ast-chip" onClick={() => submit(rel.q)}>
                            {rel.q}
                          </button>
                        ))}
                      </div>
                    )}

                    {msg.suggestions.length > 0 && (
                      <div className="ct-ast-chips">
                        {msg.suggestions.map((q) => (
                          <button key={q} type="button" className="ct-ast-chip" onClick={() => submit(q)}>
                            {q}
                          </button>
                        ))}
                      </div>
                    )}

                    {msg.faqId && (
                      <Link to={`/faq#faq-${msg.faqId}`} className="ct-ast-faq-link">
                        See this answer in the FAQ →
                      </Link>
                    )}

                    <div className="ct-ast-meta">
                      <span className="ct-ast-source">Source: {msg.source}</span>
                      <span className="ct-ast-actions">
                        <button
                          type="button"
                          className="ct-ast-act"
                          onClick={() => copyAnswer(msg)}
                          aria-label="Copy answer"
                          title="Copy answer"
                        >
                          {copiedId === msg.id ? 'Copied' : 'Copy'}
                        </button>
                        <button
                          type="button"
                          className={`ct-ast-act${feedback[msg.id] === 'up' ? ' ct-ast-act-on' : ''}`}
                          onClick={() => toggleFeedback(msg.id, 'up')}
                          aria-label="This answer was helpful"
                          aria-pressed={feedback[msg.id] === 'up'}
                          title="Helpful"
                        >
                          👍
                        </button>
                        <button
                          type="button"
                          className={`ct-ast-act${feedback[msg.id] === 'down' ? ' ct-ast-act-on' : ''}`}
                          onClick={() => toggleFeedback(msg.id, 'down')}
                          aria-label="This answer was not helpful"
                          aria-pressed={feedback[msg.id] === 'down'}
                          title="Not helpful"
                        >
                          👎
                        </button>
                        {msg.id === lastAssistantId && (
                          <button type="button" className="ct-ast-act" onClick={retry} title="Ask again" aria-label="Ask again">
                            ↻
                          </button>
                        )}
                      </span>
                    </div>
                    {feedback[msg.id] && (
                      <p className="ct-ast-feedback-note">Thanks for your feedback — it helps us improve.</p>
                    )}
                  </div>
                </div>
              )
            )}

            {typing && (
              <div className="ct-ast-row ct-ast-row-assistant">
                <div className="ct-ast-bubble ct-ast-bubble-assistant ct-ast-typing" aria-label="CarbonTally Assistant is typing">
                  <span className="ct-ast-typing-dot" />
                  <span className="ct-ast-typing-dot" />
                  <span className="ct-ast-typing-dot" />
                </div>
              </div>
            )}
          </div>

          <form className="ct-ast-input-row" onSubmit={onFormSubmit}>
            <label htmlFor="ct-ast-input" className="ct-ast-vh">
              Ask CarbonTally Assistant a question
            </label>
            <input
              id="ct-ast-input"
              ref={inputRef}
              type="text"
              autoComplete="off"
              placeholder="Ask CarbonTally..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button type="submit" className="ct-ast-send" disabled={!input.trim() || typing} aria-label="Send question">
              <SendIcon />
            </button>
          </form>
          <p className="ct-ast-disclaimer">
            The assistant provides general information about CarbonTally. It cannot see your data or account.
          </p>
        </div>
      )}
    </>
  );
}

function ChatIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
      <line x1="8" y1="10" x2="16" y2="10" />
      <line x1="8" y1="14" x2="13" y2="14" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}
