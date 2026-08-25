// frontend/src/v3/components/StateViews.jsx
// D29/F3 — shared LOADING / ERROR / EMPTY state components so every V3 page
// presents a consistent, retryable surface instead of ad-hoc implementations.
import React from 'react';

export function LoadingState({ label = 'Loading…' }) {
  return (
    <div className="v3-loading">
      <div className="spinner" />
      {label}
    </div>
  );
}

export function ErrorState({ message, onRetry, title = 'Something went wrong', inline }) {
  const content = (
    <>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{title}</div>
      <div>{message || 'Please try again.'}</div>
      {onRetry && (
        <button
          type="button"
          className="v3-btn v3-btn-sm"
          style={{ marginTop: 10 }}
          onClick={onRetry}
        >
          Retry
        </button>
      )}
    </>
  );
  if (inline) {
    return <div className="v3-error" role="alert">{content}</div>;
  }
  return (
    <div className="v3-page">
      <div className="v3-error" role="alert">{content}</div>
    </div>
  );
}

export function EmptyState({ children }) {
  return <div className="v3-empty">{children}</div>;
}
